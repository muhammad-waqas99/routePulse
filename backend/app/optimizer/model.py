"""Shared domain model for the RoutePulse recovery optimizer.

Everything in this module is deterministic. Travel times are derived from
great-circle (haversine) distances between stop coordinates and an assumed
average speed, because the sample data does not contain measured road times.

Modelling assumptions (documented, not hidden):
  * All trips run inbound along the route's declared stop order and terminate
    at the last stop of the route (the campus main gate, S01).
  * Passengers at a stop all travel to the terminal, so onboard load after a
    stop equals the cumulative boardings up to and including that stop. The
    binding capacity constraint is therefore the cumulative load.
  * Demand recorded directly at a terminal stop is treated as outbound demand
    and is not served by the inbound recovery plan.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.schemas.network import NetworkData
from app.schemas.scenario import Scenario

# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #


def parse_time(value: str) -> int:
    """Parse an ``HH:MM`` string into minutes since midnight."""

    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def format_time(total_minutes: int) -> str:
    """Format minutes since midnight as ``HH:MM`` (values wrap over 24h)."""

    total_minutes = int(round(total_minutes))
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def parse_period(period: str) -> tuple[int, int]:
    """Parse an ``HH:MM-HH:MM`` period into (start, end) minutes.

    The en dash character is also accepted so the frontend's display strings
    can be reused directly.
    """

    normalized = period.replace("\u2013", "-").replace("\u2014", "-")
    start, end = normalized.split("-")
    return parse_time(start.strip()), parse_time(end.strip())


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #

_EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates in kilometres."""

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


# --------------------------------------------------------------------------- #
# Domain objects
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RouteModel:
    """Pre-computed geometry for a route."""

    id: str
    name: str
    stop_ids: list[str]
    offsets_min: list[float]  # arrival offset from departure at each stop
    duration_min: float
    distance_km: float

    @property
    def terminal_stop_id(self) -> str:
        return self.stop_ids[-1]

    def offset_for(self, stop_id: str) -> float:
        return self.offsets_min[self.stop_ids.index(stop_id)]


@dataclass(frozen=True)
class VehicleModel:
    id: str
    capacity: int
    status: str


@dataclass
class DemandBatch:
    stop_id: str
    route_id: str
    time_min: int
    count: int


@dataclass
class PlannedTrip:
    """A single dispatched trip.

    ``boardings`` records the planned number of passengers picked up at each
    stop. It is used by the independent validator (capacity check) and is not
    trusted blindly by the simulation, which re-boards passengers itself.
    """

    trip_id: str
    route_id: str
    vehicle_id: str
    departure_min: int
    boardings: dict[str, int] = field(default_factory=dict)

    @property
    def total_boarded(self) -> int:
        return sum(self.boardings.values())


@dataclass
class Plan:
    plan_id: str
    label: str
    trips: list[PlannedTrip]


class NetworkModel:
    """Convenience wrapper around the raw seed network."""

    def __init__(self, network: NetworkData, avg_speed_kmh: float = 20.0) -> None:
        self.raw = network
        self.stops = {stop.id: stop for stop in network.stops}
        self.vehicles = {
            vehicle.id: VehicleModel(
                id=vehicle.id, capacity=vehicle.capacity, status=vehicle.status
            )
            for vehicle in network.vehicles
        }
        self.parameters = network.parameters
        self.avg_speed_kmh = avg_speed_kmh or network.parameters.avgSpeedKmh

        self.routes: dict[str, RouteModel] = {
            route.id: self._build_route(route.id, route.stopIds, route.name)
            for route in network.routes
        }

        # Map every non-terminal stop to the route that serves it.
        self.stop_to_route: dict[str, str] = {}
        for route_model in self.routes.values():
            for stop_id in route_model.stop_ids[:-1]:
                self.stop_to_route.setdefault(stop_id, route_model.id)

        self.terminal_stop_ids = {
            route.terminal_stop_id for route in self.routes.values()
        }

    def _build_route(
        self, route_id: str, stop_ids: list[str], name: str
    ) -> RouteModel:
        dwell = self.parameters.dwellMin
        offsets = [0.0]
        distance = 0.0

        for index in range(len(stop_ids) - 1):
            start = self.stops[stop_ids[index]]
            end = self.stops[stop_ids[index + 1]]
            segment_km = haversine_km(
                start.latitude, start.longitude, end.latitude, end.longitude
            )
            distance += segment_km
            travel_min = segment_km / self.avg_speed_kmh * 60.0
            offsets.append(offsets[-1] + travel_min + dwell)

        return RouteModel(
            id=route_id,
            name=name,
            stop_ids=list(stop_ids),
            offsets_min=offsets,
            duration_min=offsets[-1],
            distance_km=distance,
        )

    def vehicle(self, vehicle_id: str) -> VehicleModel:
        return self.vehicles[vehicle_id]

    def route(self, route_id: str) -> RouteModel:
        return self.routes[route_id]


# --------------------------------------------------------------------------- #
# Fleet + demand construction
# --------------------------------------------------------------------------- #


def select_fleet(
    network: NetworkModel, scenario: Scenario
) -> list[VehicleModel]:
    """Return the deterministic planning fleet for a scenario.

    Eligibility: vehicles that are not marked ``unavailable`` in the seed data
    and not explicitly disabled by the scenario. The highest-capacity vehicles
    are preferred, ties broken by id, then truncated to the scenario's
    ``availableVehicles`` count.
    """

    unavailable = set(scenario.unavailableVehicleIds)
    eligible = [
        vehicle
        for vehicle in network.vehicles.values()
        if vehicle.status != "unavailable" and vehicle.id not in unavailable
    ]
    eligible.sort(key=lambda v: (-v.capacity, v.id))
    return eligible[: scenario.availableVehicles]


def build_demand(network: NetworkModel, scenario: Scenario) -> list[DemandBatch]:
    """Expand seed demand into batches, applying the scenario multiplier.

    Terminal stops are skipped (outbound demand is out of scope for the
    inbound recovery plan).
    """

    multiplier = 1.0 + scenario.demandMultiplierPercent / 100.0
    batches: list[DemandBatch] = []

    for record in network.raw.demand:
        if record.stopId in network.terminal_stop_ids:
            continue
        route_id = network.stop_to_route.get(record.stopId)
        if route_id is None:
            continue
        count = int(round(record.passengerCount * multiplier))
        if count <= 0:
            continue
        batches.append(
            DemandBatch(
                stop_id=record.stopId,
                route_id=route_id,
                time_min=parse_time(record.time),
                count=count,
            )
        )

    batches.sort(key=lambda b: (b.time_min, b.route_id, b.stop_id))
    return batches
