"""Public entry point: rolling-horizon dispatcher.

Combines greedy dispatch with cost-based local search. Returns proposed actions
that the simulator validates and executes. Re-optimize every 5 simulated minutes
(or immediately after major events).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.optimizer.cost import Objective, plan_cost
from app.optimizer.greedy import greedy_dispatch
from app.optimizer.local_search import local_search_improve
from app.optimizer.state import OptimizationState, StopForecast


@dataclass
class DispatchAction:
    bus_id: str
    action: str                                      
    target_stop: str | None
    reason: str


@dataclass
class DispatchPlan:
    simulation_time: int
    actions: list[DispatchAction]
    objective_score: float


def dispatch(
    state: OptimizationState,
    forecasts: dict[str, StopForecast],
    objective: Objective | None = None,
    use_local_search: bool = True,
) -> DispatchPlan:
    """Produce a dispatch plan for the current state snapshot + forecasts."""
    objective = objective or Objective()
    assignments = greedy_dispatch(state, forecasts)
    if use_local_search:
        assignments = local_search_improve(state, forecasts, assignments, objective)

    actions = [
        DispatchAction(
            bus_id=a.bus_id,
            action="DISPATCH",
            target_stop=a.target_stop,
            reason=a.reason,
        )
        for a in assignments
    ]
    score = plan_cost(state, forecasts, assignments, objective)
    return DispatchPlan(
        simulation_time=state.time_min,
        actions=actions,
        objective_score=round(score, 2),
    )
