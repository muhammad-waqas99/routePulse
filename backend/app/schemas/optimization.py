"""Optimization request/response schemas.

`RecoveryPlanResult` deliberately matches the frontend
`src/types/recoveryPlanner.ts` interface. The `/api/optimize` response is a
superset: every field the Recovery Planner already renders is present at the
top level, plus the richer validation/simulation detail required by the task.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OptimizationStatus = Literal["optimal", "feasible", "infeasible", "unknown"]


class TimetableTrip(BaseModel):
    tripId: str
    routeId: str
    vehicleId: str
    departureTime: str


class ConstraintCheck(BaseModel):
    id: str
    label: str
    passed: bool
    detail: str | None = None


class OptimizationMetrics(BaseModel):
    averageWaitingTimeMin: float
    unservedPassengers: int
    missedConnections: int
    vehicleDistanceKm: float


class PlanSummary(BaseModel):
    """A baseline or optimized plan in the shape the UI consumes."""

    label: str
    trips: list[TimetableTrip]
    totalTrips: int
    vehiclesUsed: list[str]
    totalDistanceKm: float


class ValidationResult(BaseModel):
    valid: bool
    hardViolationCount: int
    constraints: list[ConstraintCheck]


class SimulationSummary(BaseModel):
    label: str
    servedPassengers: int
    unservedPassengers: int
    missedConnections: int
    capacityDeniedPassengers: int
    averageWaitingTimeMin: float
    tripsCompleted: int
    tripsTotal: int
    vehicleDistanceKm: float
    totalTravelTimeMin: float
    capacityViolations: int


class MetricDifference(BaseModel):
    metric: str
    baseline: float
    optimized: float
    difference: float
    lowerIsBetter: bool
    improved: bool


class OptimizeRequest(BaseModel):
    scenarioId: str = Field(min_length=1)
    # Optional seed override for reproducible deterministic runs.
    seed: int | None = None


class OptimizeResponse(BaseModel):
    """Full optimize payload (superset of `RecoveryPlanResult`)."""

    # --- RecoveryPlanResult-compatible fields -------------------------------
    status: OptimizationStatus
    originalTrips: list[TimetableTrip]
    proposedTrips: list[TimetableTrip]
    totalTrips: int
    constraints: list[ConstraintCheck]
    hardViolationCount: int
    metrics: OptimizationMetrics

    # --- Extended detail ----------------------------------------------------
    runId: str
    scenarioId: str
    scenarioName: str
    message: str
    baselinePlan: PlanSummary
    optimizedPlan: PlanSummary
    validation: ValidationResult
    simulation: dict[str, SimulationSummary]
    baselineMetrics: OptimizationMetrics
    optimizedMetrics: OptimizationMetrics
    differences: list[MetricDifference]
    warnings: list[str] = Field(default_factory=list)
