"""Metric aggregation from raw simulation state.

Formulas are documented here and fixed; the simulator only tracks raw counters
and :func:`summarize` derives the canonical :class:`Metrics` plus a
passenger-outcome breakdown. Keeping the formulas in one place matches
``docs/evaluation_protocol.md`` and makes the metrics easy to audit.
"""
from __future__ import annotations

import statistics

from app.schemas.metrics import Metrics
from app.simulation.models import PassengerOutcomeSummary
from app.simulation.state import PassengerGroup, SimVehicle


def summarize(
    groups: dict[str, PassengerGroup],
    vehicles: dict[str, SimVehicle],
    counters: dict,
) -> tuple[Metrics, PassengerOutcomeSummary]:
    """Derive metrics and passenger outcomes from finished simulation state.

    * ``avg_wait_min`` / ``median_wait_min`` / ``max_wait_min`` are measured over
      passengers who actually boarded (arrival -> board).
    * ``served`` == ``completed_journeys`` == passengers who reached their
      destination. Boarding alone does not count as served.
    * ``unserved == total_demand - served``; it decomposes into abandoned
      (timed-out), stranded (onboard at the horizon / after a breakdown) and
      still-waiting passengers.
    * ``eta_mae_min`` stays ``None`` unless ETA observations were supplied; the
      simulator never fabricates predictions.
    """
    served = sum(group.completed for group in groups.values())
    abandoned = sum(group.abandoned for group in groups.values())
    waiting_at_horizon = sum(group.waiting for group in groups.values())
    stranded = sum(vehicle.load for vehicle in vehicles.values())

    waits: list[float] = []
    for group in groups.values():
        waits.extend(group.wait_samples)

    total_demand = int(counters.get("total_demand", 0))
    unserved = max(0, total_demand - served)

    avg_wait = round(sum(waits) / len(waits), 2) if waits else 0.0
    median_wait = round(statistics.median(waits), 2) if waits else 0.0
    max_wait = round(max(waits), 2) if waits else 0.0

    eta_observations = int(counters.get("eta_observations", 0))
    metrics = Metrics(
        eta_mae_min=(
            round(counters["eta_mae_sum"] / eta_observations, 2)
            if eta_observations
            else None
        ),
        avg_wait_min=avg_wait,
        unserved_passengers=unserved,
        missed_connections=int(counters.get("missed_connections", 0)),
        capacity_violations=int(counters.get("capacity_violations", 0)),
        vehicle_km=round(float(counters.get("vehicle_km", 0.0)), 3),
        served_passengers=served,
        abandoned_passengers=abandoned,
        total_demand=total_demand,
        completed_journeys=served,
        median_wait_min=median_wait,
        max_wait_min=max_wait,
        passengers_affected_by_breakdowns=int(
            counters.get("affected_by_breakdowns", 0)
        ),
        breakdown_count=int(counters.get("breakdown_count", 0)),
        vehicle_departures=int(counters.get("vehicle_departures", 0)),
        vehicle_arrivals=int(counters.get("vehicle_arrivals", 0)),
        operating_cost=round(float(counters.get("operating_cost", 0.0)), 2),
        cost_available=bool(counters.get("cost_available", True)),
        max_segment_load=int(counters.get("max_segment_load", 0)),
        eta_observations=eta_observations,
    )

    outcomes = PassengerOutcomeSummary(
        total_demand=total_demand,
        served=served,
        unserved=unserved,
        abandoned=abandoned,
        stranded_onboard=stranded,
        waiting_at_horizon=waiting_at_horizon,
        affected_by_breakdowns=int(counters.get("affected_by_breakdowns", 0)),
    )
    return metrics, outcomes
