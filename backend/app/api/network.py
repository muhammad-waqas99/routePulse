"""GET /api/v1/network — return stops, routes, vehicles, and scheduled trips.

OWNED BY: API workstream.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api import deps
from app.schemas.network import Network

router = APIRouter(prefix="/api/v1", tags=["network"])


@router.get("/network", response_model=Network)
def get_network() -> Network:
    """Return the canonical campus network."""
    try:
        return deps.load_network()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
