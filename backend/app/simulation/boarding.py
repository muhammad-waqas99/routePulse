"""Boarding/alighting policy.

OWNED BY: simulation workstream.

Deterministic policy (documented in ``Wild Bugs.md``):

* Passengers wait at a stop in FCFS order: earlier ``arrival_time_min`` first,
  breaking ties by ``demand_id``.
* A passenger may only board a vehicle whose *current trip* visits their origin
  strictly before their destination (both on the trip's route). Transfers are
  not modelled, so a passenger whose destination is not downstream simply waits
  and eventually times out.
* Boarding proceeds while capacity remains and splits groups: the boarded part
  leaves the queue, the remainder keeps waiting.
* Passengers alight exactly at their destination stop.
* Passengers still waiting past ``arrival_time_min + max_wait_min`` abandon the
  system.
"""
from __future__ import annotations

from app.simulation.state import PassengerBatch, PassengerGroup, SimVehicle


def board_at_stop(
    vehicle: SimVehicle,
    waiting: list[PassengerGroup],
    stop_index_map: dict[str, int],
    stop_index: int,
    time_min: float,
) -> int:
    """Board eligible waiting passengers onto ``vehicle`` at ``stop_index``.

    Returns the number of passengers boarded. Mutates ``waiting`` (the caller's
    queue) and ``vehicle.onboard``.
    """
    capacity_left = vehicle.vehicle.capacity - vehicle.load
    if capacity_left <= 0:
        return 0

    order = sorted(
        waiting,
        key=lambda g: (g.arrival_time_min, g.demand_id),
    )
    boarded = 0
    for group in order:
        if capacity_left <= 0:
            break
        if group.waiting <= 0:
            continue
        if not group.transfer_allowed and group.destination_stop_id not in stop_index_map:
            continue
        destination_index = stop_index_map.get(group.destination_stop_id)
        if destination_index is None or destination_index <= stop_index:
            continue

        take = min(group.waiting, capacity_left)
        group.waiting -= take
        group.boarded += take
        wait = max(0.0, time_min - group.arrival_time_min)
        group.wait_sum += wait * take
        group.wait_samples.extend([wait] * take)
        vehicle.onboard.append(
            PassengerBatch(
                group=group,
                count=take,
                destination_stop_id=group.destination_stop_id,
                board_time_min=time_min,
                board_stop_id=vehicle.current_stop_id,
            )
        )
        capacity_left -= take
        boarded += take
    return boarded


def alight_at_stop(vehicle: SimVehicle, stop_id: str) -> int:
    """Alight every passenger whose destination is ``stop_id``.

    Returns the number of passengers who completed their journey.
    """
    completed = 0
    remaining: list[PassengerBatch] = []
    for batch in vehicle.onboard:
        if batch.destination_stop_id == stop_id:
            batch.group.completed += batch.count
            completed += batch.count
        else:
            remaining.append(batch)
    vehicle.onboard = remaining
    return completed
