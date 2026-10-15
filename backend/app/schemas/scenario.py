"""Scenario schemas.

The frontend `src/types/scenarios.ts` defines the base contract; the backend
adds optional fields (unavailable vehicle ids, service window) that the UI can
ignore. Extra keys on the wire are harmless to TypeScript consumers.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ScenarioType = Literal["normal", "demand-spike", "vehicle-unavailable"]
ScenarioCategory = Literal["Normal", "Stress Test", "Disruption"]


class Scenario(BaseModel):
    id: str
    name: str
    category: ScenarioCategory
    description: str
    type: ScenarioType
    demandMultiplierPercent: int = Field(ge=0)
    availableVehicles: int = Field(gt=0)
    affectedPeriod: str
    evaluationHorizonMin: int = Field(gt=0)

    # Backend-only operational detail (ignored by the current frontend).
    unavailableVehicleIds: list[str] = Field(default_factory=list)
