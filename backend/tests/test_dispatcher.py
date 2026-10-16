"""Tests for the greedy dispatcher and local search."""
from __future__ import annotations

from app.optimizer.cost import Objective
from app.optimizer.dispatcher import dispatch
from app.optimizer.greedy import greedy_dispatch
from app.optimizer.state import (
    BusState,
    OptimizationState,
    StopForecast,
    StopQueue,
)


def _state() -> OptimizationState:
    buses = {
        "B1": BusState("B1", "S1", 30),
        "B2": BusState("B2", "S2", 30),
    }
    queues = {
        "S1": StopQueue("S1", waiting=0),
        "S2": StopQueue("S2", waiting=0),
        "S3": StopQueue("S3", waiting=10),
        "S4": StopQueue("S4", waiting=5),
    }
    travel = {
        ("S1", "S3"): 5.0, ("S2", "S4"): 3.0,
        ("S1", "S4"): 10.0, ("S2", "S3"): 8.0,
        ("S3", "S1"): 5.0, ("S4", "S2"): 3.0,
        ("S4", "S1"): 10.0, ("S3", "S2"): 8.0,
    }
    return OptimizationState(time_min=0, buses=buses, queues=queues, travel_matrix=travel)


def _forecasts() -> dict[str, StopForecast]:
    return {
        "S1": StopForecast("S1", demand=0, shortfall=0, risk=0.0),
        "S2": StopForecast("S2", demand=0, shortfall=0, risk=0.0),
        "S3": StopForecast("S3", demand=20, shortfall=15, risk=2.0),
        "S4": StopForecast("S4", demand=10, shortfall=0, risk=0.0),
    }


def test_greedy_dispatches_to_shortfall() -> None:
    assignments = greedy_dispatch(_state(), _forecasts())
    targets = {a.target_stop for a in assignments}
    assert "S3" in targets                               
    assert len(assignments) == 2                              


def test_dispatch_returns_plan() -> None:
    plan = dispatch(_state(), _forecasts())
    assert plan.simulation_time == 0
    assert len(plan.actions) == 2
    assert plan.objective_score >= 0


def test_local_search_does_not_worsen() -> None:
    obj = Objective()
    greedy_plan = dispatch(_state(), _forecasts(), objective=obj, use_local_search=False)
    improved_plan = dispatch(_state(), _forecasts(), objective=obj, use_local_search=True)
    assert improved_plan.objective_score <= greedy_plan.objective_score + 1e-9
