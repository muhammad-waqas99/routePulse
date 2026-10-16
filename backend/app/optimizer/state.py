"""Optimizer state snapshot.

The optimizer never mutates the simulator: it reads a snapshot of the current
state (buses, queues, commitments, travel times) and returns proposed actions.
The simulator remains the authority on what actually happens.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BusState:
    bus_id: str
    current_stop: str
    capacity: int
    onboard: int = 0
    status: str = "idle"                                        

    @property
    def available_seats(self) -> int:
        return max(0, self.capacity - self.onboard)

    @property
    def is_available(self) -> bool:
        return self.status == "idle" and self.available_seats > 0


@dataclass
class StopQueue:
    """Passengers currently waiting at a stop (count + destinations)."""

    stop_id: str
    waiting: int = 0
    destinations: list[str] = field(default_factory=list)


@dataclass
class StopForecast:
    """Prediction-engine output for one stop, numeric and dispatcher-ready."""

    stop_id: str
    demand: float = 0.0
    shortfall: float = 0.0
    risk: float = 0.0                           


@dataclass
class OptimizationState:
    """Snapshot consumed by the dispatcher."""

    time_min: int
    buses: dict[str, BusState]
    queues: dict[str, StopQueue]
    travel_matrix: dict[tuple[str, str], float]
    commitments: set[str] = field(default_factory=set)

    def travel(self, origin: str, dest: str) -> float | None:
        return self.travel_matrix.get((origin, dest))


@dataclass
class Assignment:
    """A bus-to-stop assignment produced by the dispatcher."""

    bus_id: str
    target_stop: str
    reason: str = ""
