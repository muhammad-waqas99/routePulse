"""Event types and the priority-queue ordering rules.

The discrete-event simulator advances a min-heap of events. Events order by
``(time_min, priority, sequence)``:

* ``time_min`` -- the simulated time (minutes from midnight) at which the event
  fires.
* ``priority`` -- a fixed tie-break so that simultaneous events are processed in
  a documented order (passenger arrivals before vehicle departures, arrivals
  before departures, etc.).
* ``sequence`` -- a monotonically increasing counter that makes the ordering of
  otherwise-identical events deterministic and guarantees FIFO behaviour.

Scheduled events can be cancelled (used when a breakdown invalidates the rest of
a trip); cancelled events are skipped when popped, so stale events never mutate
state.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field

                                                                               
             
                                                                               
PASSENGER_ARRIVAL = "PASSENGER_ARRIVAL"
VEHICLE_DEPARTURE = "VEHICLE_DEPARTURE"
VEHICLE_ARRIVAL = "VEHICLE_ARRIVAL"
PASSENGER_ALIGHT = "PASSENGER_ALIGHT"
WAITING_DEADLINE = "WAITING_DEADLINE"
VEHICLE_BREAKDOWN = "VEHICLE_BREAKDOWN"
CONNECTION_CHECK = "CONNECTION_CHECK"

                                                              
                                                                          
                                                                          
                                       
PRIORITY: dict[str, int] = {
    PASSENGER_ARRIVAL: 0,
    VEHICLE_ARRIVAL: 1,
    PASSENGER_ALIGHT: 1,
    VEHICLE_DEPARTURE: 2,
    WAITING_DEADLINE: 3,
    VEHICLE_BREAKDOWN: 4,
    CONNECTION_CHECK: 5,
}

_DEFAULT_PRIORITY = 99


@dataclass(order=True)
class Event:
    """A scheduled simulation event.

    Ordering uses only ``(time_min, priority, sequence)``; the descriptive
    fields never influence ordering.
    """

    time_min: float
    priority: int
    sequence: int
    event_type: str = field(compare=False)
    payload: dict = field(compare=False, default_factory=dict)


class EventQueue:
    """Deterministic min-heap of :class:`Event` objects."""

    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._sequence = 0
        self._cancelled: set[int] = set()

    def schedule(self, time_min: float, event_type: str, payload: dict | None = None) -> Event:
        """Schedule an event and return it (so callers may cancel it later)."""
        event = Event(
            time_min=float(time_min),
            priority=PRIORITY.get(event_type, _DEFAULT_PRIORITY),
            sequence=self._sequence,
            event_type=event_type,
            payload=dict(payload or {}),
        )
        self._sequence += 1
        heapq.heappush(self._heap, event)
        return event

    def cancel(self, event: Event) -> None:
        """Mark ``event`` as cancelled; it will be skipped when popped."""
        self._cancelled.add(event.sequence)

    def pop(self) -> Event:
        """Return the next live (uncancelled) event, raising ``IndexError`` if empty."""
        while self._heap:
            event = heapq.heappop(self._heap)
            if event.sequence not in self._cancelled:
                return event
        raise IndexError("pop from an empty event queue")

    def peek_time(self) -> float | None:
        """Time of the next live event, or ``None`` when the queue is empty."""
        while self._heap and self._heap[0].sequence in self._cancelled:
            heapq.heappop(self._heap)
        return self._heap[0].time_min if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)
