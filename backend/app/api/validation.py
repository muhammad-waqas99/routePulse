"""POST /api/v1/validate — independently validate a proposed plan.

OWNED BY: validation + API workstreams.

Accepts a scenario ID and a proposed plan, resolves the canonical network and
scenario from ``data/``, runs the independent validator
(:func:`app.validation.constraints.validate_plan`) and returns the structured
report. A validly submitted but infeasible schedule returns HTTP 200 with
``feasible: false``; only an unknown scenario (or malformed request) is an
error.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.metrics import ValidationReport
from app.schemas.network import Network
from app.schemas.plan import Plan
from app.schemas.scenario import PassengerDemand, Scenario
from app.validation.constraints import validate_plan

router = APIRouter(prefix="/api/v1", tags=["validation"])

                                                                            
                                                                           
DATA_DIR = Path(
    os.environ.get("ROUTEPULSE_DATA_DIR")
    or Path(__file__).resolve().parents[3] / "data"
)


class ValidateRequest(BaseModel):
    """Request body for ``POST /api/v1/validate``."""

    scenario_id: str
    plan: Plan
                                                                         
                                                                               
                              
    demand: list[PassengerDemand] | None = None
                                                                   
    connections: list[dict] | None = None


def _read_json(path: Path):
                                                                           
                                                   
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_network() -> Network:
    """Load the canonical campus network from ``data/network/campus.json``."""
    path = DATA_DIR / "network" / "campus.json"
    if not path.exists():
        raise FileNotFoundError(f"network file not found: {path}")
    return Network.model_validate(_read_json(path))


def load_scenario(scenario_id: str) -> Scenario:
    """Load a scenario by ID, raising ``KeyError`` when it does not exist."""
    path = DATA_DIR / "scenarios" / f"{scenario_id}.json"
    if not path.exists():
        raise KeyError(scenario_id)
    return Scenario.model_validate(_read_json(path))


@router.post("/validate", response_model=ValidationReport)
def validate_endpoint(request: ValidateRequest) -> dict:
    """Validate ``request.plan`` against the scenario and return the report."""
    try:
        network = load_network()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        scenario = load_scenario(request.scenario_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"unknown scenario_id: {request.scenario_id}",
        ) from exc

    return validate_plan(
        network,
        request.plan,
        scenario,
        demand=request.demand,
        connections=request.connections,
    )
