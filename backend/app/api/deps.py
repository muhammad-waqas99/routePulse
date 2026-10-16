"""Shared data-loading helpers for the API routers.

Loads the canonical network, scenarios, and OD demand from ``data/`` (and, for
demand, the raw synthetic dataset at the repository root). Tests may override the
module-level ``DATA_DIR`` to point at a fixture directory.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from app.schemas.network import Network
from app.schemas.scenario import PassengerDemand, Scenario
from app.simulation.demand import discover_demand

DATA_DIR = Path(
    os.environ.get("ROUTEPULSE_DATA_DIR")
    or Path(__file__).resolve().parents[3] / "data"
)


def _read_json(path: Path):
                                                                              
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_network() -> Network:
    """Load the canonical campus network from ``data/network/campus.json``."""
    path = DATA_DIR / "network" / "campus.json"
    if not path.exists():
        raise FileNotFoundError(f"network file not found: {path}")
    return Network.model_validate(_read_json(path))


def load_scenario(scenario_id: str) -> Scenario:
    """Load a scenario by ID, raising ``KeyError`` when it does not exist."""
    path = DATA_DIR / "scenarios" / f"{scenario_id}.json"
    if not path.exists():
        raise KeyError(scenario_id)
    return Scenario.model_validate(_read_json(path))


def list_scenarios() -> list[Scenario]:
    """Load every scenario under ``data/scenarios`` in deterministic order."""
    scenario_dir = DATA_DIR / "scenarios"
    if not scenario_dir.exists():
        return []
    scenarios = [
        Scenario.model_validate(_read_json(path))
        for path in sorted(scenario_dir.glob("*.json"))
    ]
    return scenarios


def load_demand() -> list[PassengerDemand] | None:
    """Load OD demand, or ``None`` when no demand file is available."""
    return discover_demand(DATA_DIR)
