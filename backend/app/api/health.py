"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    """Confirm the backend is running."""

    return {
        "success": True,
        "status": "ok",
        "service": "routepulse-backend",
        "version": __version__,
    }
