"""Local search improvement over the greedy dispatch plan."""
from __future__ import annotations

from app.optimizer.cost import Objective, plan_cost
from app.optimizer.state import Assignment, OptimizationState, StopForecast


def local_search_improve(
    state: OptimizationState,
    forecasts: dict[str, StopForecast],
    assignments: list[Assignment],
    objective: Objective,
    max_iterations: int = 100,
) -> list[Assignment]:
    """Try swapping target stops between pairs of buses; keep cost-improving swaps.

    This is a small hill-climbing pass, not a global solver. It improves the
    greedy plan without requiring a heavyweight optimizer.
    """
    best = list(assignments)
    best_cost = plan_cost(state, forecasts, best, objective)

    improved = True
    iterations = 0
    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for i in range(len(best)):
            for j in range(i + 1, len(best)):
                candidate = list(best)
                candidate[i] = Assignment(best[i].bus_id, best[j].target_stop, best[i].reason)
                candidate[j] = Assignment(best[j].bus_id, best[i].target_stop, best[j].reason)
                cost = plan_cost(state, forecasts, candidate, objective)
                if cost < best_cost - 1e-9:
                    best, best_cost = candidate, cost
                    improved = True
    return best
