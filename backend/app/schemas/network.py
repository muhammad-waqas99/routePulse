"""Network schema: stops, routes, vehicles, and scheduled trips.

These models are shared by the optimizer, simulator, validator, API, and
frontend. Related records refer to entities by ID.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Stop(BaseModel):
    """A shuttle stop where passengers board or alight."""

    stop_id: str
    name: str
    lat: float
    lon: float
                                                                                   
    zone: str | None = None


class Route(BaseModel):
    """An ordered sequence of stops with per-segment travel properties."""

    route_id: str
    stop_ids: list[str]
                                                     
    segment_travel_min: list[float]
    segment_distance_km: list[float]
    allowed_vehicle_types: list[str] = Field(default_factory=lambda: ["shuttle"])
    min_headway_min: int = 5
    max_headway_min: int = 20


class Vehicle(BaseModel):
    """A shuttle vehicle with capacity and availability window (minutes from midnight)."""

    vehicle_id: str
    capacity: int
    vehicle_type: str = "shuttle"
    available_from_min: int = 0
    available_until_min: int = 720
    initial_stop_id: str
    turnaround_min: int = 4
    cost_per_km: float = 18.0


class Trip(BaseModel):
    """A scheduled trip on a route assigned to a vehicle."""

    trip_id: str
    route_id: str
    vehicle_id: str
    planned_departure_min: int
    departure_window_start_min: int
    departure_window_end_min: int


class Network(BaseModel):
    """The full campus transport network."""

    stops: list[Stop]
    routes: list[Route]
    vehicles: list[Vehicle]
    trips: list[Trip]

    @property
    def stops_by_id(self) -> dict[str, Stop]:
        return {s.stop_id: s for s in self.stops}

    @property
    def routes_by_id(self) -> dict[str, Route]:
        return {r.route_id: r for r in self.routes}

    @property
    def vehicles_by_id(self) -> dict[str, Vehicle]:
        return {v.vehicle_id: v for v in self.vehicles}
