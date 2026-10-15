"""Scenario listing endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.scenario import Scenario
from app.services.scenario_service import list_scenarios

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=ApiResponse[list[Scenario]])
def get_scenarios() -> ApiResponse[list[Scenario]]:
    return ApiResponse[list[Scenario]](
        success=True,
        message="Scenarios retrieved successfully",
        data=list_scenarios(),
    )
