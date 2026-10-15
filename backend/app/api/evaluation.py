"""Evaluation results endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.evaluation import PerformanceLabData, PerformanceRun
from app.services import run_store

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.get("", response_model=ApiResponse[PerformanceLabData])
def list_evaluation_runs() -> ApiResponse[PerformanceLabData]:
    return ApiResponse[PerformanceLabData](
        success=True,
        message="Evaluation runs retrieved successfully",
        data=PerformanceLabData(runs=run_store.list_runs()),
    )


@router.get("/{run_id}", response_model=ApiResponse[PerformanceRun])
def get_evaluation_run(run_id: str) -> ApiResponse[PerformanceRun]:
    run = run_store.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation run '{run_id}' was not found.",
        )
    return ApiResponse[PerformanceRun](
        success=True,
        message="Evaluation run retrieved successfully",
        data=run,
    )
