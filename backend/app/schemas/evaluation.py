"""Evaluation schemas.

Mirrors the frontend `src/types/performanceLab.ts` contract used by the
Performance Lab page.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

EvaluationStatus = Literal["completed", "infeasible"]
MetricUnit = Literal["min", "passengers", "percent", "km"]


class PerformanceMetric(BaseModel):
    baseline: float
    optimized: float
    unit: MetricUnit
    lowerIsBetter: bool


class PerformanceMetrics(BaseModel):
    averageWaitingTime: PerformanceMetric
    unservedPassengers: PerformanceMetric
    missedConnections: PerformanceMetric
    etaMae: PerformanceMetric
    unservedRate: PerformanceMetric
    capacityViolations: PerformanceMetric
    vehicleDistance: PerformanceMetric


class PassengerOutcome(BaseModel):
    total: int
    baselineServed: int
    baselineUnserved: int
    optimizedServed: int
    optimizedUnserved: int


class FleetUtilization(BaseModel):
    vehicleId: str
    baseline: float
    optimized: float


class EtaWithinThree(BaseModel):
    baseline: float
    optimized: float


class PerformanceRun(BaseModel):
    runId: str
    scenarioId: str
    scenarioName: str
    status: EvaluationStatus
    createdAt: str
    metrics: PerformanceMetrics | None = None
    passengerOutcome: PassengerOutcome | None = None
    fleetUtilization: list[FleetUtilization] | None = None
    etaWithinThreeMinutes: EtaWithinThree | None = None
    keyFinding: str | None = None


class PerformanceLabData(BaseModel):
    runs: list[PerformanceRun]
