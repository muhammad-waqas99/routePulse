"""Simulation-specific result models.

These reuse the canonical project schemas (:class:`Metrics`,
:class:`ValidationReport`) and add the audit surface the discrete-event engine
produces: an event log, per-vehicle histories, and passenger-outcome
accounting.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.metrics import Metrics, ValidationReport


class EventLogEntry(BaseModel):
    """One line of the simulation event log."""

    time_min: float
    event_type: str
    trip_id: str | None = None
    vehicle_id: str | None = None
    stop_id: str | None = None
    segment_index: int | None = None
    passengers: int | None = None
    load: int | None = None
    detail: str | None = None


class VehicleHistoryEntry(BaseModel):
    """A vehicle state transition (departure/arrival) along a trip."""

    time_min: float
    event: str                                         
    vehicle_id: str
    trip_id: str | None = None
    route_id: str | None = None
    stop_id: str | None = None
    segment_index: int | None = None
    onboard: int = 0
    load: int = 0


class PassengerOutcomeSummary(BaseModel):
    """Disaggregated passenger accounting from the simulation run."""

    total_demand: int = 0
    served: int = 0
    unserved: int = 0
    abandoned: int = 0
    stranded_onboard: int = 0
    waiting_at_horizon: int = 0
    affected_by_breakdowns: int = 0


class SimulationResult(BaseModel):
    """The complete, serialisable output of one simulation run."""

    run_id: str
    scenario_id: str
    plan_type: str
    seed: int
    start_min: int
    horizon_min: int
    status: str                         
    feasible: bool
    validation: ValidationReport
    metrics: Metrics
    passenger_outcomes: PassengerOutcomeSummary
    events: list[EventLogEntry] = Field(default_factory=list)
    vehicle_histories: list[VehicleHistoryEntry] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
