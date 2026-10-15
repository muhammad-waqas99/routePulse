"""FIFO boarding logic used by the simulation engine."""

from __future__ import annotations

from collections import deque

from app.simulation.events import Passenger


def board_waiting(
    waiting: deque[Passenger],
    arrival_min: float,
    onboard: int,
    capacity: int,
) -> list[Passenger]:
    """Board as many waiting passengers as capacity allows.

    ``waiting`` is a deque of passengers ordered by arrival time. Only
    passengers who are already present (``arrival_min <= arrival_min`` of the
    bus) can board. Boarded passengers are removed from the deque so they are
    not served twice.
    """

    boarded: list[Passenger] = []
    while waiting:
        candidate = waiting[0]
        if candidate.arrival_min > arrival_min:
            # Not yet present; everyone behind them arrived later too.
            break
        if onboard >= capacity:
            # Vehicle is full; leave the passenger waiting.
            break
        boarded.append(waiting.popleft())
        onboard += 1

    return boarded
