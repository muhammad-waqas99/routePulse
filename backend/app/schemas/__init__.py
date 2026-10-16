"""Shared Pydantic schemas (the canonical contract across the system)."""

from app.schemas.network import Network, Route, Stop, Trip, Vehicle
from app.schemas.scenario import (
    BusStatus,
    DemandRecord,
    GPSObservation,
    PassengerDemand,
    Scenario,
    TripObservation,
)
from app.schemas.metrics import Metrics, RunResult, ValidationReport

__all__ = [
    "Network",
    "Route",
    "Stop",
    "Trip",
    "Vehicle",
    "BusStatus",
    "DemandRecord",
    "GPSObservation",
    "PassengerDemand",
    "Scenario",
    "TripObservation",
    "Metrics",
    "RunResult",
    "ValidationReport",
]
