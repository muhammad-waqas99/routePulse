"""Feasible bus-stop candidate generation."""
from __future__ import annotations

from app.optimizer.state import BusState, OptimizationState


def feasible_candidates(
    state: OptimizationState, stop_id: str
) -> list[tuple[BusState, float]]:
    """Return (bus, travel_min) for idle, uncommitted buses that can reach the stop."""
    candidates: list[tuple[BusState, float]] = []
    for bus in state.buses.values():
        if bus.bus_id in state.commitments or not bus.is_available:
            continue
        travel = state.travel(bus.current_stop, stop_id)
        if travel is None:
            continue
        candidates.append((bus, travel))
    return candidates
