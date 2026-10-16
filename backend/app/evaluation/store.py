"""Process-local evaluation history used by the Performance Lab API."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

_EVALUATIONS: dict[str, dict] = {}


def save_evaluation(result: dict) -> str:
                                                                          
                                                                               
    evaluation_id = f"eval_{uuid4().hex[:12]}"
    _EVALUATIONS[evaluation_id] = {
        **result,
        "evaluation_id": evaluation_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return evaluation_id


def list_evaluations() -> list[dict]:
    return list(reversed(list(_EVALUATIONS.values())))


def get_evaluation(evaluation_id: str) -> dict | None:
    return _EVALUATIONS.get(evaluation_id)


def clear() -> None:
    _EVALUATIONS.clear()
