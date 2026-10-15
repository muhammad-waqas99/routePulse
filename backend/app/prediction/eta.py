"""Baseline ETA prediction.

No live GPS feed exists in the sample data, so ETAs are derived from the
published schedule plus a deterministic congestion adjustment. This is an
explicitly labelled baseline method, not a machine-learned model.
"""

from __future__ import annotations

from app.optimizer.model import (
    NetworkModel,
    build_demand,
    format_time,
    parse_time,
)
from app.schemas.network import EtaRecord
from app.schemas.scenario import Scenario
from app.simulation.events import congestion_factor

# A neutral scenario (no demand multiplier) is used purely as a congestion
# input for the schedule-based ETA baseline.
_NORMAL_SCENARIO = Scenario(
    id="normal_operations",
    name="Normal Operations",
    category="Normal",
    description="Baseline",
    type="normal",
    demandMultiplierPercent=0,
    availableVehicles=4,
    affectedPeriod="08:00-09:00",
    evaluationHorizonMin=120,
)


def predict_trip_etas(network: NetworkModel, trip) -> list[EtaRecord]:
    """Return scheduled + estimated arrivals for every stop of a trip."""

    route = network.route(trip.routeId)
    departure = parse_time(trip.departureTime)
    demand = build_demand(network, _NORMAL_SCENARIO)
    factor = congestion_factor(demand, departure)

    records: list[EtaRecord] = []
    for index, stop_id in enumerate(route.stop_ids):
        scheduled = departure + route.offsets_min[index]
        estimated = departure + route.offsets_min[index] * factor
        records.append(
            EtaRecord(
                tripId=trip.id,
                stopId=stop_id,
                scheduledArrival=format_time(scheduled),
                estimatedArrival=format_time(estimated),
            )
        )
    return records


def predict_all_etas(network: NetworkModel) -> list[EtaRecord]:
    """Predict ETAs for every published trip in the network."""

    records: list[EtaRecord] = []
    for trip in network.raw.trips:
        records.extend(predict_trip_etas(network, trip))
    return records
