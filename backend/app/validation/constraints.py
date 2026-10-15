"""Independent validation of a proposed plan.

The validator never trusts the optimizer's success flag. It re-derives every
constraint from the raw plan + network and reports a structured pass/fail for
each check. The labels mirror the ones the frontend already displays.
"""

from __future__ import annotations

from app.optimizer.model import NetworkModel, Plan
from app.schemas.optimization import ConstraintCheck, ValidationResult
from app.schemas.scenario import Scenario

# Constraint identifiers/labels shared with the frontend.
CHECK_DEFINITIONS = [
    ("vehicle-assignment", "Vehicle assignment"),
    ("vehicle-availability", "Vehicle availability"),
    ("departure-windows", "Departure windows"),
    ("vehicle-turnaround", "Vehicle turnaround"),
    ("segment-capacity", "Segment capacity"),
    ("transfer-buffer", "Transfer buffer"),
]


def validate_plan(
    network: NetworkModel, scenario: Scenario, plan: Plan
) -> ValidationResult:
    """Validate ``plan`` against the network and scenario constraints."""

    details: dict[str, tuple[bool, str]] = {}
    details["vehicle-assignment"] = _check_vehicle_assignment(network, plan)
    details["vehicle-availability"] = _check_vehicle_availability(
        network, scenario, plan
    )
    details["departure-windows"] = _check_departure_windows(
        network, scenario, plan
    )
    details["vehicle-turnaround"] = _check_turnaround(network, plan)
    details["segment-capacity"] = _check_segment_capacity(network, plan)
    details["transfer-buffer"] = _check_transfer_buffer(network, plan)

    checks: list[ConstraintCheck] = []
    for check_id, label in CHECK_DEFINITIONS:
        passed, detail = details[check_id]
        checks.append(
            ConstraintCheck(
                id=check_id, label=label, passed=passed, detail=detail or None
            )
        )

    hard = sum(1 for check in checks if not check.passed)
    return ValidationResult(
        valid=hard == 0, hardViolationCount=hard, constraints=checks
    )


def _check_vehicle_assignment(
    network: NetworkModel, plan: Plan
) -> tuple[bool, str]:
    problems: list[str] = []
    for trip in plan.trips:
        if trip.route_id not in network.routes:
            problems.append(f"{trip.trip_id}: unknown route {trip.route_id}")
        if trip.vehicle_id not in network.vehicles:
            problems.append(f"{trip.trip_id}: unknown vehicle {trip.vehicle_id}")
    if problems:
        return False, "; ".join(problems[:3])
    return True, "All trips reference known routes and vehicles."


def _check_vehicle_availability(
    network: NetworkModel, scenario: Scenario, plan: Plan
) -> tuple[bool, str]:
    unavailable = set(scenario.unavailableVehicleIds)
    used = {trip.vehicle_id for trip in plan.trips}

    problems: list[str] = []
    for vehicle_id in sorted(used):
        vehicle = network.vehicles.get(vehicle_id)
        if vehicle is None:
            problems.append(f"{vehicle_id}: not in fleet")
            continue
        if vehicle.status == "unavailable" or vehicle_id in unavailable:
            problems.append(f"{vehicle_id}: unavailable")

    if len(used) > scenario.availableVehicles:
        problems.append(
            f"{len(used)} vehicles used but only "
            f"{scenario.availableVehicles} available"
        )

    if problems:
        return False, "; ".join(problems[:3])
    return True, f"{len(used)} vehicle(s) used, all available."


def _check_departure_windows(
    network: NetworkModel, scenario: Scenario, plan: Plan
) -> tuple[bool, str]:
    from app.optimizer.model import parse_period

    start, end = parse_period(scenario.affectedPeriod)
    horizon_end = end + scenario.evaluationHorizonMin

    problems: list[str] = []
    for trip in plan.trips:
        route = network.routes.get(trip.route_id)
        if route is None:
            continue
        if trip.departure_min < start:
            problems.append(
                f"{trip.trip_id}: departs before window"
            )
        if trip.departure_min > end:
            problems.append(f"{trip.trip_id}: departs after window")
        if trip.departure_min + route.duration_min > horizon_end:
            problems.append(f"{trip.trip_id}: arrives after horizon")

    if problems:
        return False, "; ".join(problems[:3])
    return True, "All departures fall inside the service window."


def _check_turnaround(
    network: NetworkModel, plan: Plan
) -> tuple[bool, str]:
    turnaround = network.parameters.turnaroundMin
    by_vehicle: dict[str, list] = {}
    for trip in plan.trips:
        by_vehicle.setdefault(trip.vehicle_id, []).append(trip)

    problems: list[str] = []
    for vehicle_id, trips in by_vehicle.items():
        trips = sorted(trips, key=lambda t: t.departure_min)
        for earlier, later in zip(trips, trips[1:]):
            route = network.routes.get(earlier.route_id)
            if route is None:
                continue
            ready = earlier.departure_min + route.duration_min + turnaround
            if later.departure_min < ready:
                problems.append(
                    f"{vehicle_id}: {later.trip_id} departs before "
                    f"{earlier.trip_id} is ready"
                )

    if problems:
        return False, "; ".join(problems[:3])
    return True, f"All vehicles respect a {turnaround:g} min turnaround."


def _check_segment_capacity(
    network: NetworkModel, plan: Plan
) -> tuple[bool, str]:
    problems: list[str] = []
    for trip in plan.trips:
        route = network.routes.get(trip.route_id)
        vehicle = network.vehicles.get(trip.vehicle_id)
        if route is None or vehicle is None:
            continue
        cumulative = 0
        for stop_id in route.stop_ids:
            cumulative += trip.boardings.get(stop_id, 0)
            if cumulative > vehicle.capacity:
                problems.append(
                    f"{trip.trip_id}: load {cumulative} exceeds capacity "
                    f"{vehicle.capacity} at {stop_id}"
                )
                break

    if problems:
        return False, "; ".join(problems[:3])
    return True, "No trip exceeds its vehicle capacity."


def _check_transfer_buffer(
    network: NetworkModel, plan: Plan
) -> tuple[bool, str]:
    buffer = network.parameters.transferBufferMin
    by_vehicle: dict[str, list] = {}
    for trip in plan.trips:
        by_vehicle.setdefault(trip.vehicle_id, []).append(trip)

    problems: list[str] = []
    for vehicle_id, trips in by_vehicle.items():
        trips = sorted(trips, key=lambda t: t.departure_min)
        for earlier, later in zip(trips, trips[1:]):
            route = network.routes.get(earlier.route_id)
            if route is None:
                continue
            arrival_next = later.departure_min  # departure of next trip
            gap = arrival_next - (earlier.departure_min + route.duration_min)
            if gap < buffer:
                problems.append(
                    f"{vehicle_id}: only {gap:.0f} min terminal buffer"
                )

    if problems:
        return False, "; ".join(problems[:3])
    return True, f"All terminal buffers meet {buffer:g} min."


def checks_to_frontend(result: ValidationResult) -> list[ConstraintCheck]:
    """Return the constraint list in the frontend's compact shape."""

    return [
        ConstraintCheck(id=check.id, label=check.label, passed=check.passed)
        for check in result.constraints
    ]
