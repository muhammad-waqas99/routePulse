"""Stop urgency scoring (rank by unmet need, not demand alone)."""
from __future__ import annotations

                                                                
DEFAULT_WEIGHTS = {"queue": 1.0, "shortfall": 2.0, "risk": 1.0, "urgency": 1.0}


def urgency(
    queue: int,
    shortfall: float,
    risk: float,
    waiting_urgency: float = 0.0,
    weights: dict | None = None,
) -> float:
    """Compute priority from queue, shortfall, risk, and waiting age."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    return (
        w["queue"] * queue
        + w["shortfall"] * shortfall
        + w["risk"] * risk
        + w["urgency"] * waiting_urgency
    )
