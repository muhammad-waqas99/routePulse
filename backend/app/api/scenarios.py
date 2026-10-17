"""GET /api/v1/scenarios and POST /api/v1/scenarios/{id}/run.

"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from app.evaluation.comparison import compare_runs
from app.optimizer.fallback import fallback_plan
from app.optimizer.solve import optimize
from app.schemas.plan import Plan
from app.schemas.scenario import PassengerDemand, Scenario
from app.simulation.engine import simulate
from app.simulation.models import SimulationResult
from app.simulation.store import save_run
from app.validation.constraints import validate_plan

router = APIRouter(prefix="/api/v1", tags=["scenarios"])


class RunRequest(BaseModel):
    """Request body for ``POST /api/v1/scenarios/{scenario_id}/run``."""

    include_optimized: bool = False
    run_baseline: bool = True
    seed: int = 42
    evaluation_horizon_min: int | None = None
                                                                          
    plan: Plan | None = None
                                                                               
                                                
    demand: list[PassengerDemand] | None = None


class RunResponse(BaseModel):
    """Response for the scenario-run endpoint."""

    run_id: str
    scenario_id: str
    baseline: SimulationResult | None = None
    optimized: SimulationResult | None = None
    comparison: dict | None = None
    notes: list[str] = Field(default_factory=list)


def _load(scenario_id: str):
    try:
        network = deps.load_network()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    try:
        scenario = deps.load_scenario(scenario_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"unknown scenario_id: {scenario_id}"
        ) from exc
    return network, scenario


@router.get("/scenarios", response_model=list[Scenario])
def list_scenarios_endpoint() -> list[Scenario]:
    """List the available disruption scenarios."""
    return deps.list_scenarios()


@router.post("/scenarios/{scenario_id}/run", response_model=RunResponse)
def run_scenario(scenario_id: str, request: RunRequest) -> RunResponse:
    """Simulate the baseline (and optionally the optimized) plan for a scenario.

    The baseline is always simulated so its measurable outcomes are reported even
    when it is infeasible (with ``feasible: false``); the optimized candidate is
    simulated only when its hard constraints pass.
    """
    network, scenario = _load(scenario_id)
    demand = request.demand if request.demand is not None else deps.load_demand()

    notes: list[str] = []
    baseline_result: SimulationResult | None = None
    optimized_result: SimulationResult | None = None

    baseline_plan = request.plan or fallback_plan(network, scenario)
    if request.run_baseline:
        baseline_result = simulate(
            network,
            baseline_plan,
            scenario,
            demand=demand,
            seed=request.seed,
            horizon_min=request.evaluation_horizon_min,
        )
        save_run(baseline_result.model_dump())
        if not baseline_result.feasible:
            notes.append(
                f"baseline plan is infeasible ({baseline_result.validation.hard_violation_count} violations)"
            )

    if request.include_optimized:
        candidate_plan = optimize(network, scenario, demand=demand)
        candidate_validation = validate_plan(
            network, candidate_plan, scenario, demand=demand
        )
        if candidate_validation["feasible"]:
            optimized_result = simulate(
                network,
                candidate_plan,
                scenario,
                demand=demand,
                seed=request.seed,
                horizon_min=request.evaluation_horizon_min,
            )
            save_run(optimized_result.model_dump())
        else:
            notes.append(
                "optimized candidate was not simulated: "
                f"{candidate_validation['hard_violation_count']} hard violations"
            )

    comparison = None
    if baseline_result is not None:
        comparison = compare_runs(baseline_result, optimized_result)
        comparison.setdefault("notes", [])
        comparison["notes"].extend(notes)

    run_id = (
        baseline_result.run_id
        if baseline_result is not None
        else (optimized_result.run_id if optimized_result is not None else f"run_{scenario_id}")
    )
    return RunResponse(
        run_id=run_id,
        scenario_id=scenario_id,
        baseline=baseline_result,
        optimized=optimized_result,
        comparison=comparison,
        notes=notes,
    )
