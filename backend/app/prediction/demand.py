"""Baseline demand forecast.

The seed data contains a single observation per stop, so a naive "persistence"
forecast (next period demand equals the observed level, optionally scaled by a
scenario multiplier) is used. This is deliberately simple and explainable; it
is not a trained forecasting model.
"""

from __future__ import annotations

from app.optimizer.model import DemandBatch, NetworkModel, build_demand
from app.schemas.network import DemandRecord
from app.schemas.scenario import Scenario


def forecast_demand(
    network: NetworkModel, scenario: Scenario
) -> list[DemandBatch]:
    """Return scaled demand batches for a scenario (persistence forecast)."""

    return build_demand(network, scenario)


def forecast_record_counts(
    network: NetworkModel, scenario: Scenario
) -> list[DemandRecord]:
    """Return per-stop forecast counts in the API's demand record shape."""

    multiplier = 1.0 + scenario.demandMultiplierPercent / 100.0
    records: list[DemandRecord] = []
    for record in network.raw.demand:
        records.append(
            DemandRecord(
                stopId=record.stopId,
                time=record.time,
                passengerCount=int(round(record.passengerCount * multiplier)),
            )
        )
    return records
