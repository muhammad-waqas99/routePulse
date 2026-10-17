"""POST /api/v1/optimize — run the optimizer and return a candidate plan.

"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from app.optimizer.scoring import normalize_objective_weights
from app.optimizer.solve import optimize
from app.schemas.metrics import ValidationReport
from app.schemas.plan import Plan
from app.validation.constraints import validate_plan

router = APIRouter(prefix="/api/v1", tags=["optimization"])


class OptimizeRequest(BaseModel):
    """Request body for ``POST /api/v1/optimize``."""

    scenario_id: str
    time_limit_seconds: int | None = Field(default=None, gt=0)
    objective_weights: dict[str, float] | None = None


class OptimizeResponse(BaseModel):
    """A candidate plan plus its independent validation."""

    scenario_id: str
    plan: Plan
    feasible: bool
    solver_status: str
    validation: ValidationReport
    notes: list[str] = Field(default_factory=list)


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_endpoint(request: OptimizeRequest) -> OptimizeResponse:
    """Run the vehicle-assignment optimizer and validate the candidate plan."""
    try:
        network = deps.load_network()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    try:
        scenario = deps.load_scenario(request.scenario_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"unknown scenario_id: {request.scenario_id}"
        ) from exc

    notes: list[str] = []
    try:
        weights = normalize_objective_weights(request.objective_weights)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if request.time_limit_seconds is not None:
        notes.append("The current greedy optimizer does not support a time limit; this value was not applied.")

    demand = deps.load_demand()
    try:
        plan = optimize(
            network,
            scenario,
            time_limit_seconds=request.time_limit_seconds,
            demand=demand,
            objective_weights=weights,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if plan.solver_status == "BASELINE_RETAINED":
        notes.append("The candidate did not improve the weighted operating objective; the baseline assignment was retained.")
    validation = validate_plan(network, plan, scenario, demand=demand)
    return OptimizeResponse(
        scenario_id=request.scenario_id,
        plan=plan,
        feasible=validation["feasible"],
        solver_status=plan.solver_status,
        validation=validation,
        notes=notes,
    )
