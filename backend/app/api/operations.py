"""Reference operations overview assembled from the configured data files.

This is a synthetic/configured snapshot, not a live telemetry feed. ETA and
alert fields are returned as empty lists until those data sources exist.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app.api import deps
from app.optimizer.fallback import fallback_plan
from app.schemas.scenario import Scenario
from app.validation.constraints import validate_plan

router = APIRouter(prefix="/api/v1", tags=["operations"])


def _clock(minutes: int) -> str:
    return f"{(minutes // 60) % 24:02d}:{minutes % 60:02d}"


@router.get("/operations/overview")
def get_operations_overview() -> dict:
    """Return canonical network, schedule, sample bus state and OD demand.

    The camelCase payload is a frontend view model. It is derived from the
    canonical Pydantic records and explicitly labels synthetic snapshot data.
    """
    try:
        network = deps.load_network()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    bus_status_path = deps.DATA_DIR / "bus_status.json"
    try:
        if bus_status_path.exists():
            with open(bus_status_path, encoding="utf-8-sig") as handle:
                bus_status = json.load(handle)
        else:
            bus_status = []
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="invalid bus_status.json") from exc

    routes = [
        {
            "id": route.route_id,
            "name": route.route_id,
            "stopIds": route.stop_ids,
            "status": "active" if any(t.route_id == route.route_id for t in network.trips) else "inactive",
        }
        for route in network.routes
    ]
    stops = [
        {"id": stop.stop_id, "name": stop.name, "latitude": stop.lat, "longitude": stop.lon}
        for stop in network.stops
    ]

    status_by_vehicle = {str(item.get("bus_id")): item for item in bus_status if isinstance(item, dict)}
    vehicles = []
    for vehicle in network.vehicles:
        snapshot = status_by_vehicle.get(vehicle.vehicle_id, {})
        current_stop = snapshot.get("current_stop_id", vehicle.initial_stop_id)
        available = bool(snapshot.get("available", True))
        assigned_trip = next((trip for trip in network.trips if trip.vehicle_id == vehicle.vehicle_id), None)
        vehicles.append({
            "id": vehicle.vehicle_id,
            "capacity": vehicle.capacity,
            "status": "available" if available else "unavailable",
            "currentStopId": current_stop,
            "routeId": assigned_trip.route_id if assigned_trip else None,
        })

    trips = [
        {
            "id": trip.trip_id,
            "routeId": trip.route_id,
            "vehicleId": trip.vehicle_id,
            "departureTime": _clock(trip.planned_departure_min),
            "status": "scheduled",
        }
        for trip in network.trips
    ]

    demand_groups = deps.load_demand()
    demand_records: dict[tuple[str, int], int] = {}
    for group in demand_groups or []:
        key = (group.origin_stop_id, group.arrival_time_min)
        demand_records[key] = demand_records.get(key, 0) + group.passenger_count
    demand = [
        {"stopId": stop_id, "time": _clock(minutes), "passengerCount": count}
        for (stop_id, minutes), count in sorted(demand_records.items())
    ]

    alerts = []
    for vehicle_id, item in status_by_vehicle.items():
        if not bool(item.get("available", True)):
            alerts.append({
                "id": f"vehicle-unavailable-{vehicle_id}",
                "title": "Vehicle unavailable",
                "description": f"{vehicle_id} is marked unavailable in the configured bus status snapshot.",
                "severity": "critical",
                "status": "active",
                "vehicleId": vehicle_id,
            })

    if demand_groups is not None:
        normal_scenario = Scenario(scenario_id="normal")
        baseline_plan = fallback_plan(network, normal_scenario)
        load_report = validate_plan(network, baseline_plan, normal_scenario, demand=demand_groups)
        capacity_alerts: dict[str, dict] = {}
        for violation in load_report["violations"]:
            if violation.get("code") != "CAPACITY_EXCEEDED":
                continue
            trip_id = str(violation.get("trip_id", "unknown"))
            alert = capacity_alerts.get(trip_id)
            actual_load = int(violation.get("actual_load", 0))
            if alert is None or actual_load > alert["actual_load"]:
                route_id = str(violation.get("route_id", "unknown"))
                vehicle_id = str(violation.get("vehicle_id", "unknown"))
                capacity_alerts[trip_id] = {
                    "id": f"capacity-{trip_id}",
                    "title": "Passenger load exceeds bus capacity",
                    "description": f"{trip_id} on {route_id} has an estimated {actual_load} passengers against {int(violation.get('capacity', 0))} seats.",
                    "severity": "warning",
                    "status": "active",
                    "routeId": route_id,
                    "vehicleId": vehicle_id,
                    "actual_load": actual_load,
                }
        alerts.extend({key: value for key, value in alert.items() if key != "actual_load"} for alert in capacity_alerts.values())
    else:
        alerts.append({
            "id": "demand-data-unavailable",
            "title": "Passenger load checks unavailable",
            "description": "The demand dataset could not be loaded, so bus-capacity alerts were not evaluated.",
            "severity": "warning",
            "status": "active",
        })

    return {
        "routes": routes,
        "stops": stops,
        "vehicles": vehicles,
        "trips": trips,
        "demand": demand,
        "etas": [],
        "alerts": alerts,
        "dataSource": "synthetic snapshot",
        "notes": ["Vehicle positions and demand are configured sample data, not live telemetry.", "Live ETA telemetry is unavailable; arrival times use timetable estimates."],
    }
