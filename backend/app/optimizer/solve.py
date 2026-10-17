from __future__ import annotations

from collections import Counter
from typing import Optional

from app.prediction.predictor import PredictionOutput
from app.optimizer.fallback import fallback_plan
from app.optimizer.scoring import normalize_objective_weights, road_distance_matrix, score_plan
from app.schemas.network import Network, Route, Trip, Vehicle
from app.schemas.plan import Plan, TripAssignment
from app.schemas.scenario import PassengerDemand, Scenario


def route_duration_min(route: Route) -> float:
    return sum(route.segment_travel_min)


def _duration_min(route: Route, scenario: Scenario) -> float:
    """Trip duration exactly as the validator computes it."""
    return route_duration_min(route) * scenario.travel_time_multipliers.get(
        route.route_id, 1.0
    )


def _fits_availability(v: Vehicle, dep: float, end: float) -> bool:
    return dep >= v.available_from_min and end <= v.available_until_min


def _overlaps(busy: dict[str, list[tuple[float, float]]], vid: str, start: float, end: float) -> bool:
    return any(start < e and s < end for s, e in busy.get(vid, []))


def _can_assign(vid: str, dep: float, end: float, vehicles: dict[str, Vehicle],
                busy: dict[str, list[tuple[float, float]]]) -> bool:
    v = vehicles[vid]
    return _fits_availability(v, dep, end) and not _overlaps(busy, vid, dep, end)


def _mark_busy(busy: dict[str, list[tuple[float, float]]], vid: str,
               start: float, end: float, turnaround: int) -> None:
    busy.setdefault(vid, []).append((start, end + turnaround))


def _headway_ok(route: Route, existing: list[float], dep: float) -> bool:
    """Would inserting ``dep`` keep every route gap inside ``[min, max]``?"""
    for other in existing:
        gap = abs(dep - other)
        if gap < route.min_headway_min or gap > route.max_headway_min:
            return False
    return True


def _depot_vehicles(network: Network) -> dict[str, set[str]]:
    """Vehicle ids whose ``initial_stop_id`` equals their route's start stop."""
    vehicles = network.vehicles_by_id
    return {
        route.route_id: {
            v.vehicle_id for v in vehicles.values()
            if v.initial_stop_id == route.stop_ids[0]
        }
        for route in network.routes
    }


def _peak_trip_loads(
    network: Network,
    departures: dict[str, float],
    demand: Optional[list[PassengerDemand]],
    scenario: Scenario,
    extra_trips: Optional[list[TripAssignment]] = None,
) -> dict[str, int]:
    if not demand:
        return {}

    routes = network.routes_by_id
    trip_specs = [
        (trip.trip_id, trip.route_id, departures[trip.trip_id])
        for trip in network.trips
    ]
    trip_specs.extend(
        (trip.trip_id, trip.route_id, trip.departure_min)
        for trip in (extra_trips or [])
    )
    segment_loads = {
        trip_id: [0] * max(0, len(routes[route_id].stop_ids) - 1)
        for trip_id, route_id, _departure in trip_specs
    }
    for group in demand:
        choice: tuple[tuple[float, str], str, int, int] | None = None
        for trip_id, route_id, departure in trip_specs:
            route = routes[route_id]
            stops = route.stop_ids
            if group.origin_stop_id not in stops or group.destination_stop_id not in stops:
                continue
            origin = stops.index(group.origin_stop_id)
            destination = stops.index(group.destination_stop_id)
            if origin >= destination:
                continue

            multiplier = scenario.travel_time_multipliers.get(route_id, 1.0)
            offset = 0
            for segment_time in route.segment_travel_min[:origin]:
                duration = int(round(segment_time * multiplier))
                if segment_time > 0 and duration < 1:
                    duration = 1
                offset += duration
            board_time = departure + offset
            if board_time < group.arrival_time_min:
                continue
            if board_time > group.arrival_time_min + group.max_wait_min:
                continue
            key = (board_time, trip_id)
            if choice is None or key < choice[0]:
                choice = (key, trip_id, origin, destination)
        if choice is None:
            continue
        _key, trip_id, origin, destination = choice
        passenger_count = int(round(
            group.passenger_count
            * scenario.demand_multipliers.get(group.origin_stop_id, 1.0)
        ))
        for segment in range(origin, destination):
            segment_loads[trip_id][segment] += passenger_count
    return {
        trip_id: max(loads, default=0)
        for trip_id, loads in segment_loads.items()
    }


def _demand_extra_trips(
    network: Network,
    scenario: Scenario,
    base_assignments: list[TripAssignment],
    demand: Optional[list[PassengerDemand]],
) -> list[TripAssignment]:
    if not demand or not base_assignments:
        return []

    start_min = min(assignment.departure_min for assignment in base_assignments)
    horizon_end = start_min + scenario.evaluation_horizon_min
    extras: list[TripAssignment] = []
    existing_ids = {trip.trip_id for trip in network.trips}

    for route in network.routes:
        route_assignments = sorted(
            (assignment for assignment in base_assignments if assignment.route_id == route.route_id),
            key=lambda assignment: assignment.departure_min,
        )
        if len(route_assignments) < 2:
            continue

        scheduled_departures = [assignment.departure_min for assignment in route_assignments]
        route_stops = {stop_id: index for index, stop_id in enumerate(route.stop_ids)}
        multiplier = scenario.travel_time_multipliers.get(route.route_id, 1.0)

        def offset_to_stop(stop_index: int) -> int:
            total = 0
            for segment_time in route.segment_travel_min[:stop_index]:
                duration = int(round(segment_time * multiplier))
                if segment_time > 0 and duration < 1:
                    duration = 1
                total += duration
            return total

        route_demand = sorted(
            (
                group for group in demand
                if group.origin_stop_id in route_stops
                and group.destination_stop_id in route_stops
                and route_stops[group.origin_stop_id] < route_stops[group.destination_stop_id]
                and group.arrival_time_min <= horizon_end
                and round(group.passenger_count * scenario.demand_multipliers.get(group.origin_stop_id, 1.0)) > 0
            ),
            key=lambda group: (group.arrival_time_min, group.demand_id),
        )

        for group in route_demand:
            origin_index = route_stops[group.origin_stop_id]
            stop_offset = offset_to_stop(origin_index)

            def serves(departure: int) -> bool:
                board_time = departure + stop_offset
                return group.arrival_time_min <= board_time <= group.arrival_time_min + group.max_wait_min

            if any(serves(departure) for departure in scheduled_departures):
                continue

            earliest = max(start_min, group.arrival_time_min - stop_offset)
            latest = min(horizon_end, group.arrival_time_min + group.max_wait_min - stop_offset)
            options = [
                departure
                for departure in range(earliest, latest + 1)
                if serves(departure)
                and all(abs(departure - scheduled) >= route.min_headway_min for scheduled in scheduled_departures)
            ]
            if not options:
                continue

            departure = min(options, key=lambda value: (value + stop_offset - group.arrival_time_min, value))
            trip_id = f"OPT_{route.route_id}_{departure}"
            if trip_id in existing_ids:
                continue
            extras.append(TripAssignment(
                trip_id=trip_id,
                route_id=route.route_id,
                vehicle_id="",
                departure_min=departure,
            ))
            existing_ids.add(trip_id)
            scheduled_departures.append(departure)

    return extras


def _capacity_extra_trips(
    network: Network,
    scenario: Scenario,
    assignments: list[TripAssignment],
    demand: Optional[list[PassengerDemand]],
) -> list[TripAssignment]:
    if not demand or not assignments:
        return []

    from app.validation.constraints import CAPACITY_EXCEEDED, validate_plan

    report = validate_plan(
        network,
        Plan(plan_type="capacity_review", assignments=assignments),
        scenario,
        demand=demand,
    )
    assignment_by_trip = {assignment.trip_id: assignment for assignment in assignments}
    routes = network.routes_by_id
    scheduled_by_route: dict[str, list[int]] = {}
    for assignment in assignments:
        scheduled_by_route.setdefault(assignment.route_id, []).append(assignment.departure_min)

    existing_ids = {trip.trip_id for trip in network.trips}
    extras: list[TripAssignment] = []
    for issue in report["violations"]:
        if issue.get("code") != CAPACITY_EXCEEDED:
            continue
        overloaded_trip = assignment_by_trip.get(issue.get("trip_id"))
        if overloaded_trip is None:
            continue
        route = routes.get(overloaded_trip.route_id)
        segment_index = issue.get("segment_index")
        if route is None or not isinstance(segment_index, int) or segment_index >= len(route.stop_ids) - 1:
            continue

        origin_stop_id = route.stop_ids[segment_index]
        downstream = {stop_id: index for index, stop_id in enumerate(route.stop_ids[segment_index + 1 :], start=segment_index + 1)}
        multiplier = scenario.travel_time_multipliers.get(route.route_id, 1.0)
        offset = 0
        for segment_time in route.segment_travel_min[:segment_index]:
            duration = int(round(segment_time * multiplier))
            if segment_time > 0 and duration < 1:
                duration = 1
            offset += duration

        base_board_time = overloaded_trip.departure_min + offset
        impacted_groups = [
            group for group in demand
            if group.origin_stop_id == origin_stop_id
            and group.destination_stop_id in downstream
            and group.arrival_time_min <= base_board_time <= group.arrival_time_min + group.max_wait_min
            and round(group.passenger_count * scenario.demand_multipliers.get(group.origin_stop_id, 1.0)) > 0
        ]
        if not impacted_groups:
            continue

        route_departures = scheduled_by_route.setdefault(route.route_id, [])
        departure_choice: int | None = None
        for group in sorted(impacted_groups, key=lambda item: (item.arrival_time_min, item.demand_id)):
            earliest = overloaded_trip.departure_min + route.min_headway_min
            latest = min(
                overloaded_trip.departure_min + scenario.evaluation_horizon_min,
                group.arrival_time_min + group.max_wait_min - offset,
            )
            for departure in range(earliest, latest + 1):
                board_time = departure + offset
                if not (group.arrival_time_min <= board_time <= group.arrival_time_min + group.max_wait_min):
                    continue
                if any(abs(departure - existing) < route.min_headway_min for existing in route_departures):
                    continue
                departure_choice = departure
                break
            if departure_choice is not None:
                break

        if departure_choice is None:
            continue
        trip_id = f"OPT_{route.route_id}_{departure_choice}"
        if trip_id in existing_ids:
            continue
        extras.append(TripAssignment(
            trip_id=trip_id,
            route_id=route.route_id,
            vehicle_id="",
            departure_min=departure_choice,
        ))
        existing_ids.add(trip_id)
        route_departures.append(departure_choice)

    return extras


def _assign_with_extras(
    network: Network,
    scenario: Scenario,
    base_assignments: list[TripAssignment],
    proposed_extras: list[TripAssignment],
    demand: Optional[list[PassengerDemand]],
    weights: dict[str, float],
) -> tuple[list[TripAssignment], list[TripAssignment]]:
    if not proposed_extras:
        return base_assignments, []

    routes = network.routes_by_id
    vehicles = network.vehicles_by_id
    unavailable = set(scenario.unavailable_vehicle_ids)
    road_distances = road_distance_matrix(network)
    assigned_by_vehicle: dict[str, list[TripAssignment]] = {vehicle_id: [] for vehicle_id in vehicles}
    departures_by_route: dict[str, list[float]] = {}
    for assignment in base_assignments:
        route = routes.get(assignment.route_id)
        vehicle = vehicles.get(assignment.vehicle_id)
        if route is None or vehicle is None:
            continue
        assigned_by_vehicle[vehicle.vehicle_id].append(assignment)
        departures_by_route.setdefault(route.route_id, []).append(float(assignment.departure_min))

    output_extras: list[TripAssignment] = []
    for assignment in sorted(proposed_extras, key=lambda item: (item.departure_min, item.trip_id)):
        route = routes.get(assignment.route_id)
        if route is None or not route.stop_ids:
            continue
        departure = float(assignment.departure_min)
        end = departure + _duration_min(route, scenario)
        route_departures = departures_by_route.setdefault(route.route_id, [])
        if any(abs(departure - existing) < route.min_headway_min for existing in route_departures):
            continue
        estimated_load = 0
        if demand:
            stop_indexes = {stop_id: index for index, stop_id in enumerate(route.stop_ids)}
            multiplier = scenario.travel_time_multipliers.get(route.route_id, 1.0)
            segment_loads = [0] * max(0, len(route.stop_ids) - 1)
            for group in demand:
                origin = stop_indexes.get(group.origin_stop_id)
                destination = stop_indexes.get(group.destination_stop_id)
                if origin is None or destination is None or origin >= destination:
                    continue
                offset = 0
                for segment_time in route.segment_travel_min[:origin]:
                    duration = int(round(segment_time * multiplier))
                    if segment_time > 0 and duration < 1:
                        duration = 1
                    offset += duration
                board_time = assignment.departure_min + offset
                if not (group.arrival_time_min <= board_time <= group.arrival_time_min + group.max_wait_min):
                    continue
                passenger_count = int(round(
                    group.passenger_count
                    * scenario.demand_multipliers.get(group.origin_stop_id, 1.0)
                ))
                for segment in range(origin, destination):
                    segment_loads[segment] += passenger_count
            estimated_load = max(segment_loads, default=0)

        candidates: list[tuple[float, str]] = []
        for vehicle_id, vehicle in vehicles.items():
            if vehicle_id in unavailable or vehicle.vehicle_type not in route.allowed_vehicle_types:
                continue
            if departure < vehicle.available_from_min or end > vehicle.available_until_min:
                continue
            prior_assignments = [
                item for item in assigned_by_vehicle[vehicle_id]
                if item.departure_min < assignment.departure_min
            ]
            if not prior_assignments and vehicle.initial_stop_id != route.stop_ids[0]:
                continue

            conflicts = False
            for other in assigned_by_vehicle[vehicle_id]:
                other_route = routes.get(other.route_id)
                if other_route is None:
                    continue
                other_start = float(other.departure_min)
                other_end = other_start + _duration_min(other_route, scenario)
                if departure >= other_start:
                    conflicts = departure < other_end + vehicle.turnaround_min
                else:
                    conflicts = end + vehicle.turnaround_min > other_start
                if conflicts:
                    break
            if conflicts:
                continue

            reposition_km = 0.0
            if prior_assignments:
                previous = max(prior_assignments, key=lambda item: item.departure_min)
                previous_route = routes.get(previous.route_id)
                if previous_route and previous_route.stop_ids:
                    reposition_km = road_distances.get(
                        (previous_route.stop_ids[-1], route.stop_ids[0]), 0.0
                    )
            trip_km = sum(route.segment_distance_km)
            score = (
                weights["operating_cost"] * (trip_km + reposition_km) * vehicle.cost_per_km
                + weights["vehicle_km"] * (trip_km + reposition_km)
                + weights["deadhead_km"] * reposition_km
                + weights["vehicle_changes"] * (vehicle_id != assignment.vehicle_id)
                + max(0, estimated_load - vehicle.capacity) * weights["unserved_passengers"]
            )
            candidates.append((score, vehicle_id))

        if not candidates:
            continue
        _score, chosen = min(candidates, key=lambda item: (item[0], item[1]))
        assigned = TripAssignment(
            trip_id=assignment.trip_id,
            route_id=assignment.route_id,
            vehicle_id=chosen,
            departure_min=assignment.departure_min,
        )
        assigned_by_vehicle[chosen].append(assigned)
        route_departures.append(departure)
        output_extras.append(assigned)

    return base_assignments, output_extras


def _resolve_departures(network: Network, scenario: Scenario) -> dict[str, float]:
    """Service departure per trip, stable under scenario vehicle delays.

    Delays are only honoured while they leave the trip inside its own
    departure window *and* leave every consecutive gap on the route within the
    route's headway bounds; otherwise the scheduled time stands.
    """
    delays = scenario.vehicle_delays_min
    departure: dict[str, float] = {}
    for trip in network.trips:
        planned = float(trip.planned_departure_min)
        delayed = planned + delays.get(trip.vehicle_id, 0)
        if trip.departure_window_start_min <= delayed <= trip.departure_window_end_min:
            departure[trip.trip_id] = delayed
        else:
            departure[trip.trip_id] = planned

    for route in network.routes:
        route_trips = [t for t in network.trips if t.route_id == route.route_id]
        route_trips.sort(key=lambda t: (departure[t.trip_id], t.trip_id))
        for previous, current in zip(route_trips, route_trips[1:]):
            gap = departure[current.trip_id] - departure[previous.trip_id]
            if gap < route.min_headway_min or gap > route.max_headway_min:
                for trip in route_trips:
                    departure[trip.trip_id] = float(trip.planned_departure_min)
                break
    return departure


def _extra_dispatches(network: Network, scenario: Scenario,
                      prediction: Optional[PredictionOutput],
                      busy: dict[str, list[tuple[float, float]]],
                      departures: dict[str, list[float]],
                      scheduled: dict[str, list[float]]) -> list[TripAssignment]:
    """Add dispatches for stops the prediction engine flags as HIGH crowding risk.

    An extra trip is only added when it can slot into the route's service
    headway; otherwise the scheduled service would be broken.
    """
    if prediction is None:
        return []
    unavailable = set(scenario.unavailable_vehicle_ids)
    vehicles = network.vehicles_by_id
    routes = network.routes_by_id
    extra: list[TripAssignment] = []
    high = sorted(
        (f for f in prediction.stop_forecasts if f.crowding_risk == "HIGH"),
        key=lambda f: -f.capacity_shortfall,
    )
    for f in high:
        route = _route_serving_stop(routes, f.stop_id)
        if route is None:
            continue
        dep = float(f.time_bucket_min)
        known = departures.get(route.route_id, []) + scheduled.get(route.route_id, [])
        if not _headway_ok(route, known, dep):
            continue
        duration = _duration_min(route, scenario)
        for vid, v in vehicles.items():
            if vid in unavailable or v.vehicle_type not in route.allowed_vehicle_types:
                continue
            if _can_assign(vid, dep, dep + duration, vehicles, busy):
                extra.append(TripAssignment(
                    trip_id=f"X_{f.stop_id}",
                    route_id=route.route_id,
                    vehicle_id=vid,
                    departure_min=int(dep),
                ))
                _mark_busy(busy, vid, dep, dep + duration, v.turnaround_min)
                departures.setdefault(route.route_id, []).append(dep)
                break
    return extra


def _route_serving_stop(routes: dict[str, Route], stop_id: str) -> Optional[Route]:
    for r in routes.values():
        if stop_id in r.stop_ids:
            return r
    return None


def optimize(network: Network, scenario: Scenario,
             prediction: Optional[PredictionOutput] = None,
             time_limit_seconds: Optional[int] = None,
             demand: Optional[list[PassengerDemand]] = None,
             objective_weights: Optional[dict[str, float]] = None) -> Plan:
    weights = normalize_objective_weights(objective_weights)
    unavailable = set(scenario.unavailable_vehicle_ids)
    vehicles = network.vehicles_by_id
    routes = network.routes_by_id
    road_distances = road_distance_matrix(network)
    departure = _resolve_departures(network, scenario)
    peak_loads = _peak_trip_loads(network, departure, demand, scenario)

    depot = _depot_vehicles(network)
    route_used: dict[str, set[str]] = {rid: set() for rid in routes}
    busy: dict[str, list[tuple[float, float]]] = {vid: [] for vid in vehicles}
    started: set[str] = set()
    current_stops = {vehicle_id: vehicle.initial_stop_id for vehicle_id, vehicle in vehicles.items()}
    departures: dict[str, list[float]] = {rid: [] for rid in routes}
    scheduled: dict[str, list[float]] = {rid: [] for rid in routes}
    for trip in network.trips:
        scheduled[trip.route_id].append(departure[trip.trip_id])

    assignments: list[TripAssignment] = []
    unassigned: list[str] = []

    trips = sorted(network.trips, key=lambda t: (departure[t.trip_id], t.trip_id))
    for trip in trips:
        route = routes[trip.route_id]
        rid = trip.route_id
        duration = _duration_min(route, scenario)
        dep = departure[trip.trip_id]
        end = dep + duration

        def usable(vid: str) -> bool:
            v = vehicles[vid]
            if vid in unavailable or v.vehicle_type not in route.allowed_vehicle_types:
                return False
            if not _can_assign(vid, dep, end, vehicles, busy):
                return False
                                                                              
            if vid not in started and route.stop_ids and route.stop_ids[0] != v.initial_stop_id:
                return False
            return True

        def rank(vid: str) -> tuple[int, float, int, int, str]:
            vehicle = vehicles[vid]
            required_capacity = peak_loads.get(trip.trip_id, 0)
            capacity_shortfall = max(0, required_capacity - vehicle.capacity)
            capacity_spare = max(0, vehicle.capacity - required_capacity)
            reposition_km = road_distances.get((current_stops[vid], route.stop_ids[0]), 0.0)
            route_km = sum(route.segment_distance_km)
            weighted_operating_cost = weights["operating_cost"] * (route_km + reposition_km) * vehicle.cost_per_km
            weighted_distance = (
                weights["vehicle_km"] * (route_km + reposition_km)
                + weights["deadhead_km"] * reposition_km
            )
            weighted_change = weights["vehicle_changes"] * (vid != trip.vehicle_id)
            reused_route = 0 if vid in route_used[rid] else 1
            return (
                capacity_shortfall,
                weighted_operating_cost + weighted_distance + weighted_change,
                reused_route,
                capacity_spare,
                vid,
            )

        chosen = min((vid for vid in vehicles if usable(vid)), key=rank, default=None)
        if chosen is None:
            unassigned.append(trip.trip_id)
            continue

        v = vehicles[chosen]
        _mark_busy(busy, chosen, dep, end, v.turnaround_min)
        started.add(chosen)
        route_used[rid].add(chosen)
        current_stops[chosen] = route.stop_ids[-1]
        departures[rid].append(dep)
        assignments.append(TripAssignment(
            trip_id=trip.trip_id, route_id=trip.route_id,
            vehicle_id=chosen, departure_min=int(dep),
        ))

    status = "OK" if not unassigned else "PARTIAL"
    candidate_plans = [Plan(
        plan_type="optimized",
        assignments=assignments,
        unassigned_trip_ids=unassigned,
        solver_status=status,
    )]
    if demand:
        demand_extras = _demand_extra_trips(network, scenario, assignments, demand)
        # Service-priority candidates are deliberately bounded. This gives the
        # evaluator choices in the 50–80% service-improvement range without
        # accepting an unlimited extra-trip expansion.
        budgets = sorted({
            max(1, round(len(demand_extras) * fraction))
            for fraction in (0.5, 0.6, 0.75)
        }) if demand_extras else []
        network_trip_ids = {trip.trip_id for trip in network.trips}
        for budget in budgets:
            proposed_extras = demand_extras[:budget]
            candidate_assignments, assigned_demand_extras = _assign_with_extras(
                network, scenario, assignments, proposed_extras, demand, weights
            )
            if not assigned_demand_extras:
                continue
            all_candidate_assignments = [*candidate_assignments, *assigned_demand_extras]
            capacity_extras = _capacity_extra_trips(
                network, scenario, all_candidate_assignments, demand
            )
            _with_capacity, assigned_capacity_extras = _assign_with_extras(
                network, scenario, all_candidate_assignments, capacity_extras, demand, weights
            )
            candidate_plans.append(Plan(
                plan_type="optimized",
                assignments=[
                    item for item in all_candidate_assignments
                    if item.trip_id in network_trip_ids
                ],
                extra_trips=[
                    item for item in all_candidate_assignments
                    if item.trip_id not in network_trip_ids
                ] + assigned_capacity_extras,
                unassigned_trip_ids=unassigned,
                solver_status=status,
            ))
    elif prediction is not None:
        extra = _extra_dispatches(network, scenario, prediction, busy, departures, scheduled)
        if extra:
            candidate_plans.append(Plan(
                plan_type="optimized",
                assignments=assignments,
                extra_trips=extra,
                unassigned_trip_ids=unassigned,
                solver_status=status,
            ))

    baseline = fallback_plan(network, scenario)
    baseline_score, baseline_detail = score_plan(
        network, scenario, baseline, demand, weights
    )
    baseline_validation = baseline_detail["validation"]
    baseline_violation_counts = Counter(item["code"] for item in baseline_validation["violations"])
    best_plan = baseline
    best_score = baseline_score
    for candidate in candidate_plans:
        candidate_score, candidate_detail = score_plan(
            network, scenario, candidate, demand, weights
        )
        candidate_validation = candidate_detail["validation"]
        candidate_violation_counts = Counter(
            item["code"] for item in candidate_validation["violations"]
        )
        candidate_is_worse_on_hard_constraints = (
            baseline_validation["feasible"] and not candidate_validation["feasible"]
        ) or (
            not candidate_validation["feasible"]
            and any(
                candidate_violation_counts[code] > baseline_violation_counts[code]
                for code in candidate_violation_counts.keys() | baseline_violation_counts.keys()
            )
        )
        if not candidate_is_worse_on_hard_constraints and candidate_score < best_score - 1e-6:
            best_plan = candidate
            best_score = candidate_score

    if best_plan is baseline:
        return Plan(
            plan_type="optimized",
            assignments=baseline.assignments,
            extra_trips=[],
            unassigned_trip_ids=baseline.unassigned_trip_ids,
            solver_status="BASELINE_RETAINED",
        )
    return best_plan
