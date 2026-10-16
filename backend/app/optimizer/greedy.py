"""Greedy dispatch: assign available buses to the most urgent stops."""
from __future__ import annotations

from app.optimizer.candidates import feasible_candidates
from app.optimizer.cost import incremental_cost
from app.optimizer.priorities import urgency
from app.optimizer.state import Assignment, OptimizationState, StopForecast


def greedy_dispatch(
    state: OptimizationState,
    forecasts: dict[str, StopForecast],
    lambdas: dict | None = None,
) -> list[Assignment]:
    """Assign idle buses to stops ranked by urgency (shortfall + queue + risk)."""

    def stop_urgency(item: tuple[str, StopForecast]) -> float:
        stop_id, fc = item
        queue = state.queues.get(stop_id)
        return urgency(
            queue=queue.waiting if queue else 0,
            shortfall=fc.shortfall,
            risk=fc.risk,
        )

    ranked = sorted(forecasts.items(), key=stop_urgency, reverse=True)

    assignments: list[Assignment] = []
    for stop_id, fc in ranked:
        candidates = feasible_candidates(state, stop_id)
        if not candidates:
            continue
                                                                                
        candidates.sort(
            key=lambda c: incremental_cost(
                c[1], onboard_impact=c[0].onboard, added_distance=c[1], lambdas=lambdas
            )
        )
        bus, _ = candidates[0]
        state.commitments.add(bus.bus_id)
        reason = "High forecast shortfall" if fc.shortfall > 0 else "Serving queued passengers"
        assignments.append(Assignment(bus_id=bus.bus_id, target_stop=stop_id, reason=reason))

    return assignments
