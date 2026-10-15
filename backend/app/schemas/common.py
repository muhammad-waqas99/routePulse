"""Shared API envelope schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard success envelope used by every data endpoint."""

    success: bool = True
    message: str
    data: T


class ErrorResponse(BaseModel):
    """Consistent JSON error payload."""

    success: bool = False
    message: str
    error: str
    detail: str | None = None
