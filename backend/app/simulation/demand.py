"""Demand loading and conversion for the simulator.

The canonical OD demand lives in the repository's synthetic dataset
(``routepulse_synthetic_data.json``) as ``demand`` records with an origin
(``stopId``), a destination (``destinationStopId``), a ``timeWindow`` such as
``"07:00"``, a passenger ``passengers`` count, and an ``eventFactor``. The data
pipeline under ``scripts/`` maps the rest of that file into ``data/`` but does
not currently emit OD demand, so this module converts the raw OD records into
canonical :class:`~app.schemas.scenario.PassengerDemand` groups on demand.

If a canonical ``data/demand.json`` (a JSON list of ``PassengerDemand`` objects)
exists it is preferred; otherwise the raw synthetic file is converted. Neither
is required: when no demand file is found the simulator simply runs with no
passengers and reports the capacity constraint as unverified.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.schemas.scenario import PassengerDemand

DEFAULT_MAX_WAIT_MIN = 25


def time_to_min(value: Any) -> int:
    """Convert ``"HH:MM"`` (or an int/float of minutes) to minutes from midnight."""
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if ":" in text:
        hours, minutes = text.split(":", 1)
        return int(hours) * 60 + int(minutes)
    return int(float(text))


def raw_to_passenger_demand(
    records: list[dict],
    default_max_wait_min: int = DEFAULT_MAX_WAIT_MIN,
) -> list[PassengerDemand]:
    """Convert raw synthetic ``demand`` records to canonical passenger groups."""
    groups: list[PassengerDemand] = []
    for index, record in enumerate(records):
        origin = record.get("stopId") or record.get("origin_stop_id")
        destination = record.get("destinationStopId") or record.get("destination_stop_id")
        if origin is None or destination is None or origin == destination:
            continue
        demand_id = str(record.get("demandId") or record.get("demand_id") or f"D{index:05d}")
        count = int(round(float(record.get("passengers", 0))))
        if count <= 0:
            continue
        arrival = record.get("arrival_time_min")
        if arrival is None:
            arrival = time_to_min(record.get("timeWindow", 0))
        groups.append(
            PassengerDemand(
                demand_id=demand_id,
                origin_stop_id=str(origin),
                destination_stop_id=str(destination),
                arrival_time_min=int(arrival),
                passenger_count=count,
                max_wait_min=int(record.get("max_wait_min", default_max_wait_min)),
                transfer_allowed=bool(record.get("transfer_allowed", True)),
            )
        )
    return groups


def _read_json(path: Path) -> Any:
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_demand_file(path: Path) -> list[PassengerDemand]:
    """Load OD demand from either a canonical list or the raw synthetic dataset."""
    data = _read_json(path)
    if isinstance(data, dict):
        records = data.get("demand", [])
        return raw_to_passenger_demand(records)
    return [PassengerDemand.model_validate(item) for item in data]


def discover_demand(data_dir: Path) -> Optional[list[PassengerDemand]]:
    """Find and load OD demand, or return ``None`` when none is available."""
    candidates = [
        data_dir / "demand.json",
        data_dir.parent / "routepulse_synthetic_data.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return load_demand_file(candidate)
    return None
