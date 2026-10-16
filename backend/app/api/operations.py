"""Reference operations overview assembled from the configured data files.

This is a synthetic/configured snapshot, not a live telemetry feed. ETA and
alert fields are returned as empty lists until those data sources exist.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app.api import deps

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

    demand_records: dict[tuple[str, int], int] = {}
    for demand in deps.load_demand() or []:
        key = (demand.origin_stop_id, demand.arrival_time_min)
        demand_records[key] = demand_records.get(key, 0) + demand.passenger_count
    demand = [
        {"stopId": stop_id, "time": _clock(minutes), "passengerCount": count}
        for (stop_id, minutes), count in sorted(demand_records.items())
    ]

    return {
        "routes": routes,
        "stops": stops,
        "vehicles": vehicles,
        "trips": trips,
        "demand": demand,
        "etas": [],
        "alerts": [],
        "dataSource": "synthetic snapshot",
        "notes": ["Vehicle positions and demand are configured sample data, not live telemetry.", "ETA predictions and operational alerts are not available."],
    }
