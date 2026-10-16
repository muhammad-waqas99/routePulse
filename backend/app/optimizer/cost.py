"""Objective function and incremental assignment cost."""
from __future__ import annotations

from dataclasses import dataclass

from app.optimizer.state import Assignment, OptimizationState, StopForecast


@dataclass
class Objective:
    """J = w_w*W + w_u*U + w_d*L + w_dst*D (waiting, unserved, delay, distance)."""

    w_wait: float = 1.0
    w_unserved: float = 20.0
    w_delay: float = 2.0
    w_distance: float = 3.0

    def total(self, waiting: float, unserved: float, delay: float, distance: float) -> float:
        return (
            self.w_wait * waiting
            + self.w_unserved * unserved
            + self.w_delay * delay
            + self.w_distance * distance
        )


def incremental_cost(
    travel_min: float,
    onboard_impact: float,
    added_distance: float,
    lambdas: dict | None = None,
) -> float:
    """Cost of assigning a bus to a stop: Cost = l1*T + l2*I + l3*dL."""
    lam = {"travel": 1.0, "impact": 2.0, "distance": 0.5, **(lambdas or {})}
    return lam["travel"] * travel_min + lam["impact"] * onboard_impact + lam["distance"] * added_distance


def plan_cost(
    state: OptimizationState,
    forecasts: dict[str, StopForecast],
    assignments: list[Assignment],
    objective: Objective,
) -> float:
    """Fast approximate cost of a complete assignment plan.

    Waiting is approximated by each bus's travel time to its target; unserved
    shortfalls are penalized. The simulator validates the chosen plan.
    """
    total = 0.0
    covered = {a.target_stop for a in assignments}
    for a in assignments:
        t = state.travel(state.buses[a.bus_id].current_stop, a.target_stop)
        total += objective.w_wait * (t or 0.0)
    for stop_id, fc in forecasts.items():
        if stop_id not in covered and fc.shortfall > 0:
            total += objective.w_unserved * fc.shortfall
    return total
