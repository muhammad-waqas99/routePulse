"""Deterministic recovery optimizer.

Algorithm (documented explicitly so the result is never mistaken for a
mathematical optimum):

1. **Fleet selection** - pick the highest-capacity eligible vehicles up to the
   scenario's ``availableVehicles`` count.
2. **Baseline plan** - the published schedule in ``network.json``, pruned of
   any trip whose vehicle is unavailable under the scenario. No adaptation.
3. **Constructive scheduling** - demand batches are processed in chronological
   order. Each batch first tries to board an already-dispatched trip on its
   route (if the trip has not passed the stop yet and has spare capacity).
   Unassigned passengers spawn a new trip on the earliest available vehicle,
   scheduled so it arrives at the stop just after the batch is created.
4. **Local search** - a repair pass attempts to cancel trips whose passengers
   can be re-accommodated on other trips without breaking capacity or timing,
   which reduces vehicle distance while preserving service.

Hard constraints are *not* enforced here by trust: the resulting plan is handed
to :mod:`app.validation.constraints` which re-checks it independently.
"""

from __future__ import annotations

import math

from app.optimizer.model import (
    DemandBatch,
    NetworkModel,
    Plan,
    PlannedTrip,
    build_demand,
    parse_period,
    select_fleet,
)
from app.schemas.scenario import Scenario

DEPARTURE_STEP_MIN = 5


class InfeasibleError(Exception):
    """Raised when no valid plan can be produced for a scenario."""


def _ceil_to_step(value: float, step: int) -> int:
    return int(math.ceil(value / step) * step)


def _service_window(scenario: Scenario) -> tuple[int, int]:
    return parse_period(scenario.affectedPeriod)


def build_baseline_plan(
    network: NetworkModel, scenario: Scenario
) -> Plan:
    """Return the published timetable, pruned for unavailable vehicles."""

    unavailable = set(scenario.unavailableVehicleIds)
    trips: list[PlannedTrip] = []

    for trip in network.raw.trips:
        if trip.vehicleId in unavailable:
            continue
        if trip.vehicleId not in network.vehicles:
            continue
        from app.optimizer.model import parse_time

        trips.append(
            PlannedTrip(
                trip_id=trip.id,
                route_id=trip.routeId,
                vehicle_id=trip.vehicleId,
                departure_min=parse_time(trip.departureTime),
            )
        )

    return Plan(plan_id="baseline", label="Baseline (published timetable)", trips=trips)


def assign_existing_boardings(
    network: NetworkModel,
    demand: list[DemandBatch],
    trips: list[PlannedTrip],
) -> dict[str, int]:
    """Greedily assign demand to a fixed set of trips.

    Returns a mapping of ``trip_id -> boarded`` for quick reporting. Boardings
    are written onto the trip objects.
    """

    for trip in trips:
        trip.boardings = {}

    trips_by_route: dict[str, list[PlannedTrip]] = {}
    for trip in trips:
        trips_by_route.setdefault(trip.route_id, []).append(trip)

    for route_trips in trips_by_route.values():
        route_trips.sort(key=lambda t: t.departure_min)

    boarded: dict[str, int] = {trip.trip_id: 0 for trip in trips}

    for batch in demand:
        route = network.route(batch.route_id)
        offset = route.offset_for(batch.stop_id)
        remaining = batch.count

        for trip in trips_by_route.get(batch.route_id, []):
            if trip.departure_min + offset < batch.time_min:
                continue
            vehicle = network.vehicle(trip.vehicle_id)
            free = vehicle.capacity - trip.total_boarded
            if free <= 0:
                continue
            take = min(remaining, free)
            if take <= 0:
                continue
            trip.boardings[batch.stop_id] = trip.boardings.get(batch.stop_id, 0) + take
            boarded[trip.trip_id] += take
            remaining -= take
            if remaining == 0:
                break

    return boarded


def build_optimized_plan(
    network: NetworkModel, scenario: Scenario
) -> Plan:
    """Construct and locally improve an optimized plan."""

    fleet = select_fleet(network, scenario)
    if not fleet:
        raise InfeasibleError("No eligible vehicles are available for this scenario.")

    demand = build_demand(network, scenario)
    if not demand:
        raise InfeasibleError("No measurable demand exists for this scenario.")

    window_start, window_end = _service_window(scenario)
    horizon_end = window_end + scenario.evaluationHorizonMin

    vehicle_free: dict[str, int] = {vehicle.id: window_start for vehicle in fleet}
    trips: list[PlannedTrip] = []
    counter = 0

    for batch in demand:
        route = network.route(batch.route_id)
        offset = route.offset_for(batch.stop_id)
        remaining = batch.count

        # 1) try existing trips on this route.
        for trip in [t for t in trips if t.route_id == batch.route_id]:
            if trip.departure_min + offset < batch.time_min:
                continue
            vehicle = network.vehicle(trip.vehicle_id)
            free = vehicle.capacity - trip.total_boarded
            if free <= 0:
                continue
            take = min(remaining, free)
            trip.boardings[batch.stop_id] = (
                trip.boardings.get(batch.stop_id, 0) + take
            )
            remaining -= take
            if remaining == 0:
                break

        if remaining == 0:
            continue

        # 2) dispatch new trips on the earliest available vehicle.
        for _ in range(len(fleet) + 1):
            if remaining <= 0:
                break

            best: tuple[tuple[float, int, str], object, int] | None = None
            for vehicle in fleet:
                departure = max(batch.time_min - offset, vehicle_free[vehicle.id])
                departure = _ceil_to_step(departure, DEPARTURE_STEP_MIN)
                if departure > window_end:
                    continue
                if departure + route.duration_min > horizon_end:
                    continue
                key = (departure, -vehicle.capacity, vehicle.id)
                if best is None or key < best[0]:
                    best = (key, vehicle, departure)

            if best is None:
                break

            _, vehicle, departure = best
            take = min(remaining, vehicle.capacity)
            counter += 1
            trip = PlannedTrip(
                trip_id=f"OPT-{counter:03d}",
                route_id=batch.route_id,
                vehicle_id=vehicle.id,
                departure_min=departure,
                boardings={batch.stop_id: take},
            )
            trips.append(trip)
            vehicle_free[vehicle.id] = (
                departure + route.duration_min + network.parameters.turnaroundMin
            )
            remaining -= take

    trips.sort(key=lambda t: (t.departure_min, t.route_id, t.trip_id))
    trips = _local_search_reduce(network, trips)
    trips.sort(key=lambda t: (t.departure_min, t.route_id, t.trip_id))

    return Plan(plan_id="optimized", label="Optimized plan", trips=trips)


def _local_search_reduce(
    network: NetworkModel,
    trips: list[PlannedTrip],
) -> list[PlannedTrip]:
    """Try to remove trips whose passengers can be served elsewhere.

    A trip is removed only if every passenger it planned to carry can be moved
    onto other trips without exceeding capacity or arriving before the
    passenger. This reduces distance/turnaround pressure without harming
    service; otherwise the trip is kept.
    """

    changed = True
    while changed:
        changed = False
        for candidate in sorted(trips, key=lambda t: t.total_boarded, reverse=True):
            others = [t for t in trips if t is not candidate]
            if _try_reassign(network, candidate, others):
                trips = others
                changed = True
                break
    return trips


def _try_reassign(
    network: NetworkModel,
    candidate: PlannedTrip,
    others: list[PlannedTrip],
) -> bool:
    """Check whether ``candidate``'s boardings fit on ``others`` (no mutation)."""

    route = network.route(candidate.route_id)
    # Work on copies so a failed attempt leaves the plan untouched.
    planned = {
        trip.trip_id: dict(trip.boardings) for trip in others
    }

    for stop_id, count in candidate.boardings.items():
        offset = route.offset_for(stop_id)
        remaining = count
        # Only move passengers to a trip that arrives no earlier than the
        # candidate did, so we never "un-serve" a passenger who had not yet
        # arrived when the receiving bus passed the stop.
        for trip in others:
            if trip.route_id != candidate.route_id:
                continue
            if trip.departure_min < candidate.departure_min:
                continue
            vehicle = network.vehicle(trip.vehicle_id)
            used = sum(planned[trip.trip_id].values())
            free = vehicle.capacity - used
            if free <= 0:
                continue
            take = min(remaining, free)
            planned[trip.trip_id][stop_id] = (
                planned[trip.trip_id].get(stop_id, 0) + take
            )
            remaining -= take
            if remaining == 0:
                break
        if remaining > 0:
            return False

    # Commit the reassigned boardings.
    for trip in others:
        trip.boardings = planned[trip.trip_id]
    return True
