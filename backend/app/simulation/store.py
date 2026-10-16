"""In-memory run store.

The project has no persistence layer yet, so completed simulation results are
kept in a process-local dictionary keyed by ``run_id``. This is enough for the
``GET /api/v1/runs/{run_id}`` endpoint and for follow-up evaluations within a
session. Swapping in a durable store later only requires replacing these
functions.
"""
from __future__ import annotations

from typing import Optional

_RUNS: dict[str, dict] = {}


def save_run(result: dict) -> None:
    """Store a serialised run result under its ``run_id``."""
    _RUNS[result["run_id"]] = result


def get_run(run_id: str) -> Optional[dict]:
    """Return a stored run result, or ``None`` when unknown."""
    return _RUNS.get(run_id)


def clear() -> None:
    """Remove all stored runs (used by tests)."""
    _RUNS.clear()
