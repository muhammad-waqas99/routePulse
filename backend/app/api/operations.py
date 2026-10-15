"""Operations overview endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.network import OperationsData
from app.services.operations_service import get_operations_overview

router = APIRouter(prefix="/api/operations", tags=["operations"])


@router.get("/overview", response_model=ApiResponse[OperationsData])
def overview() -> ApiResponse[OperationsData]:
    return ApiResponse[OperationsData](
        success=True,
        message="Operations overview retrieved successfully",
        data=get_operations_overview(),
    )
