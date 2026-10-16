"""Independent feasibility validator.

OWNED BY: validation workstream (P0 — never cut).

``validate_plan()`` must NOT rely on the optimizer's own feasibility status. It
independently recomputes every hard constraint and returns structured
violations. Required checks (from ``Wild Bugs.md``):

- every scheduled trip has exactly one valid vehicle assignment
- vehicle types match route requirements
- vehicles are available for their assigned trips
- no overlapping trips or insufficient turnaround
- departure times obey their allowed windows
- every segment's passenger load respects vehicle capacity
- connections satisfy the configured transfer buffer
- required service constraints are respected

Runs on the baseline too; pre-existing baseline violations must be reported.

Design notes
------------
* The validator never trusts ``Plan.solver_status`` (or any optimizer flag): it
  only inspects the proposed assignments and the canonical network/scenario.
* It does not mutate its inputs.
* Violations are returned in a deterministic order for identical inputs.
* Passenger-capacity checking needs an explicit passenger allocation. When the
  caller supplies ``demand`` (canonical ``PassengerDemand`` groups) the load on
  *every route segment* is computed with a deterministic boarding/alighting
  policy. When demand is absent the capacity constraint is reported as
  **unverified** rather than being silently assumed to pass.
* Transfer checking needs configured connections. When ``connections`` is
  absent nothing is configured, so transfer validation is inert. When it is
  supplied without a buffer the check is reported unverified.
"""
from __future__ import annotations

from typing import Any, Optional

from app.schemas.network import Network, Route, Vehicle
from app.schemas.plan import Plan
from app.schemas.scenario import PassengerDemand, Scenario

                                                                               
                                      
                                                                               
UNASSIGNED_TRIP = "UNASSIGNED_TRIP"
DUPLICATE_ASSIGNMENT = "DUPLICATE_ASSIGNMENT"
UNKNOWN_TRIP = "UNKNOWN_TRIP"
UNKNOWN_ROUTE = "UNKNOWN_ROUTE"
UNKNOWN_VEHICLE = "UNKNOWN_VEHICLE"
ROUTE_MISMATCH = "ROUTE_MISMATCH"
VEHICLE_TYPE_INCOMPATIBLE = "VEHICLE_TYPE_INCOMPATIBLE"
VEHICLE_UNAVAILABLE = "VEHICLE_UNAVAILABLE"
VEHICLE_AVAILABILITY = "VEHICLE_AVAILABILITY"
INITIAL_STOP_MISMATCH = "INITIAL_STOP_MISMATCH"
DEPARTURE_WINDOW = "DEPARTURE_WINDOW"
VEHICLE_OVERLAP = "VEHICLE_OVERLAP"
INSUFFICIENT_TURNAROUND = "INSUFFICIENT_TURNAROUND"
CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
HEADWAY_TOO_SHORT = "HEADWAY_TOO_SHORT"
HEADWAY_EXCEEDED = "HEADWAY_EXCEEDED"
ROUTE_UNCOVERED = "ROUTE_UNCOVERED"
MISSED_CONNECTION = "MISSED_CONNECTION"

                                                                               
CAPACITY_UNVERIFIED = "CAPACITY_UNVERIFIED"
TRANSFER_UNVERIFIED = "TRANSFER_UNVERIFIED"

                                              
_CODE_ORDER = [
    UNASSIGNED_TRIP,
    DUPLICATE_ASSIGNMENT,
    UNKNOWN_TRIP,
    UNKNOWN_ROUTE,
    UNKNOWN_VEHICLE,
    ROUTE_MISMATCH,
    VEHICLE_TYPE_INCOMPATIBLE,
    VEHICLE_UNAVAILABLE,
    VEHICLE_AVAILABILITY,
    INITIAL_STOP_MISMATCH,
    DEPARTURE_WINDOW,
    VEHICLE_OVERLAP,
    INSUFFICIENT_TURNAROUND,
    CAPACITY_EXCEEDED,
    HEADWAY_TOO_SHORT,
    HEADWAY_EXCEEDED,
    ROUTE_UNCOVERED,
    MISSED_CONNECTION,
]
_CODE_RANK = {code: i for i, code in enumerate(_CODE_ORDER)}


def _violation(code: str, **fields: Any) -> dict:
    return {"code": code, **fields}


def _unverified(code: str, reason: str) -> dict:
    return {"code": code, "reason": reason}


def _sort_key(v: dict) -> tuple:
    return (
        _CODE_RANK.get(v.get("code", ""), len(_CODE_ORDER)),
        str(v.get("trip_id", "")),
        str(v.get("vehicle_id", "")),
        str(v.get("route_id", "")),
        int(v.get("segment_index", -1)),
    )


def route_duration_min(route: Route) -> float:
    """Established route-duration semantics: sum of scheduled segment times.

    Mirrors ``app.optimizer.solve.route_duration_min`` so the validator and the
    optimizer agree on what "trip length" means without importing the optimizer.
    """
    return sum(route.segment_travel_min)


def _duration(route: Route, scenario: Optional[Scenario]) -> float:
    """Route duration adjusted by the scenario's travel-time multiplier."""
    duration = route_duration_min(route)
    if scenario is not None:
        duration *= scenario.travel_time_multipliers.get(route.route_id, 1.0)
    return duration


def _resolve(plan: Plan):
    """Yield (assignment, is_extra) pairs for regular assignments + extras."""
    for assignment in plan.assignments:
        yield assignment, False
    for assignment in plan.extra_trips:
        yield assignment, True


def _check_capacity(
    trip_specs: dict[str, tuple[Route, Vehicle, float]],
    demand: list[PassengerDemand],
    violations: list[dict],
) -> None:
    """Deterministically allocate demand to trips and check every segment.

    Allocation policy (deterministic, documented): each demand group boards the
    earliest-departing assigned trip whose route visits its origin *before* its
    destination, that departs at or after the arrival time and within the
    group's ``max_wait_min``. Groups with no eligible trip are simply unserved
    (that is an outcome metric, not a hard-constraint violation). On-board load
    is accumulated only across the segments actually traversed, so boarding and
    alighting both affect the segment loads.

    ``trip_specs`` maps ``trip_id -> (route, vehicle, departure_min)``.
    """
    loads: dict[str, list[int]] = {
        trip_id: [0] * max(0, len(route.stop_ids) - 1)
        for trip_id, (route, _vehicle, _dep) in trip_specs.items()
    }

    for group in demand:
        chosen = None
        for trip_id, (route, _vehicle, departure) in trip_specs.items():
            stops = route.stop_ids
            if group.origin_stop_id not in stops or group.destination_stop_id not in stops:
                continue
            i = stops.index(group.origin_stop_id)
            j = stops.index(group.destination_stop_id)
            if i >= j:
                continue
            if departure < group.arrival_time_min:
                continue
            if departure > group.arrival_time_min + group.max_wait_min:
                continue
            key = (departure, trip_id)
            if chosen is None or key < chosen[0]:
                chosen = (key, trip_id, i, j)
        if chosen is None:
            continue
        _key, trip_id, i, j = chosen
        for segment in range(i, j):
            loads[trip_id][segment] += group.passenger_count

    for trip_id, segments in loads.items():
        route, vehicle, _dep = trip_specs[trip_id]
        for segment_index, load in enumerate(segments):
            if load > vehicle.capacity:
                violations.append(_violation(
                    CAPACITY_EXCEEDED,
                    trip_id=trip_id,
                    vehicle_id=vehicle.vehicle_id,
                    route_id=route.route_id,
                    segment_index=segment_index,
                    actual_load=load,
                    capacity=vehicle.capacity,
                ))


def _check_transfers(
    connections: list[dict],
    trip_times: dict[str, tuple[float, float]],
    violations: list[dict],
    unverified: list[dict],
) -> None:
    """Check configured transfer buffers between assigned trips.

    ``connections`` entries look like
    ``{"from_trip_id": ..., "to_trip_id": ..., "buffer_min": ...}``. A missed
    connection is ``arrival(from) + buffer > departure(to)``. Trips without an
    assignment, or entries without a buffer, are reported as unverified rather
    than guessed.
    """
    reported_unverified = False
    for conn in connections:
        from_id = conn.get("from_trip_id")
        to_id = conn.get("to_trip_id")
        buffer_min = conn.get("buffer_min")
        if from_id not in trip_times or to_id not in trip_times:
            if not reported_unverified:
                unverified.append(_unverified(
                    TRANSFER_UNVERIFIED,
                    "one or more connection endpoints were not assigned trips",
                ))
                reported_unverified = True
            continue
        if buffer_min is None:
            if not reported_unverified:
                unverified.append(_unverified(
                    TRANSFER_UNVERIFIED,
                    "connection was supplied without a buffer_min value",
                ))
                reported_unverified = True
            continue
        arrival = trip_times[from_id][1]
        departure = trip_times[to_id][0]
        if arrival + buffer_min > departure:
            violations.append(_violation(
                MISSED_CONNECTION,
                from_trip_id=from_id,
                to_trip_id=to_id,
                arrival_min=arrival,
                departure_min=departure,
                buffer_min=buffer_min,
            ))


def validate_plan(
    network: Network,
    plan: Plan,
    scenario: Optional[Scenario] = None,
    demand: Optional[list[PassengerDemand]] = None,
    connections: Optional[list[dict]] = None,
) -> dict:
    """Independently validate ``plan`` against ``network`` (+ ``scenario``).

    Returns ``{feasible, hard_violation_count, violations, unverified_constraints}``.
    ``feasible`` is true only when there are no hard violations *and* no required
    hard constraint was left unverified.
    """
    if scenario is None:
        scenario = Scenario(scenario_id=plan.plan_type)

    routes = network.routes_by_id
    vehicles = network.vehicles_by_id
    canonical = {t.trip_id: t for t in network.trips}
    unavailable = set(scenario.unavailable_vehicle_ids)

    violations: list[dict] = []
    unverified: list[dict] = []

                                                                              
    assigned_count: dict[str, int] = {}
    for assignment in plan.assignments:
        assigned_count[assignment.trip_id] = assigned_count.get(assignment.trip_id, 0) + 1

    for trip_id, count in sorted(assigned_count.items()):
        if count > 1:
            violations.append(_violation(
                DUPLICATE_ASSIGNMENT, trip_id=trip_id, assignment_count=count,
            ))

    for trip_id, trip in sorted(canonical.items()):
        if assigned_count.get(trip_id, 0) == 0:
            violations.append(_violation(
                UNASSIGNED_TRIP,
                trip_id=trip_id,
                route_id=trip.route_id,
                planned_vehicle_id=trip.vehicle_id,
            ))

                                                                             
    trip_times: dict[str, tuple[float, float]] = {}
    trip_info: dict[str, tuple[Route, Vehicle]] = {}
    by_vehicle: dict[str, list[tuple[float, float, str]]] = {}

    for assignment, is_extra in _resolve(plan):
        trip = canonical.get(assignment.trip_id)
        if trip is None and not is_extra:
            violations.append(_violation(
                UNKNOWN_TRIP,
                trip_id=assignment.trip_id,
                route_id=assignment.route_id,
                vehicle_id=assignment.vehicle_id,
            ))

        route = routes.get(assignment.route_id)
        vehicle = vehicles.get(assignment.vehicle_id)
        if route is None:
            violations.append(_violation(
                UNKNOWN_ROUTE,
                trip_id=assignment.trip_id,
                route_id=assignment.route_id,
            ))
        if vehicle is None:
            violations.append(_violation(
                UNKNOWN_VEHICLE,
                trip_id=assignment.trip_id,
                vehicle_id=assignment.vehicle_id,
            ))
        if route is None or vehicle is None:
            continue

        if trip is not None and trip.route_id != assignment.route_id:
            violations.append(_violation(
                ROUTE_MISMATCH,
                trip_id=assignment.trip_id,
                route_id=assignment.route_id,
                expected_route_id=trip.route_id,
            ))

        if vehicle.vehicle_type not in route.allowed_vehicle_types:
            violations.append(_violation(
                VEHICLE_TYPE_INCOMPATIBLE,
                trip_id=assignment.trip_id,
                vehicle_id=vehicle.vehicle_id,
                vehicle_type=vehicle.vehicle_type,
                allowed_vehicle_types=list(route.allowed_vehicle_types),
                route_id=route.route_id,
            ))

        if assignment.vehicle_id in unavailable:
            violations.append(_violation(
                VEHICLE_UNAVAILABLE,
                trip_id=assignment.trip_id,
                vehicle_id=vehicle.vehicle_id,
            ))

        duration = _duration(route, scenario)
        departure = float(assignment.departure_min)
        end = departure + duration

        if departure < vehicle.available_from_min or end > vehicle.available_until_min:
            violations.append(_violation(
                VEHICLE_AVAILABILITY,
                trip_id=assignment.trip_id,
                vehicle_id=vehicle.vehicle_id,
                departure_min=assignment.departure_min,
                arrival_min=end,
                available_from_min=vehicle.available_from_min,
                available_until_min=vehicle.available_until_min,
            ))

        if trip is not None and not (
            trip.departure_window_start_min <= departure <= trip.departure_window_end_min
        ):
            violations.append(_violation(
                DEPARTURE_WINDOW,
                trip_id=assignment.trip_id,
                route_id=assignment.route_id,
                departure_min=assignment.departure_min,
                window_start_min=trip.departure_window_start_min,
                window_end_min=trip.departure_window_end_min,
            ))

                                                                          
                                                       
        trip_times.setdefault(assignment.trip_id, (departure, end))
        trip_info.setdefault(assignment.trip_id, (route, vehicle))
        by_vehicle.setdefault(vehicle.vehicle_id, []).append(
            (departure, end, assignment.trip_id)
        )

                                                                             
    for vehicle_id, items in by_vehicle.items():
        vehicle = vehicles[vehicle_id]
        items.sort(key=lambda x: (x[0], x[2]))

                                                                        
                                                                              
        first_trip_id = items[0][2]
        first_route = trip_info[first_trip_id][0]
        if first_route.stop_ids and first_route.stop_ids[0] != vehicle.initial_stop_id:
            violations.append(_violation(
                INITIAL_STOP_MISMATCH,
                vehicle_id=vehicle_id,
                trip_id=first_trip_id,
                initial_stop_id=vehicle.initial_stop_id,
                route_start_stop_id=first_route.stop_ids[0],
            ))

        for previous, current in zip(items, items[1:]):
            if current[0] < previous[1]:
                violations.append(_violation(
                    VEHICLE_OVERLAP,
                    vehicle_id=vehicle_id,
                    trip_id=current[2],
                    previous_trip_id=previous[2],
                    previous_end_min=previous[1],
                    departure_min=current[0],
                ))
            elif current[0] < previous[1] + vehicle.turnaround_min:
                violations.append(_violation(
                    INSUFFICIENT_TURNAROUND,
                    vehicle_id=vehicle_id,
                    trip_id=current[2],
                    previous_trip_id=previous[2],
                    previous_end_min=previous[1],
                    departure_min=current[0],
                    turnaround_min=vehicle.turnaround_min,
                ))

                                                                             
    departures_by_route: dict[str, list[tuple[float, str]]] = {}
    for trip_id, (departure, _end) in trip_times.items():
        route, _vehicle = trip_info[trip_id]
        departures_by_route.setdefault(route.route_id, []).append((departure, trip_id))

    for route_id, departures in departures_by_route.items():
        route = routes[route_id]
        departures.sort(key=lambda x: (x[0], x[1]))
        for (d1, t1), (d2, t2) in zip(departures, departures[1:]):
            gap = d2 - d1
            if gap < route.min_headway_min:
                violations.append(_violation(
                    HEADWAY_TOO_SHORT,
                    route_id=route_id,
                    from_trip_id=t1,
                    to_trip_id=t2,
                    actual_headway_min=gap,
                    min_headway_min=route.min_headway_min,
                ))
            if gap > route.max_headway_min:
                violations.append(_violation(
                    HEADWAY_EXCEEDED,
                    route_id=route_id,
                    from_trip_id=t1,
                    to_trip_id=t2,
                    actual_headway_min=gap,
                    max_headway_min=route.max_headway_min,
                ))

    required_routes = {trip.route_id for trip in network.trips}
    served_routes = {
        trip_info[trip_id][0].route_id
        for trip_id in trip_times
        if trip_id in trip_info
    }
    for route_id in sorted(required_routes - served_routes):
        violations.append(_violation(ROUTE_UNCOVERED, route_id=route_id))

                                                                             
    if demand is None:
        unverified.append(_unverified(
            CAPACITY_UNVERIFIED,
            "no passenger demand supplied; segment loads cannot be computed",
        ))
    else:
        capacity_specs = {
            trip_id: (trip_info[trip_id][0], trip_info[trip_id][1], trip_times[trip_id][0])
            for trip_id in trip_times
            if trip_id in trip_info
        }
        _check_capacity(capacity_specs, demand, violations)

                                                                              
    if connections:
        _check_transfers(connections, trip_times, violations, unverified)

    violations.sort(key=_sort_key)
    unverified.sort(key=lambda v: v["code"])

    feasible = len(violations) == 0 and len(unverified) == 0
    return {
        "feasible": feasible,
        "hard_violation_count": len(violations),
        "violations": violations,
        "unverified_constraints": unverified,
    }
