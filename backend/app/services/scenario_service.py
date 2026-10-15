"""Scenario loading and lookup."""

from __future__ import annotations

import json
from functools import lru_cache

from app.config import settings
from app.schemas.scenario import Scenario


class UnknownScenarioError(KeyError):
    """Raised when a caller references a scenario id that does not exist."""

    def __init__(self, scenario_id: str) -> None:
        super().__init__(scenario_id)
        self.scenario_id = scenario_id


@lru_cache(maxsize=1)
def _load_scenarios() -> dict[str, Scenario]:
    with settings.scenarios_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    scenarios: dict[str, Scenario] = {}
    for item in raw.get("scenarios", []):
        scenario = Scenario.model_validate(item)
        scenarios[scenario.id] = scenario

    if not scenarios:
        raise RuntimeError("No scenarios are defined in scenarios.json")
    return scenarios


def list_scenarios() -> list[Scenario]:
    return list(_load_scenarios().values())


def get_scenario(scenario_id: str) -> Scenario:
    scenarios = _load_scenarios()
    if scenario_id not in scenarios:
        raise UnknownScenarioError(scenario_id)
    return scenarios[scenario_id]
