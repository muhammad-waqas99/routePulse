"""Tests for the vehicle-assignment optimizer and fallback."""
from __future__ import annotations

from app.optimizer.fallback import fallback_plan
from app.optimizer.solve import optimize
from app.schemas.network import Network, Route, Stop, Trip, Vehicle
from app.schemas.scenario import Scenario


def _network() -> Network:
    stops = [Stop(stop_id=f"S{i}", name=f"Stop {i}", lat=0.0, lon=0.0) for i in range(1, 4)]
    route = Route(
        route_id="R1",
        stop_ids=["S1", "S2", "S3"],
        segment_travel_min=[5.0, 5.0],
        segment_distance_km=[1.0, 1.0],
    )
    vehicles = [
        Vehicle(vehicle_id="V1", capacity=30, initial_stop_id="S1",
                available_from_min=0, available_until_min=720, turnaround_min=4),
        Vehicle(vehicle_id="V2", capacity=30, initial_stop_id="S1",
                available_from_min=0, available_until_min=720, turnaround_min=4),
        Vehicle(vehicle_id="V3", capacity=30, initial_stop_id="S1",
                available_from_min=0, available_until_min=720, turnaround_min=4),
    ]
    trips = [
        Trip(trip_id="T1", route_id="R1", vehicle_id="V1", planned_departure_min=60,
             departure_window_start_min=55, departure_window_end_min=65),
        Trip(trip_id="T2", route_id="R1", vehicle_id="V2", planned_departure_min=120,
             departure_window_start_min=115, departure_window_end_min=125),
    ]
    return Network(stops=stops, routes=[route], vehicles=vehicles, trips=trips)


def test_fallback_drops_unavailable() -> None:
    net = _network()
    sc = Scenario(scenario_id="s", unavailable_vehicle_ids=["V2"])
    plan = fallback_plan(net, sc)
    assigned = {a.trip_id for a in plan.assignments}
    assert "T1" in assigned
    assert "T2" not in assigned
    assert plan.unassigned_trip_ids == ["T2"]


def test_optimize_reassigns_unavailable_trip() -> None:
    net = _network()
    sc = Scenario(scenario_id="s", unavailable_vehicle_ids=["V2"])
    plan = optimize(net, sc)
    by_trip = {a.trip_id: a.vehicle_id for a in plan.assignments}
    assert by_trip["T1"] == "V1"
    assert by_trip["T2"] != "V2"                                          
    assert plan.unassigned_trip_ids == []
    assert plan.solver_status == "OK"


def test_optimize_partial_when_blocked() -> None:
    net = _network()
                                                                      
    net.trips[1].planned_departure_min = 62
    net.trips[1].departure_window_start_min = 60
    net.trips[1].departure_window_end_min = 64
    sc = Scenario(scenario_id="s", unavailable_vehicle_ids=["V2", "V3"])
    plan = optimize(net, sc)
    assert "T2" in plan.unassigned_trip_ids
    assert plan.solver_status == "PARTIAL"
