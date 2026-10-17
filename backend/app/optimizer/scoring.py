from __future__ import annotations

import heapq
import math

from app.schemas.network import Network
from app.schemas.plan import Plan
from app.schemas.scenario import PassengerDemand, Scenario


DEFAULT_OBJECTIVE_WEIGHTS = {
    "operating_cost": 1.0,
    "vehicle_km": 1.0,
    "deadhead_km": 1.0,
    "vehicle_changes": 500.0,
    "unassigned_services": 100_000.0,
    "passenger_wait": 1.0,
    "unserved_passengers": 100.0,
    "constraint_violations": 250_000.0,
}

_WEIGHT_ALIASES = {
    "cost": "operating_cost",
    "distance": "vehicle_km",
    "deadhead_distance": "deadhead_km",
    "deadhead_distance_km": "deadhead_km",
    "repositioning_distance": "deadhead_km",
    "unnecessary_vehicle_changes": "vehicle_changes",
    "unassigned_services": "unassigned_services",
    "wait": "passenger_wait",
    "passenger_wait_min": "passenger_wait",
    "unserved": "unserved_passengers",
    "constraints": "constraint_violations",
}


def normalize_objective_weights(weights: dict[str, float] | None = None) -> dict[str, float]:
    normalized = dict(DEFAULT_OBJECTIVE_WEIGHTS)
    for raw_key, raw_value in (weights or {}).items():
        key = _WEIGHT_ALIASES.get(raw_key, raw_key)
        if key not in normalized:
            raise ValueError(f"unsupported objective weight: {raw_key}")
        value = float(raw_value)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"objective weight '{raw_key}' must be a finite non-negative number")
        normalized[key] = value
    return normalized


def road_distance_matrix(network: Network) -> dict[tuple[str, str], float]:
    adjacency: dict[str, list[tuple[str, float]]] = {}
    for route in network.routes:
        for index, (origin, destination) in enumerate(zip(route.stop_ids, route.stop_ids[1:])):
            if index >= len(route.segment_distance_km):
                continue
            distance = float(route.segment_distance_km[index])
            adjacency.setdefault(origin, []).append((destination, distance))
            adjacency.setdefault(destination, []).append((origin, distance))

    matrix: dict[tuple[str, str], float] = {}
    for source in adjacency:
        distances = {source: 0.0}
        pending = [(0.0, source)]
        while pending:
            distance, current = heapq.heappop(pending)
            if distance != distances.get(current):
                continue
            for neighbor, edge_distance in adjacency.get(current, []):
                candidate = distance + edge_distance
                if candidate < distances.get(neighbor, math.inf):
                    distances[neighbor] = candidate
                    heapq.heappush(pending, (candidate, neighbor))
        matrix.update({(source, destination): distance for destination, distance in distances.items()})
    return matrix


def plan_deadhead_distance_km(network: Network, plan: Plan) -> float:
    routes = network.routes_by_id
    vehicles = network.vehicles_by_id
    distances = road_distance_matrix(network)
    assignments = sorted(
        [*plan.assignments, *plan.extra_trips],
        key=lambda assignment: (assignment.departure_min, assignment.trip_id),
    )
    current_stop = {vehicle_id: vehicle.initial_stop_id for vehicle_id, vehicle in vehicles.items()}
    total = 0.0
    for assignment in assignments:
        route = routes.get(assignment.route_id)
        vehicle = vehicles.get(assignment.vehicle_id)
        if route is None or vehicle is None or not route.stop_ids:
            continue
        origin = current_stop.get(vehicle.vehicle_id, vehicle.initial_stop_id)
        reposition = distances.get((origin, route.stop_ids[0]))
        if reposition is not None:
            total += reposition
        current_stop[vehicle.vehicle_id] = route.stop_ids[-1]
    return total


def plan_deadhead_cost(network: Network, plan: Plan) -> float:
    routes = network.routes_by_id
    vehicles = network.vehicles_by_id
    distances = road_distance_matrix(network)
    assignments = sorted(
        [*plan.assignments, *plan.extra_trips],
        key=lambda assignment: (assignment.departure_min, assignment.trip_id),
    )
    current_stop = {vehicle_id: vehicle.initial_stop_id for vehicle_id, vehicle in vehicles.items()}
    total = 0.0
    for assignment in assignments:
        route = routes.get(assignment.route_id)
        vehicle = vehicles.get(assignment.vehicle_id)
        if route is None or vehicle is None or not route.stop_ids:
            continue
        origin = current_stop.get(vehicle.vehicle_id, vehicle.initial_stop_id)
        reposition = distances.get((origin, route.stop_ids[0]))
        if reposition is not None:
            total += reposition * vehicle.cost_per_km
        current_stop[vehicle.vehicle_id] = route.stop_ids[-1]
    return total


def score_plan(
    network: Network,
    scenario: Scenario,
    plan: Plan,
    demand: list[PassengerDemand] | None,
    weights: dict[str, float],
) -> tuple[float, dict]:
    from app.simulation.engine import simulate
    from app.validation.constraints import validate_plan

    validation = validate_plan(network, plan, scenario, demand=demand)
    result = simulate(network, plan, scenario, demand=demand)
    metrics = result.metrics
    assigned_ids = {assignment.trip_id for assignment in plan.assignments}
    expected_ids = {trip.trip_id for trip in network.trips}
    unassigned_count = len(expected_ids - assigned_ids)
    unassigned_count = max(unassigned_count, len(plan.unassigned_trip_ids))
    canonical = {trip.trip_id: trip for trip in network.trips}
    vehicle_changes = sum(
        1
        for assignment in plan.assignments
        if assignment.trip_id in canonical
        and assignment.vehicle_id != canonical[assignment.trip_id].vehicle_id
    )

    deadhead_km = plan_deadhead_distance_km(network, plan)
    deadhead_cost = plan_deadhead_cost(network, plan)

    passenger_wait = metrics.avg_wait_min * metrics.served_passengers
    score = (
        weights["operating_cost"] * (metrics.operating_cost + deadhead_cost)
        + weights["vehicle_km"] * (metrics.vehicle_km + deadhead_km)
        + weights["deadhead_km"] * deadhead_km
        + weights["vehicle_changes"] * vehicle_changes
        + weights["unassigned_services"] * unassigned_count
        + weights["passenger_wait"] * passenger_wait
        + weights["unserved_passengers"] * metrics.unserved_passengers
        + weights["constraint_violations"] * validation["hard_violation_count"]
        + weights["constraint_violations"] * len(validation["unverified_constraints"])
    )
    return score, {
        "validation": validation,
        "metrics": metrics.model_dump(),
        "deadhead_distance_km": deadhead_km,
        "vehicle_changes": vehicle_changes,
        "unassigned_services": unassigned_count,
    }
