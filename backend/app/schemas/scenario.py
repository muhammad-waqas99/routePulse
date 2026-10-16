"""Scenario and simulation-input schema.

Includes the records the prediction engine consumes (historical demand, trip
observations, GPS observations, bus status) and the disruption scenarios that
drive experiments.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PassengerDemand(BaseModel):
    """A group of passengers arriving at an origin stop bound for a destination."""

    demand_id: str
    origin_stop_id: str
    destination_stop_id: str
    arrival_time_min: int
    passenger_count: int
    max_wait_min: int = 25
    transfer_allowed: bool = True


class DemandRecord(BaseModel):
    """A historical demand observation used to train the demand forecaster."""

    stop_id: str
    day_type: str = "WEEKDAY"                         
    time_bucket_min: int                                                     
    passengers: int


class TripObservation(BaseModel):
    """A historical segment travel-time observation used to train the ETA model."""

    route_id: str
    segment_index: int
    from_stop_id: str
    to_stop_id: str
    travel_time_sec: float


class GPSObservation(BaseModel):
    """A single GPS sample of a vehicle's position along a route."""

    vehicle_id: str
    timestamp_min: int
    lat: float
    lon: float
    route_id: str
    segment_index: int


class BusStatus(BaseModel):
    """Current state of a bus (position, capacity, availability)."""

    bus_id: str
    current_stop_id: str
    capacity: int
    available: bool
    onboard: int = 0


class Scenario(BaseModel):
    """A disruption scenario with multipliers and unavailability."""

    scenario_id: str
    seed: int = 42
    evaluation_horizon_min: int = 180
    demand_multipliers: dict[str, float] = Field(default_factory=dict)
    travel_time_multipliers: dict[str, float] = Field(default_factory=dict)
    unavailable_vehicle_ids: list[str] = Field(default_factory=list)
    vehicle_delays_min: dict[str, int] = Field(default_factory=dict)
