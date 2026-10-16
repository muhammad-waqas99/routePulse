"""Overload / crowding risk (decision support).

Compares predicted demand against available capacity to flag likely
shortfalls:

    Shortfall = max(0, expected_demand - capacity)

The prediction engine *flags* the situation; the optimizer decides whether an
extra bus is feasible and which bus should serve the stop.
"""
from __future__ import annotations

from dataclasses import dataclass

LOW = "LOW"
MEDIUM = "MEDIUM"
HIGH = "HIGH"


@dataclass
class RiskAssessment:
    stop_id: str
    time_bucket_min: int
    expected_demand: float
    available_capacity: int
    capacity_shortfall: float
    crowding_risk: str                       
    recommended_action: str


def capacity_shortfall(expected_demand: float, capacity: int) -> float:
    return max(0.0, expected_demand - capacity)


def crowding_risk(
    expected_demand: float,
    capacity: int,
    medium_threshold: float = 0.85,
) -> str:
    """Classify crowding risk from the demand-to-capacity ratio.

    Thresholds are configurable and documented, not statistical facts.
    """
    if capacity <= 0:
        return HIGH if expected_demand > 0 else LOW
    ratio = expected_demand / capacity
    if ratio > 1.0:
        return HIGH
    if ratio >= medium_threshold:
        return MEDIUM
    return LOW


def _action(risk: str) -> str:
    return {
        HIGH: "EVALUATE_EXTRA_BUS",
        MEDIUM: "MONITOR",
        LOW: "NO_ACTION",
    }[risk]


def assess_risk(
    stop_id: str,
    time_bucket_min: int,
    expected_demand: float,
    available_capacity: int,
    medium_threshold: float = 0.85,
) -> RiskAssessment:
    """Build a full risk assessment for one stop."""
    shortfall = capacity_shortfall(expected_demand, available_capacity)
    risk = crowding_risk(expected_demand, available_capacity, medium_threshold)
    return RiskAssessment(
        stop_id=stop_id,
        time_bucket_min=time_bucket_min,
        expected_demand=round(expected_demand, 2),
        available_capacity=available_capacity,
        capacity_shortfall=round(shortfall, 2),
        crowding_risk=risk,
        recommended_action=_action(risk),
    )
