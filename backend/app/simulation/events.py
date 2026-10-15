"""Demand events and congestion model for the simulation.

Everything here is a pure function of the inputs, so both the baseline and the
optimized plan are simulated under byte-for-byte identical demand and
congestion conditions.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.optimizer.model import DemandBatch

# Congestion is modelled deterministically: a trip is delayed proportionally to
# how busy the demand bucket it departs in is, relative to the busiest bucket.
MAX_CONGESTION = 0.5
_DEFAULT_BUCKET_MIN = 15


@dataclass(frozen=True)
class Passenger:
    """A single waiting passenger."""

    stop_id: str
    arrival_min: float


def expand_passengers(demand: list[DemandBatch]) -> list[Passenger]:
    """Expand counted demand batches into individual passengers.

    Batch members share the same arrival time. The list is ordered so boarding
    is FIFO by arrival time then stop id, making the simulation deterministic.
    """

    passengers: list[Passenger] = []
    for batch in demand:
        for _ in range(batch.count):
            passengers.append(
                Passenger(stop_id=batch.stop_id, arrival_min=float(batch.time_min))
            )

    passengers.sort(key=lambda p: (p.arrival_min, p.stop_id))
    return passengers


def demand_buckets(
    demand: list[DemandBatch], bucket_min: int = _DEFAULT_BUCKET_MIN
) -> dict[int, int]:
    """Total demand counted per ``bucket_min`` bucket keyed by bucket start."""

    buckets: dict[int, int] = {}
    for batch in demand:
        key = (batch.time_min // bucket_min) * bucket_min
        buckets[key] = buckets.get(key, 0) + batch.count
    return buckets


def congestion_factor(
    demand: list[DemandBatch],
    departure_min: float,
    bucket_min: int = _DEFAULT_BUCKET_MIN,
) -> float:
    """Return the travel-time multiplier for a trip departing at a time.

    ``1.0`` when there is no demand; up to ``1 + MAX_CONGESTION`` when demand is
    at its busiest bucket.
    """

    buckets = demand_buckets(demand, bucket_min)
    if not buckets:
        return 1.0

    peak = max(buckets.values())
    if peak <= 0:
        return 1.0

    key = (int(departure_min) // bucket_min) * bucket_min
    bucket_value = buckets.get(key, 0)
    return 1.0 + MAX_CONGESTION * (bucket_value / peak)
