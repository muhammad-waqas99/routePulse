"""Independent validator tests."""

from __future__ import annotations

from app.optimizer.model import Plan, PlannedTrip, parse_time
from app.optimizer.solve import build_optimized_plan
from app.services.operations_service import get_network_model
from app.services.scenario_service import get_scenario
from app.validation.constraints import validate_plan


def _failed_ids(result):
    return {check.id for check in result.constraints if not check.passed}


def test_valid_optimized_plan_passes_validation():
    network = get_network_model()
    scenario = get_scenario("normal_operations")
    plan = build_optimized_plan(network, scenario)

    result = validate_plan(network, scenario, plan)

    assert result.valid is True
    assert result.hardViolationCount == 0
    assert all(check.passed for check in result.constraints)
    assert {check.id for check in result.constraints} == {
        "vehicle-assignment",
        "vehicle-availability",
        "departure-windows",
        "vehicle-turnaround",
        "segment-capacity",
        "transfer-buffer",
    }


def test_unknown_vehicle_and_route_are_detected():
    network = get_network_model()
    scenario = get_scenario("normal_operations")
    plan = Plan(
        plan_id="bad",
        label="bad",
        trips=[
            PlannedTrip(
                trip_id="X1",
                route_id="R-UNKNOWN",
                vehicle_id="BUS-UNKNOWN",
                departure_min=parse_time("08:00"),
            )
        ],
    )

    result = validate_plan(network, scenario, plan)

    assert result.valid is False
    assert "vehicle-assignment" in _failed_ids(result)


def test_unavailable_vehicle_is_detected():
    network = get_network_model()
    scenario = get_scenario("vehicle_unavailable")
    plan = Plan(
        plan_id="bad",
        label="bad",
        trips=[
            PlannedTrip(
                trip_id="X1",
                route_id="R1",
                vehicle_id="BUS02",  # grounded in this scenario
                departure_min=parse_time("08:00"),
            )
        ],
    )

    result = validate_plan(network, scenario, plan)
    assert "vehicle-availability" in _failed_ids(result)


def test_departure_window_violation_is_detected():
    network = get_network_model()
    scenario = get_scenario("normal_operations")
    plan = Plan(
        plan_id="bad",
        label="bad",
        trips=[
            PlannedTrip(
                trip_id="X1",
                route_id="R1",
                vehicle_id="BUS01",
                departure_min=parse_time("07:00"),  # before window
            )
        ],
    )

    result = validate_plan(network, scenario, plan)
    assert "departure-windows" in _failed_ids(result)


def test_capacity_and_turnaround_violations_are_detected():
    network = get_network_model()
    scenario = get_scenario("normal_operations")

    plan = Plan(
        plan_id="bad",
        label="bad",
        trips=[
            PlannedTrip(
                trip_id="X1",
                route_id="R1",
                vehicle_id="BUS01",
                departure_min=parse_time("08:00"),
                # BUS01 capacity 40; 500 passengers clearly overloads it.
                boardings={"S02": 500},
            ),
            # Same vehicle leaves again one minute later (turnaround conflict).
            PlannedTrip(
                trip_id="X2",
                route_id="R1",
                vehicle_id="BUS01",
                departure_min=parse_time("08:01"),
            ),
        ],
    )

    result = validate_plan(network, scenario, plan)
    failed = _failed_ids(result)

    assert "segment-capacity" in failed
    assert "vehicle-turnaround" in failed
    assert result.hardViolationCount >= 2
