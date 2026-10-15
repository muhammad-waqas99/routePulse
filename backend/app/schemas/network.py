"""Network / operations schemas.

These mirror the TypeScript interfaces the frontend already consumes
(`src/types/operations.ts`) so the JSON contract is identical.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RouteStatus = Literal["active", "delayed", "disrupted", "inactive"]
VehicleStatus = Literal["available", "in-service", "unavailable"]
TripStatus = Literal["scheduled", "in-progress", "completed", "cancelled"]
AlertSeverity = Literal["info", "warning", "critical"]
AlertStatus = Literal["active", "resolved"]


class Stop(BaseModel):
    id: str
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Route(BaseModel):
    id: str
    name: str
    stopIds: list[str]
    status: RouteStatus


class Vehicle(BaseModel):
    id: str
    capacity: int = Field(gt=0)
    status: VehicleStatus
    currentStopId: str | None = None
    routeId: str | None = None


class Trip(BaseModel):
    id: str
    routeId: str
    vehicleId: str
    departureTime: str
    status: TripStatus


class DemandRecord(BaseModel):
    stopId: str
    time: str
    passengerCount: int = Field(ge=0)


class EtaRecord(BaseModel):
    tripId: str
    stopId: str
    scheduledArrival: str
    estimatedArrival: str


class TransportAlert(BaseModel):
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    routeId: str | None = None
    vehicleId: str | None = None


class NetworkParameters(BaseModel):
    """Operational assumptions used by travel-time and simulation models."""

    avgSpeedKmh: float = 20.0
    dwellMin: float = 1.0
    turnaroundMin: float = 5.0
    transferBufferMin: float = 3.0
    horizonStart: str = "08:00"
    horizonEnd: str = "10:00"
    intervalMin: int = 5


class NetworkData(BaseModel):
    """Full seed network loaded from `data/network.json`."""

    stops: list[Stop]
    routes: list[Route]
    vehicles: list[Vehicle]
    trips: list[Trip]
    demand: list[DemandRecord]
    alerts: list[TransportAlert]
    parameters: NetworkParameters = NetworkParameters()


class OperationsData(BaseModel):
    """Payload returned by the operations overview endpoint."""

    routes: list[Route]
    stops: list[Stop]
    vehicles: list[Vehicle]
    trips: list[Trip]
    demand: list[DemandRecord]
    etas: list[EtaRecord]
    alerts: list[TransportAlert]
