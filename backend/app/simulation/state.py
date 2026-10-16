"""Mutable runtime state for the discrete-event simulator.

These dataclasses hold the *dynamic* state that :mod:`app.simulation.engine`
mutates as events fire. They are deliberately separate from the canonical
Pydantic schemas (which describe the static inputs and the serialisable
results).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.network import Vehicle


@dataclass
class PassengerGroup:
    """A still-tracked group of passengers sharing an origin/destination.

    ``waiting`` shrinks as passengers board; ``completed``/``abandoned`` grow as
    passengers reach their destination or time out. ``original_count`` never
    changes and lets the invariant
    ``original_count == waiting + boarded`` hold, where
    ``boarded == completed + (currently onboard)``.
    """

    demand_id: str
    origin_stop_id: str
    destination_stop_id: str
    arrival_time_min: float
    max_wait_min: int
    original_count: int
    waiting: int
    transfer_allowed: bool = True

    boarded: int = 0
    completed: int = 0
    abandoned: int = 0

                                                                               
    wait_sum: float = 0.0
    wait_samples: list[float] = field(default_factory=list)


@dataclass
class PassengerBatch:
    """Passengers of one group currently riding one vehicle."""

    group: PassengerGroup
    count: int
    destination_stop_id: str
    board_time_min: float
    board_stop_id: str


                        
IDLE = "idle"
IN_TRANSIT = "in_transit"
BROKEN_DOWN = "broken_down"


@dataclass
class SimVehicle:
    """Runtime state of a single vehicle."""

    vehicle: Vehicle
    current_stop_id: str
    status: str = IDLE
    trip_id: str | None = None
    route_id: str | None = None
    onboard: list[PassengerBatch] = field(default_factory=list)

    @property
    def load(self) -> int:
        return sum(batch.count for batch in self.onboard)
