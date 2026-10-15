"""Optimization endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.optimization import OptimizeRequest, OptimizeResponse
from app.services.pipeline_service import run_optimization
from app.services.scenario_service import UnknownScenarioError, list_scenarios

logger = logging.getLogger("routepulse.optimization")

router = APIRouter(prefix="/api", tags=["optimization"])


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest) -> OptimizeResponse:
    """Run the recovery optimization pipeline for a scenario.

    Returns the computed plan, independent validation, simulated metrics and a
    comparison against the baseline. Unknown scenarios return 404; an
    infeasible scenario returns HTTP 200 with ``status == "infeasible"`` and an
    explanatory ``message``/``warnings``.
    """

    try:
        return run_optimization(request.scenarioId)
    except UnknownScenarioError:
        allowed = ", ".join(scenario.id for scenario in list_scenarios())
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario '{request.scenarioId}'. Known scenarios: {allowed}.",
        ) from None
    except Exception:  # noqa: BLE001 - log and return a safe message
        logger.exception("Unexpected error while optimizing scenario %s", request.scenarioId)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while optimizing the scenario.",
        ) from None
