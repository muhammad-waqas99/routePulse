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
    """P_s = a*Q + b*U + c*R + d*A (see Wild Bugs optimization notes)."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    return (
        w["queue"] * queue
        + w["shortfall"] * shortfall
        + w["risk"] * risk
        + w["urgency"] * waiting_urgency
    )
