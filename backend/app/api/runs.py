"""GET /api/v1/runs/{run_id} — retrieve a stored simulation run.

OWNED BY: API workstream.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.simulation.store import get_run

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get("/runs/{run_id}")
def get_run_endpoint(run_id: str) -> dict:
    """Return a previously stored run result, or 404 when it is unknown."""
    result = get_run(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"unknown run_id: {run_id}")
    return result
