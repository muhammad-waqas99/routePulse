"""Tests for the independent feasibility validator.

Every test asserts concrete violation codes, entity IDs, values, and
feasibility status. Where capacity is checked, an explicit passenger
allocation (``demand``) is supplied so the segment-load constraint is verified
rather than reported unverified.
"""
from __future__ import annotations

import json

from app.optimizer.fallback import fallback_plan
from app.optimizer.solve import optimize
from app.schemas.network import Network, Route, Stop, Trip, Vehicle
from app.schemas.plan import Plan, TripAssignment
from app.schemas.scenario import PassengerDemand, Scenario
from app.validation.constraints import validate_plan


def _network(
    *,
    allowed_types: list[str] | None = None,
    min_headway: int = 5,
    max_headway: int = 120,
    capacity: int = 30,
    available_until: int = 720,
    turnaround: int = 4,
    vehicles: list[str] | None = None,
) -> Network:
    stops = [Stop(stop_id=f"S{i}", name=f"Stop {i}", lat=0.0, lon=0.0) for i in range(1, 5)]
    route = Route(
        route_id="R1",
        stop_ids=["S1", "S2", "S3", "S4"],
        segment_travel_min=[5.0, 5.0, 5.0],
        segment_distance_km=[1.0, 1.0, 1.0],
        allowed_vehicle_types=allowed_types or ["shuttle"],
        min_headway_min=min_headway,
        max_headway_min=max_headway,
    )
    vehicle_ids = vehicles or ["V1"]
    veh = [
        Vehicle(
            vehicle_id=vid,
            capacity=capacity,
            vehicle_type="shuttle",
            available_from_min=0,
            available_until_min=available_until,
            initial_stop_id="S1",
            turnaround_min=turnaround,
        )
        for vid in vehicle_ids
    ]
    return Network(stops=stops, routes=[route], vehicles=veh, trips=[])


def _trip(trip_id: str, dep: int, window: tuple[int, int] = (55, 65), vehicle: str = "V1", route: str = "R1") -> Trip:
    return Trip(
        trip_id=trip_id,
        route_id=route,
        vehicle_id=vehicle,
        planned_departure_min=dep,
        departure_window_start_min=window[0],
        departure_window_end_min=window[1],
    )


def _codes(report: dict) -> list[str]:
    return [v["code"] for v in report["violations"]]


                                                                               
                 
                                                                               
def test_valid_schedule_is_feasible() -> None:
    net = _network()
    net.trips = [_trip("T1", 60)]
    plan = Plan(
        plan_type="baseline",
        assignments=[TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60)],
    )
    demand = [PassengerDemand(
        demand_id="D1", origin_stop_id="S1", destination_stop_id="S2",
        arrival_time_min=55, passenger_count=10,
    )]
    report = validate_plan(net, plan, Scenario(scenario_id="normal"), demand=demand)

    assert report["feasible"] is True
    assert report["hard_violation_count"] == 0
    assert report["violations"] == []
    assert report["unverified_constraints"] == []


                                                                               
                                       
                                                                               
def test_unassigned_trip_and_invalid_references() -> None:
    net = _network(vehicles=["V1", "V2"])
    net.trips = [_trip("T1", 60), _trip("T2", 120, window=(115, 125), vehicle="V2")]
    plan = Plan(
        plan_type="optimized",
        assignments=[
            TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
                                                
            TripAssignment(trip_id="TX", route_id="R1", vehicle_id="V1", departure_min=200),
            TripAssignment(trip_id="T1", route_id="RX", vehicle_id="V1", departure_min=60),
            TripAssignment(trip_id="T1", route_id="R1", vehicle_id="VX", departure_min=60),
        ],
    )
    report = validate_plan(net, plan, demand=[])
    codes = set(_codes(report))
    assert "UNASSIGNED_TRIP" in codes
    assert "UNKNOWN_TRIP" in codes
    assert "UNKNOWN_ROUTE" in codes
    assert "UNKNOWN_VEHICLE" in codes
    assert "DUPLICATE_ASSIGNMENT" in codes
    assert report["feasible"] is False

    unassigned = next(v for v in report["violations"] if v["code"] == "UNASSIGNED_TRIP")
    assert unassigned["trip_id"] == "T2"
    assert unassigned["planned_vehicle_id"] == "V2"


                                                                               
                            
                                                                               
def test_vehicle_type_incompatible() -> None:
    net = _network(allowed_types=["shuttle"])
    net.vehicles[0].vehicle_type = "van"
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    report = validate_plan(net, plan, demand=[])
    violation = next(v for v in report["violations"] if v["code"] == "VEHICLE_TYPE_INCOMPATIBLE")
    assert violation["vehicle_type"] == "van"
    assert violation["allowed_vehicle_types"] == ["shuttle"]


                                                                               
                      
                                                                               
def test_vehicle_unavailable_in_scenario() -> None:
    net = _network()
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    scenario = Scenario(scenario_id="vehicle_failure", unavailable_vehicle_ids=["V1"])
    report = validate_plan(net, plan, scenario, demand=[])
    assert "VEHICLE_UNAVAILABLE" in _codes(report)


def test_vehicle_availability_window() -> None:
    net = _network(available_until=65)
    net.trips = [_trip("T1", 60)]                                         
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    report = validate_plan(net, plan, demand=[])
    violation = next(v for v in report["violations"] if v["code"] == "VEHICLE_AVAILABILITY")
    assert violation["available_until_min"] == 65
    assert violation["arrival_min"] == 75


                                                                               
                   
                                                                               
def test_departure_window_violation() -> None:
    net = _network()
    net.trips = [_trip("T1", 60, window=(55, 65))]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=70),
    ])
    report = validate_plan(net, plan, demand=[])
    violation = next(v for v in report["violations"] if v["code"] == "DEPARTURE_WINDOW")
    assert violation["departure_min"] == 70
    assert violation["window_start_min"] == 55
    assert violation["window_end_min"] == 65


def test_departure_window_boundaries_are_inclusive() -> None:
    net = _network()
    net.trips = [_trip("T1", 55, window=(55, 65))]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=55),
    ])
    report = validate_plan(net, plan, demand=[])
    assert "DEPARTURE_WINDOW" not in _codes(report)


                                                                               
                        
                                                                               
def test_overlap_and_insufficient_turnaround() -> None:
    net = _network(vehicles=["V1", "V2"], turnaround=4, min_headway=0)
    net.trips = [
                                                                                
        _trip("T1", 60, window=(55, 65), vehicle="V1"),
        _trip("T2", 77, window=(75, 85), vehicle="V1"),
                                                     
        _trip("T3", 60, window=(55, 65), vehicle="V2"),
        _trip("T4", 70, window=(65, 75), vehicle="V2"),
    ]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
        TripAssignment(trip_id="T2", route_id="R1", vehicle_id="V1", departure_min=77),
        TripAssignment(trip_id="T3", route_id="R1", vehicle_id="V2", departure_min=60),
        TripAssignment(trip_id="T4", route_id="R1", vehicle_id="V2", departure_min=70),
    ])
    report = validate_plan(net, plan, demand=[])
    codes = _codes(report)
    assert "VEHICLE_OVERLAP" in codes
    assert "INSUFFICIENT_TURNAROUND" in codes


def test_initial_stop_mismatch() -> None:
    net = _network()
    net.vehicles[0].initial_stop_id = "S4"                         
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    report = validate_plan(net, plan, demand=[])
    violation = next(v for v in report["violations"] if v["code"] == "INITIAL_STOP_MISMATCH")
    assert violation["initial_stop_id"] == "S4"
    assert violation["route_start_stop_id"] == "S1"


                                                                               
                                                     
                                                                               
def test_intermediate_segment_capacity_exceeded() -> None:
    net = _network(capacity=30)
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="baseline", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    demand = [
        PassengerDemand(demand_id="D1", origin_stop_id="S1", destination_stop_id="S3",
                        arrival_time_min=55, passenger_count=20),
        PassengerDemand(demand_id="D2", origin_stop_id="S2", destination_stop_id="S4",
                        arrival_time_min=55, passenger_count=20),
    ]
    report = validate_plan(net, plan, demand=demand)
    violation = next(v for v in report["violations"] if v["code"] == "CAPACITY_EXCEEDED")
    assert violation["trip_id"] == "T1"
    assert violation["vehicle_id"] == "V1"
    assert violation["segment_index"] == 1
    assert violation["actual_load"] == 40
    assert violation["capacity"] == 30


def test_capacity_shortfall_is_resolved_by_later_service_within_wait_limit() -> None:
    net = _network(capacity=30, vehicles=["V1", "V2"])
    net.trips = [
        _trip("T1", 60, vehicle="V1"),
        _trip("T2", 75, window=(70, 80), vehicle="V2"),
    ]
    plan = Plan(plan_type="baseline", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
        TripAssignment(trip_id="T2", route_id="R1", vehicle_id="V2", departure_min=75),
    ])
    demand = [
        PassengerDemand(demand_id="D1", origin_stop_id="S1", destination_stop_id="S3",
                        arrival_time_min=55, passenger_count=20),
        PassengerDemand(demand_id="D2", origin_stop_id="S2", destination_stop_id="S4",
                        arrival_time_min=55, passenger_count=20),
    ]

    report = validate_plan(net, plan, demand=demand)

    assert "CAPACITY_EXCEEDED" not in _codes(report)


def test_boarding_and_alighting_keeps_load_within_capacity() -> None:
    net = _network(capacity=30)
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="baseline", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
                                                                        
    demand = [
        PassengerDemand(demand_id="D1", origin_stop_id="S1", destination_stop_id="S2",
                        arrival_time_min=55, passenger_count=25),
        PassengerDemand(demand_id="D2", origin_stop_id="S2", destination_stop_id="S3",
                        arrival_time_min=55, passenger_count=25),
    ]
    report = validate_plan(net, plan, demand=demand)
    assert "CAPACITY_EXCEEDED" not in _codes(report)


                                                                               
           
                                                                               
def test_missed_connection_buffer_violation() -> None:
    net = _network(vehicles=["V1", "V2"])
    net.routes.append(Route(
        route_id="R2",
        stop_ids=["S2", "S1"],
        segment_travel_min=[5.0],
        segment_distance_km=[1.0],
        min_headway_min=5,
        max_headway_min=200,
    ))
    net.trips = [
        _trip("T1", 60, window=(55, 65), vehicle="V1"),                    
        _trip("T2", 72, window=(70, 80), vehicle="V2", route="R2"),
    ]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
        TripAssignment(trip_id="T2", route_id="R2", vehicle_id="V2", departure_min=72),
    ])
    connections = [{"from_trip_id": "T1", "to_trip_id": "T2", "buffer_min": 5}]
    report = validate_plan(net, plan, demand=[], connections=connections)
    violation = next(v for v in report["violations"] if v["code"] == "MISSED_CONNECTION")
    assert violation["arrival_min"] == 75
    assert violation["departure_min"] == 72
    assert violation["buffer_min"] == 5


def test_connection_without_buffer_is_unverified() -> None:
    net = _network()
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    report = validate_plan(
        net, plan, demand=[],
        connections=[{"from_trip_id": "T1", "to_trip_id": "T1"}],
    )
    assert any(u["code"] == "TRANSFER_UNVERIFIED" for u in report["unverified_constraints"])
    assert report["feasible"] is False


                                                                               
                       
                                                                               
def test_headway_violations_and_route_coverage() -> None:
    net = _network(vehicles=["V1", "V2"], min_headway=10, max_headway=30)
    net.routes.append(Route(
        route_id="R2",
        stop_ids=["S1", "S2"],
        segment_travel_min=[5.0],
        segment_distance_km=[1.0],
        min_headway_min=10,
        max_headway_min=30,
    ))
    net.trips = [
        _trip("T1", 60, window=(55, 65), vehicle="V1"),
        _trip("T2", 100, window=(95, 105), vehicle="V2"),                           
        _trip("T3", 110, window=(105, 115), vehicle="V1"),                            
        _trip("T4", 115, window=(110, 120), vehicle="V2"),                           
        Trip(trip_id="T5", route_id="R2", vehicle_id="V2",
             planned_departure_min=60, departure_window_start_min=55, departure_window_end_min=65),
    ]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
        TripAssignment(trip_id="T2", route_id="R1", vehicle_id="V2", departure_min=100),
        TripAssignment(trip_id="T3", route_id="R1", vehicle_id="V1", departure_min=110),
        TripAssignment(trip_id="T4", route_id="R1", vehicle_id="V2", departure_min=115),
                                                             
    ])
    report = validate_plan(net, plan, demand=[])
    codes = set(_codes(report))
    assert "HEADWAY_EXCEEDED" in codes
    assert "HEADWAY_TOO_SHORT" in codes
    assert "ROUTE_UNCOVERED" in codes


                                                                               
                                            
                                                                               
def test_capacity_unverified_without_demand() -> None:
    net = _network()
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="baseline", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    report = validate_plan(net, plan)
    assert report["hard_violation_count"] == 0
    assert any(u["code"] == "CAPACITY_UNVERIFIED" for u in report["unverified_constraints"])
    assert report["feasible"] is False                                                         


                                                                               
                                     
                                                                               
def test_multiple_violations_in_one_report() -> None:
    net = _network(available_until=65)
    net.trips = [_trip("T1", 60), _trip("T2", 120, window=(115, 125))]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=70),
                       
    ])
    report = validate_plan(net, plan, demand=[])
    codes = set(_codes(report))
    assert {"DEPARTURE_WINDOW", "UNASSIGNED_TRIP", "VEHICLE_AVAILABILITY"} <= codes
    assert report["hard_violation_count"] >= 3


def test_report_is_deterministic() -> None:
    net = _network(available_until=65)
    net.trips = [_trip("T1", 60), _trip("T2", 120, window=(115, 125))]
    plan = Plan(plan_type="optimized", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=70),
    ])
    first = validate_plan(net, plan, demand=[])
    second = validate_plan(net, plan, demand=[])
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_inputs_are_not_mutated() -> None:
    net = _network()
    net.trips = [_trip("T1", 60)]
    plan = Plan(plan_type="baseline", assignments=[
        TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=60),
    ])
    before = (net.model_dump(), plan.model_dump())
    validate_plan(net, plan, Scenario(scenario_id="normal"), demand=[])
    after = (net.model_dump(), plan.model_dump())
    assert before == after


                                                                               
                                             
                                                                               
def test_optimizer_status_does_not_bypass_validation() -> None:
    net = _network(available_until=65)
    net.trips = [_trip("T1", 60)]
    plan = Plan(
        plan_type="optimized",
        solver_status="OK",                            
        assignments=[TripAssignment(trip_id="T1", route_id="R1", vehicle_id="V1", departure_min=70)],
    )
    report = validate_plan(net, plan, demand=[])
    assert report["feasible"] is False
    assert report["hard_violation_count"] >= 1


                                                                               
                              
                                                                               
def _assign_network() -> Network:
    net = _network(vehicles=["V1", "V2", "V3"], max_headway=200)
    net.trips = [
        _trip("T1", 60, window=(55, 65), vehicle="V1"),
        _trip("T2", 120, window=(115, 125), vehicle="V2"),
    ]
    return net


def test_baseline_reports_preexisting_violation() -> None:
    net = _assign_network()
    scenario = Scenario(scenario_id="vehicle_failure", unavailable_vehicle_ids=["V2"])
    baseline = fallback_plan(net, scenario)
    report = validate_plan(net, baseline, scenario, demand=[])
    assert report["feasible"] is False
    assert "UNASSIGNED_TRIP" in _codes(report)


def test_optimized_plan_validates() -> None:
    net = _assign_network()
    scenario = Scenario(scenario_id="vehicle_failure", unavailable_vehicle_ids=["V2"])
    candidate = optimize(net, scenario)
    report = validate_plan(net, candidate, scenario, demand=[])
    assert report["feasible"] is True
    assert candidate.unassigned_trip_ids == []
