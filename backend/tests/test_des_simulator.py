"""Tests for the discrete-event, plan-executing simulator."""
from __future__ import annotations

import pytest

from app.schemas.network import Network, Route, Stop, Trip, Vehicle
from app.schemas.plan import Plan, TripAssignment
from app.schemas.scenario import PassengerDemand, Scenario
from app.simulation.engine import simulate


def _network() -> Network:
    stops = [
        Stop(stop_id=f"S{i}", name=f"S{i}", lat=0.0, lon=0.0) for i in range(1, 5)
    ]
    route = Route(
        route_id="R1",
        stop_ids=["S1", "S2", "S3", "S4"],
        segment_travel_min=[5.0, 5.0, 5.0],
        segment_distance_km=[1.0, 1.0, 1.0],
        allowed_vehicle_types=["shuttle"],
        min_headway_min=5,
        max_headway_min=120,
    )
    vehicles = [
        Vehicle(vehicle_id="V1", capacity=10, initial_stop_id="S1", turnaround_min=4),
        Vehicle(vehicle_id="V2", capacity=10, initial_stop_id="S1", turnaround_min=4),
    ]

    def trip(tid: str, vid: str, dep: int) -> Trip:
        return Trip(
            trip_id=tid,
            route_id="R1",
            vehicle_id=vid,
            planned_departure_min=dep,
            departure_window_start_min=dep - 5,
            departure_window_end_min=dep + 5,
        )

    trips = [trip("T1", "V1", 60), trip("T2", "V1", 90), trip("T3", "V2", 70), trip("T4", "V2", 105)]
    return Network(stops=stops, routes=[route], vehicles=vehicles, trips=trips)


def _plan() -> Plan:
    return Plan(
        plan_type="baseline",
        assignments=[
            TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
            TripAssignment(trip_id="T2", route_id="R1", vehicle_id="V1", departure_min=90),
            TripAssignment(trip_id="T3", route_id="R1", vehicle_id="V2", departure_min=70),
            TripAssignment(trip_id="T4", route_id="R1", vehicle_id="V2", departure_min=105),
        ],
    )


def _demand(*items) -> list[PassengerDemand]:
    return list(items)


def test_feasible_plan_serves_and_tracks_metrics() -> None:
    net, plan = _network(), _plan()
    demand = _demand(
        PassengerDemand(
            demand_id="D1", origin_stop_id="S1", destination_stop_id="S3",
            arrival_time_min=58, passenger_count=5,
        ),
        PassengerDemand(
            demand_id="D2", origin_stop_id="S2", destination_stop_id="S4",
            arrival_time_min=72, passenger_count=3,
        ),
    )
    result = simulate(net, plan, Scenario(scenario_id="normal"), demand=demand, seed=42)

    assert result.feasible is True
    assert result.status == "OK"
    assert result.metrics.total_demand == 8
    assert result.metrics.served_passengers == 8
    assert result.metrics.unserved_passengers == 0
    assert result.metrics.capacity_violations == 0
    assert result.metrics.vehicle_km == pytest.approx(12.0)                              
    assert result.metrics.avg_wait_min > 0
    assert result.passenger_outcomes.waiting_at_horizon == 0
    assert result.events                             
    assert result.metrics.eta_mae_min is None
    assert result.metrics.eta_observations == 0


def test_passenger_arriving_at_departure_time_boards() -> None:
    net, plan = _network(), _plan()
    demand = _demand(
        PassengerDemand(
            demand_id="D1", origin_stop_id="S1", destination_stop_id="S4",
            arrival_time_min=60, passenger_count=4,
        )
    )
    result = simulate(net, plan, Scenario(scenario_id="normal"), demand=demand)
    assert result.metrics.served_passengers == 4


def test_group_splits_at_capacity_and_remainder_abandons() -> None:
    net = _network()
    net.routes[0].segment_travel_min = [5.0, 5.0, 5.0]
    net.vehicles[0].capacity = 4
    plan = Plan(
        plan_type="baseline",
        assignments=[
            TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60)
        ],
    )
    demand = _demand(
        PassengerDemand(
            demand_id="D1", origin_stop_id="S1", destination_stop_id="S4",
            arrival_time_min=58, passenger_count=6, max_wait_min=10,
        )
    )
    result = simulate(net, plan, Scenario(scenario_id="normal"), demand=demand)

    assert result.metrics.served_passengers == 4
    assert result.metrics.abandoned_passengers == 2
    assert result.metrics.unserved_passengers == 2
    assert result.metrics.capacity_violations == 0


def test_passengers_abandon_after_max_wait() -> None:
    net = _network()
    plan = _plan()
    demand = _demand(
        PassengerDemand(
            demand_id="D1", origin_stop_id="S1", destination_stop_id="S4",
            arrival_time_min=200, passenger_count=3, max_wait_min=5,
        )
    )
    result = simulate(net, plan, Scenario(scenario_id="normal", evaluation_horizon_min=300), demand=demand)
    assert result.metrics.abandoned_passengers == 3
    assert result.metrics.served_passengers == 0


def test_breakdown_strands_passengers_and_cancels_trip() -> None:
    net, plan = _network(), _plan()
    demand = _demand(
        PassengerDemand(
            demand_id="D1", origin_stop_id="S1", destination_stop_id="S4",
            arrival_time_min=58, passenger_count=5,
        )
    )
    result = simulate(
        net, plan, Scenario(scenario_id="normal"), demand=demand,
        breakdowns=[("V1", 63)],
    )

    assert result.metrics.breakdown_count == 1
    assert result.metrics.passengers_affected_by_breakdowns == 5
    assert result.metrics.served_passengers == 0
                                                      
    assert any("not executed" in note for note in result.notes)
                                                                                
    departures = [h for h in result.vehicle_histories if h.event == "departure" and h.vehicle_id == "V1"]
    assert [h.trip_id for h in departures] == ["T1"]


def test_unavailable_vehicle_is_not_executed() -> None:
    net, plan = _network(), _plan()
    scenario = Scenario(scenario_id="vehicle_failure", unavailable_vehicle_ids=["V1"])
    result = simulate(net, plan, scenario, demand=[])

    assert result.feasible is False
    assert result.status == "INVALID_PLAN"
    codes = {v["code"] for v in result.validation.violations}
    assert "VEHICLE_UNAVAILABLE" in codes
    assert all(h.vehicle_id != "V1" for h in result.vehicle_histories)


def test_unknown_vehicle_is_reported_not_repaired() -> None:
    net = _network()
    plan = Plan(
        plan_type="optimized",
        assignments=[
            TripAssignment(trip_id="T1", route_id="R1", vehicle_id="VX", departure_min=60)
        ],
    )
    result = simulate(net, plan, Scenario(scenario_id="normal"), demand=[])
    assert result.feasible is False
    codes = {v["code"] for v in result.validation.violations}
    assert "UNKNOWN_VEHICLE" in codes
    assert result.metrics.vehicle_departures == 0


def test_travel_time_multiplier_delays_arrivals() -> None:
    net = _network()
    plan = Plan(
        plan_type="baseline",
        assignments=[
            TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60)
        ],
    )
    demand = _demand(
        PassengerDemand(
            demand_id="D1", origin_stop_id="S1", destination_stop_id="S4",
            arrival_time_min=58, passenger_count=2,
        )
    )
    base = simulate(net, plan, Scenario(scenario_id="normal"), demand=demand)
    slow = simulate(
        net, plan,
        Scenario(scenario_id="traffic_delay", travel_time_multipliers={"R1": 2.0}),
        demand=demand,
    )

    def last_arrival(result):
        arrivals = [h.time_min for h in result.vehicle_histories if h.event == "arrival"]
        return max(arrivals)

    assert last_arrival(slow) > last_arrival(base)


def test_simulation_is_deterministic() -> None:
    net, plan = _network(), _plan()
    demand = _demand(
        PassengerDemand(
            demand_id="D1", origin_stop_id="S1", destination_stop_id="S4",
            arrival_time_min=58, passenger_count=5,
        ),
        PassengerDemand(
            demand_id="D2", origin_stop_id="S2", destination_stop_id="S3",
            arrival_time_min=66, passenger_count=4,
        ),
    )
    first = simulate(net, plan, Scenario(scenario_id="normal"), demand=demand, seed=7)
    second = simulate(net, plan, Scenario(scenario_id="normal"), demand=demand, seed=7)
    assert first.model_dump() == second.model_dump()
