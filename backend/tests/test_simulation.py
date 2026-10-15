"""Simulation determinism, capacity and metric-derivation tests."""

from __future__ import annotations

from app.evaluation.metrics import compute_plan_metrics
from app.optimizer.model import (
    DemandBatch,
    NetworkModel,
    Plan,
    PlannedTrip,
    build_demand,
    parse_time,
)
from app.services.operations_service import get_network_model
from app.services.scenario_service import get_scenario
from app.simulation.engine import simulate


def _single_trip_plan(vehicle_id: str, departure: str, trip_id: str = "X1") -> Plan:
    return Plan(
        plan_id="test",
        label="Test plan",
        trips=[
            PlannedTrip(
                trip_id=trip_id,
                route_id="R1",
                vehicle_id=vehicle_id,
                departure_min=parse_time(departure),
            )
        ],
    )


def test_simulation_is_deterministic():
    network = get_network_model()
    scenario = get_scenario("normal_operations")
    demand = [
        DemandBatch(stop_id="S02", route_id="R1", time_min=parse_time("08:00"), count=20),
        DemandBatch(stop_id="S03", route_id="R1", time_min=parse_time("08:00"), count=10),
    ]
    plan = _single_trip_plan("BUS01", "08:00")

    first = simulate(network, scenario, plan, demand)
    second = simulate(network, scenario, plan, demand)

    assert (first.served, first.unserved, first.distance_km, first.total_wait_min) == (
        second.served,
        second.unserved,
        second.distance_km,
        second.total_wait_min,
    )
    assert first.eta_abs_errors == second.eta_abs_errors


def test_waiting_time_is_measured_from_simulation():
    network = get_network_model()
    scenario = get_scenario("normal_operations")
    demand = [
        DemandBatch(stop_id="S03", route_id="R1", time_min=parse_time("08:00"), count=3)
    ]
    plan = _single_trip_plan("BUS01", "08:00")

    result = simulate(network, scenario, plan, demand)

    assert result.served == 3
    assert result.unserved == 0

    route = network.route("R1")
    load_factor = 1.5  # single demand bucket -> maximum deterministic congestion
    expected_wait = round(3 * route.offsets_min[1] * load_factor, 3)
    assert result.total_wait_min == expected_wait
    assert result.average_wait_min == round(expected_wait / 3, 2)


def test_capacity_is_enforced_and_unserved_classified():
    network = get_network_model()
    scenario = get_scenario("normal_operations")
    demand = [
        # 100 passengers, bus capacity 40 -> 60 capacity-denied.
        DemandBatch(stop_id="S02", route_id="R1", time_min=parse_time("08:00"), count=100),
        # 5 passengers arrive long after the only bus passed -> missed connection.
        DemandBatch(stop_id="S04", route_id="R1", time_min=parse_time("10:00"), count=5),
    ]
    plan = _single_trip_plan("BUS01", "08:00")

    result = simulate(network, scenario, plan, demand)

    assert result.served == 40
    assert result.capacity_denied == 60
    assert result.missed_connections == 5
    assert result.unserved == 65
    assert result.unserved_rate == 61.9


def test_metrics_are_derived_from_simulation_output():
    network = get_network_model()
    scenario = get_scenario("normal_operations")
    demand = [
        DemandBatch(stop_id="S02", route_id="R1", time_min=parse_time("08:00"), count=200)
    ]
    plan = _single_trip_plan("BUS01", "08:00")
    sim = simulate(network, scenario, plan, demand)

    metrics = compute_plan_metrics(sim, plan)

    assert metrics.unserved_passengers == sim.unserved
    assert metrics.missed_connections == sim.missed_connections
    assert metrics.average_waiting_time_min == sim.average_wait_min
    assert metrics.vehicle_distance_km == sim.distance_km
    assert metrics.capacity_violations == sim.capacity_denied
    assert metrics.served == sim.served


def test_baseline_and_optimized_share_identical_demand():
    network = get_network_model()
    scenario = get_scenario("demand_spike")
    demand = build_demand(network, scenario)
    total_demand = sum(batch.count for batch in demand)
    assert total_demand > 0

    # A run persisted by the pipeline reports outcomes that must add up to the
    # same total demand for both plans.
    from app.services.pipeline_service import run_optimization
    from app.services import run_store

    response = run_optimization("demand_spike")
    run = run_store.get_run(response.runId)
    assert run is not None
    assert run.passengerOutcome is not None

    outcome = run.passengerOutcome
    assert outcome.total == total_demand
    assert outcome.baselineServed + outcome.baselineUnserved == total_demand
    assert outcome.optimizedServed + outcome.optimizedUnserved == total_demand
