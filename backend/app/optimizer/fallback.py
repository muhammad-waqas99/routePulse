"""Fallback plan: the original timetable (with unavailable vehicles dropped).

Used when the optimizer is unavailable, times out, or returns an infeasible
result. A pre-existing baseline violation (e.g. an unavailable vehicle) is
reported via ``unassigned_trip_ids`` rather than silently hidden.
"""
from __future__ import annotations

from app.schemas.network import Network
from app.schemas.plan import Plan, TripAssignment
from app.schemas.scenario import Scenario


def fallback_plan(network: Network, scenario: Scenario) -> Plan:
    unavailable = set(scenario.unavailable_vehicle_ids)
    assignments: list[TripAssignment] = []
    unassigned: list[str] = []

    for trip in network.trips:
        if trip.vehicle_id in unavailable:
            unassigned.append(trip.trip_id)
            continue
        dep = trip.planned_departure_min + scenario.vehicle_delays_min.get(trip.vehicle_id, 0)
        assignments.append(TripAssignment(
            trip_id=trip.trip_id,
            route_id=trip.route_id,
            vehicle_id=trip.vehicle_id,
            departure_min=dep,
        ))

    return Plan(
        plan_type="baseline",
        assignments=assignments,
        unassigned_trip_ids=unassigned,
        solver_status="OK" if not unassigned else "PARTIAL",
    )
