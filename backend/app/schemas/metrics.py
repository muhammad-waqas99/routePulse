"""Result and audit-record schemas.

These capture the metrics and independent validation report produced after a
simulation run.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Metrics(BaseModel):
    """Outcome metrics from a simulation run.

    The first six fields are the base simulator metrics.
    ``eta_mae_min`` is ``None`` when no ETA predictions were supplied (see
    ``eta_observations``); predictions are never fabricated just to populate it.
    The remaining fields are simulator extensions with defaults so existing
    callers keep working.
    """

    eta_mae_min: float | None = None
    avg_wait_min: float = 0.0
    unserved_passengers: int = 0
    missed_connections: int = 0
    capacity_violations: int = 0
    vehicle_km: float = 0.0

                                                                            
    served_passengers: int = 0
    abandoned_passengers: int = 0
    total_demand: int = 0
    completed_journeys: int = 0
    median_wait_min: float = 0.0
    max_wait_min: float = 0.0
    passengers_affected_by_breakdowns: int = 0
    breakdown_count: int = 0
    vehicle_departures: int = 0
    vehicle_arrivals: int = 0
    operating_cost: float = 0.0
    cost_available: bool = True
    max_segment_load: int = 0
    eta_observations: int = 0


class ValidationReport(BaseModel):
    """Independent validation result.

    ``feasible`` is true only when there are no hard violations *and* no
    required hard constraint was left unverified. Hard constraints that could
    not be checked (e.g. capacity without a passenger allocation) are listed in
    ``unverified_constraints`` so a schedule is never reported as fully feasible
    on the strength of a check that never ran.
    """

    feasible: bool
    hard_violation_count: int
    violations: list[dict] = Field(default_factory=list)
    unverified_constraints: list[dict] = Field(default_factory=list)


class RunResult(BaseModel):
    run_id: str
    scenario_id: str
    plan_type: str                            
    seed: int
    metrics: Metrics
    validation: ValidationReport
