"""Vehicle assignment and dispatch (greedy baseline optimizer).

The game plan specifies OR-Tools CP-SAT as the final solver; this greedy
dispatcher is the deterministic, dependency-free baseline it recommends
building first. It:

1. starts from the original timetable,
2. reassigns trips whose assigned vehicle is unavailable (or already busy) to a
   spare compatible vehicle, respecting the availability window, turnaround and
   non-overlapping trips,
3. honours each vehicle's ``initial_stop_id``: a vehicle's first trip must
   start where the vehicle actually is, which is what the independent validator
   checks,
4. optionally adds extra dispatches for stops the prediction engine flags as
   HIGH crowding risk,
5. returns a Plan for the validator / simulator / API to consume.

Two hard constraints drive the design:

* **Service headways** are per-route min/max gaps between *consecutive assigned
  departures*. To keep them satisfiable the optimizer holds departures at their
  scheduled values (any scenario vehicle-delay retiming is applied only when it
  leaves the whole route inside its headway bounds) instead of nudging trips,
  and it always tries to assign every trip, because a dropped trip widens the
  gap around it.
* **Vehicle initial position** limits where a fleet can start. Vehicles are
  therefore ranked so a route draws on its own depot vehicles first, rather
  than stealing another route's only starting vehicle.
"""
from __future__ import annotations

from typing import Optional

from app.prediction.predictor import PredictionOutput
from app.schemas.network import Network, Route, Trip, Vehicle
from app.schemas.plan import Plan, TripAssignment
from app.schemas.scenario import Scenario


def route_duration_min(route: Route) -> float:
    return sum(route.segment_travel_min)


def _duration_min(route: Route, scenario: Scenario) -> float:
    """Trip duration exactly as the validator computes it."""
    return route_duration_min(route) * scenario.travel_time_multipliers.get(
        route.route_id, 1.0
    )


def _fits_availability(v: Vehicle, dep: float, end: float) -> bool:
    return dep >= v.available_from_min and end <= v.available_until_min


def _overlaps(busy: dict[str, list[tuple[float, float]]], vid: str, start: float, end: float) -> bool:
    return any(start < e and s < end for s, e in busy.get(vid, []))


def _can_assign(vid: str, dep: float, end: float, vehicles: dict[str, Vehicle],
                busy: dict[str, list[tuple[float, float]]]) -> bool:
    v = vehicles[vid]
    return _fits_availability(v, dep, end) and not _overlaps(busy, vid, dep, end)


def _mark_busy(busy: dict[str, list[tuple[float, float]]], vid: str,
               start: float, end: float, turnaround: int) -> None:
    busy.setdefault(vid, []).append((start, end + turnaround))


def _headway_ok(route: Route, existing: list[float], dep: float) -> bool:
    """Would inserting ``dep`` keep every route gap inside ``[min, max]``?"""
    for other in existing:
        gap = abs(dep - other)
        if gap < route.min_headway_min or gap > route.max_headway_min:
            return False
    return True


def _depot_vehicles(network: Network) -> dict[str, set[str]]:
    """Vehicle ids whose ``initial_stop_id`` equals their route's start stop."""
    vehicles = network.vehicles_by_id
    return {
        route.route_id: {
            v.vehicle_id for v in vehicles.values()
            if v.initial_stop_id == route.stop_ids[0]
        }
        for route in network.routes
    }


def _resolve_departures(network: Network, scenario: Scenario) -> dict[str, float]:
    """Service departure per trip, stable under scenario vehicle delays.

    Delays are only honoured while they leave the trip inside its own
    departure window *and* leave every consecutive gap on the route within the
    route's headway bounds; otherwise the scheduled time stands.
    """
    delays = scenario.vehicle_delays_min
    departure: dict[str, float] = {}
    for trip in network.trips:
        planned = float(trip.planned_departure_min)
        delayed = planned + delays.get(trip.vehicle_id, 0)
        if trip.departure_window_start_min <= delayed <= trip.departure_window_end_min:
            departure[trip.trip_id] = delayed
        else:
            departure[trip.trip_id] = planned

    for route in network.routes:
        route_trips = [t for t in network.trips if t.route_id == route.route_id]
        route_trips.sort(key=lambda t: (departure[t.trip_id], t.trip_id))
        for previous, current in zip(route_trips, route_trips[1:]):
            gap = departure[current.trip_id] - departure[previous.trip_id]
            if gap < route.min_headway_min or gap > route.max_headway_min:
                for trip in route_trips:
                    departure[trip.trip_id] = float(trip.planned_departure_min)
                break
    return departure


def _extra_dispatches(network: Network, scenario: Scenario,
                      prediction: Optional[PredictionOutput],
                      busy: dict[str, list[tuple[float, float]]],
                      departures: dict[str, list[float]],
                      scheduled: dict[str, list[float]]) -> list[TripAssignment]:
    """Add dispatches for stops the prediction engine flags as HIGH crowding risk.

    An extra trip is only added when it can slot into the route's service
    headway; otherwise the scheduled service would be broken.
    """
    if prediction is None:
        return []
    unavailable = set(scenario.unavailable_vehicle_ids)
    vehicles = network.vehicles_by_id
    routes = network.routes_by_id
    extra: list[TripAssignment] = []
    high = sorted(
        (f for f in prediction.stop_forecasts if f.crowding_risk == "HIGH"),
        key=lambda f: -f.capacity_shortfall,
    )
    for f in high:
        route = _route_serving_stop(routes, f.stop_id)
        if route is None:
            continue
        dep = float(f.time_bucket_min)
        known = departures.get(route.route_id, []) + scheduled.get(route.route_id, [])
        if not _headway_ok(route, known, dep):
            continue
        duration = _duration_min(route, scenario)
        for vid, v in vehicles.items():
            if vid in unavailable or v.vehicle_type not in route.allowed_vehicle_types:
                continue
            if _can_assign(vid, dep, dep + duration, vehicles, busy):
                extra.append(TripAssignment(
                    trip_id=f"X_{f.stop_id}",
                    route_id=route.route_id,
                    vehicle_id=vid,
                    departure_min=int(dep),
                ))
                _mark_busy(busy, vid, dep, dep + duration, v.turnaround_min)
                departures.setdefault(route.route_id, []).append(dep)
                break
    return extra


def _route_serving_stop(routes: dict[str, Route], stop_id: str) -> Optional[Route]:
    for r in routes.values():
        if stop_id in r.stop_ids:
            return r
    return None


def optimize(network: Network, scenario: Scenario,
             prediction: Optional[PredictionOutput] = None,
             time_limit_seconds: Optional[int] = None) -> Plan:
    """Greedy vehicle-assignment optimizer (baseline).

    ``prediction`` enables extra dispatches for predicted-crowded stops.
    ``time_limit_seconds`` is accepted for API parity (the greedy solver is
    effectively instant and does not use it).
    """
    unavailable = set(scenario.unavailable_vehicle_ids)
    vehicles = network.vehicles_by_id
    routes = network.routes_by_id
    departure = _resolve_departures(network, scenario)

    depot = _depot_vehicles(network)
    route_used: dict[str, set[str]] = {rid: set() for rid in routes}
    busy: dict[str, list[tuple[float, float]]] = {vid: [] for vid in vehicles}
    started: set[str] = set()
    departures: dict[str, list[float]] = {rid: [] for rid in routes}
    scheduled: dict[str, list[float]] = {rid: [] for rid in routes}
    for trip in network.trips:
        scheduled[trip.route_id].append(departure[trip.trip_id])

    assignments: list[TripAssignment] = []
    unassigned: list[str] = []

    trips = sorted(network.trips, key=lambda t: (departure[t.trip_id], t.trip_id))
    for trip in trips:
        route = routes[trip.route_id]
        rid = trip.route_id
        duration = _duration_min(route, scenario)
        dep = departure[trip.trip_id]
        end = dep + duration

        def usable(vid: str) -> bool:
            v = vehicles[vid]
            if vid in unavailable or v.vehicle_type not in route.allowed_vehicle_types:
                return False
            if not _can_assign(vid, dep, end, vehicles, busy):
                return False
                                                                              
            if vid not in started and route.stop_ids and route.stop_ids[0] != v.initial_stop_id:
                return False
            return True

        def rank(vid: str) -> tuple[int, str]:
            if vid == trip.vehicle_id:
                return (0, vid)
            if vid in route_used[rid]:
                return (1, vid)
            if vid in depot[rid] and vid not in started:
                return (2, vid)
            return (3, vid)

        chosen = min((vid for vid in vehicles if usable(vid)), key=rank, default=None)
        if chosen is None:
            unassigned.append(trip.trip_id)
            continue

        v = vehicles[chosen]
        _mark_busy(busy, chosen, dep, end, v.turnaround_min)
        started.add(chosen)
        route_used[rid].add(chosen)
        departures[rid].append(dep)
        assignments.append(TripAssignment(
            trip_id=trip.trip_id, route_id=trip.route_id,
            vehicle_id=chosen, departure_min=int(dep),
        ))

    extra = _extra_dispatches(network, scenario, prediction, busy, departures, scheduled)

    status = "OK" if not unassigned else "PARTIAL"
    return Plan(
        plan_type="optimized",
        assignments=assignments,
        extra_trips=extra,
        unassigned_trip_ids=unassigned,
        solver_status=status,
    )
