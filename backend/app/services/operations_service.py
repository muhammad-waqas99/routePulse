"""Operations overview service.

Loads the seed network once and exposes the payload the dashboards consume.
ETAs are computed from the schedule (see :mod:`app.prediction.eta`) instead of
being hardcoded.
"""

from __future__ import annotations

import json
from functools import lru_cache

from app.config import settings
from app.optimizer.model import NetworkModel
from app.prediction.eta import predict_all_etas
from app.schemas.network import NetworkData, OperationsData


@lru_cache(maxsize=1)
def get_network() -> NetworkData:
    with settings.network_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    return NetworkData.model_validate(raw)


@lru_cache(maxsize=1)
def get_network_model() -> NetworkModel:
    return NetworkModel(get_network(), avg_speed_kmh=settings.avg_speed_kmh)


def get_operations_overview() -> OperationsData:
    network = get_network()
    network_model = get_network_model()

    return OperationsData(
        routes=network.routes,
        stops=network.stops,
        vehicles=network.vehicles,
        trips=network.trips,
        demand=network.demand,
        etas=predict_all_etas(network_model),
        alerts=network.alerts,
    )


def referential_integrity_errors() -> list[str]:
    """Return a list of problems found in the seed network (empty if valid).

    Used by tests and the startup self-check to guarantee the sample data is
    internally consistent before it is served.
    """

    network = get_network()
    errors: list[str] = []

    stop_ids = {stop.id for stop in network.stops}
    route_ids = {route.id for route in network.routes}
    vehicle_ids = {vehicle.id for vehicle in network.vehicles}
    trip_ids = {trip.id for trip in network.trips}

    for route in network.routes:
        if len(route.stopIds) < 2:
            errors.append(f"Route {route.id} has fewer than two stops")
        for stop_id in route.stopIds:
            if stop_id not in stop_ids:
                errors.append(f"Route {route.id} references unknown stop {stop_id}")

    for vehicle in network.vehicles:
        if vehicle.routeId and vehicle.routeId not in route_ids:
            errors.append(f"Vehicle {vehicle.id} references unknown route {vehicle.routeId}")
        if vehicle.currentStopId and vehicle.currentStopId not in stop_ids:
            errors.append(
                f"Vehicle {vehicle.id} references unknown stop {vehicle.currentStopId}"
            )

    for trip in network.trips:
        if trip.routeId not in route_ids:
            errors.append(f"Trip {trip.id} references unknown route {trip.routeId}")
        if trip.vehicleId not in vehicle_ids:
            errors.append(f"Trip {trip.id} references unknown vehicle {trip.vehicleId}")

    for record in network.demand:
        if record.stopId not in stop_ids:
            errors.append(f"Demand references unknown stop {record.stopId}")

    for alert in network.alerts:
        if alert.routeId and alert.routeId not in route_ids:
            errors.append(f"Alert {alert.id} references unknown route {alert.routeId}")
        if alert.vehicleId and alert.vehicleId not in vehicle_ids:
            errors.append(
                f"Alert {alert.id} references unknown vehicle {alert.vehicleId}"
            )

    # Referenced ids that only exist to be referenced.
    _ = trip_ids
    return errors
