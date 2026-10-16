"""Baseline-vs-optimized comparison.

OWNED BY: evaluation workstream.

Runs both plans against identical demand and disruption inputs and reports
differences (see ``docs/evaluation_protocol.md``). The comparison never edits
either result: it reports the candidate's own validation report and, when the
candidate could not be simulated (hard violations), says so instead of
pretending it produced outcomes.
"""
from __future__ import annotations

from typing import Optional

from app.simulation.models import SimulationResult

                                                                            
                                                                              
                
COMPARED_METRICS: dict[str, str] = {
    "unserved_passengers": "lower",
    "served_passengers": "higher",
    "avg_wait_min": "lower",
    "median_wait_min": "lower",
    "max_wait_min": "lower",
    "abandoned_passengers": "lower",
    "total_demand": "neutral",
    "capacity_violations": "lower",
    "vehicle_km": "lower",
    "operating_cost": "lower",
    "vehicle_departures": "neutral",
}


def _metrics_dict(result: SimulationResult) -> dict:
    return result.metrics.model_dump()


def compare_runs(
    baseline: SimulationResult,
    candidate: Optional[SimulationResult] = None,
) -> dict:
    """Compare a baseline run with an optional candidate run.

    Returns a JSON-serialisable summary containing each run's PASSENGER-relevant
    metrics, the per-metric deltas (``candidate - baseline``), and pass/fail
    notes. When ``candidate`` is ``None`` (e.g. it was infeasible and therefore
    not simulated) ``deltas`` is empty and a note explains why.
    """
    baseline_metrics = _metrics_dict(baseline)
    summary: dict = {
        "baseline": {
            "run_id": baseline.run_id,
            "feasible": baseline.feasible,
            "metrics": baseline_metrics,
            "unserved_passengers": baseline_metrics["unserved_passengers"],
        },
        "candidate": None,
        "deltas": {},
        "directions": dict(COMPARED_METRICS),
        "notes": list(baseline.notes),
    }

    if candidate is None:
        summary["notes"].append(
            "candidate was not simulated (hard constraint violations or not requested)"
        )
        return summary

    candidate_metrics = _metrics_dict(candidate)
    deltas: dict[str, float] = {}
    for key in COMPARED_METRICS:
        if key in baseline_metrics and key in candidate_metrics:
            deltas[key] = round(candidate_metrics[key] - baseline_metrics[key], 4)

    summary["candidate"] = {
        "run_id": candidate.run_id,
        "feasible": candidate.feasible,
        "metrics": candidate_metrics,
    }
    summary["deltas"] = deltas
    summary["notes"].extend(candidate.notes)
    return summary
