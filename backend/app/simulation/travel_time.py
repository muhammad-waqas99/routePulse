"""Segment travel-time computation for the simulator.

Travel times come from the canonical ``Route.segment_travel_min`` and are scaled
by scenario multipliers:

* ``Scenario.travel_time_multipliers[route_id]`` scales an entire route.
* An optional ``segment_multipliers`` mapping (keyed ``(route_id,
  segment_index)``) scales individual segments. The canonical scenario schema
  has no segment-level field; this hook lets tests and future scenarios express
  localised slowdowns without changing the schema.

Rounding rule: each *segment* duration is rounded to the nearest whole minute.
A segment with a positive base duration is never rounded below 1 minute, so a
vehicle can never "arrive before it departs" and the event loop always makes
forward progress.
"""
from __future__ import annotations

from typing import Optional

from app.schemas.network import Route
from app.schemas.scenario import Scenario


def segment_duration_min(
    route: Route,
    segment_index: int,
    scenario: Optional[Scenario] = None,
    segment_multipliers: Optional[dict[tuple[str, int], float]] = None,
) -> int:
    """Rounded duration (minutes) of ``route``'s ``segment_index``."""
    base = route.segment_travel_min[segment_index]
    multiplier = 1.0
    if scenario is not None:
        multiplier *= scenario.travel_time_multipliers.get(route.route_id, 1.0)
    if segment_multipliers:
        multiplier *= segment_multipliers.get((route.route_id, segment_index), 1.0)

    duration = base * multiplier
    rounded = int(round(duration))
    if base > 0 and rounded < 1:
        rounded = 1
    return rounded


def route_duration_min(
    route: Route,
    scenario: Optional[Scenario] = None,
    segment_multipliers: Optional[dict[tuple[str, int], float]] = None,
) -> int:
    """Total rounded duration of traversing all of ``route``'s segments."""
    return sum(
        segment_duration_min(route, i, scenario, segment_multipliers)
        for i in range(len(route.segment_travel_min))
    )
