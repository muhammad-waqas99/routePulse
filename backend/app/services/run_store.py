"""In-memory store for optimization/evaluation runs.

Survives for the lifetime of the process, which is sufficient for the current
single-session demo. The interface is deliberately narrow so it can be swapped
for a database later without touching the API layer.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from datetime import datetime, timezone

from app.schemas.evaluation import PerformanceRun

_lock = threading.Lock()
_runs: "OrderedDict[str, PerformanceRun]" = OrderedDict()
_counter = 1000


def next_run_id() -> str:
    """Return the next sequential run id (thread-safe)."""

    global _counter
    with _lock:
        _counter += 1
        return str(_counter)


def save_run(run: PerformanceRun) -> None:
    with _lock:
        _runs[run.runId] = run


def get_run(run_id: str) -> PerformanceRun | None:
    with _lock:
        return _runs.get(run_id)


def list_runs() -> list[PerformanceRun]:
    """Return runs newest first (by creation time, then id)."""

    with _lock:
        runs = list(_runs.values())
    runs.sort(key=lambda run: (run.createdAt, run.runId), reverse=True)
    return runs


def clear() -> None:
    """Reset the store (used by tests)."""

    global _counter
    with _lock:
        _runs.clear()
        _counter = 1000


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
