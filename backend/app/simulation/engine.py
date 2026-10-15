"""Deterministic discrete-event simulation of a plan.

Given a plan (a list of dispatched trips), the seed demand, and the scenario,
the engine replays the operating window:

  * passengers wait at their stop until a trip on a serving route arrives with
    free capacity (FIFO boarding),
  * travel times are scaled by a deterministic congestion factor derived from
    demand volume, so the same demand produces the same result every run,
  * leftover passengers are classified as either *missed connections* (no trip
    served the stop at/after their arrival) or *capacity denied* (a trip did
    pass, but it was full).

The engine does not inspect the optimizer's own boardings; it re-derives the
outcome, which is what makes the evaluation independent.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from app.optimizer.model import DemandBatch, NetworkModel, Plan, parse_period
from app.schemas.scenario import Scenario
from app.simulation.boarding import board_waiting
from app.simulation.events import Passenger, congestion_factor, expand_passengers


@dataclass
class TripSim:
    trip_id: str
    route_id: str
    vehicle_id: str
    departure_min: float
    terminal_arrival_min: float
    boardings: dict[str, int]
    onboard_peak: int
    ride_passenger_minutes: float
    distance_km: float
    completed: bool


@dataclass
class VehicleStats:
    vehicle_id: str
    capacity: int
    trips: int = 0
    boarded: int = 0
    ride_passenger_minutes: float = 0.0
    capacity_minutes: float = 0.0

    @property
    def utilization_percent(self) -> float:
        if self.capacity_minutes <= 0:
            return 0.0
        value = 100.0 * self.ride_passenger_minutes / self.capacity_minutes
        return round(min(100.0, max(0.0, value)), 1)


@dataclass
class SimulationResult:
    label: str
    trips: list[TripSim]
    served: int
    unserved: int
    missed_connections: int
    capacity_denied: int
    total_wait_min: float
    total_travel_min: float
    distance_km: float
    total_demand: int
    eta_abs_errors: list[float] = field(default_factory=list)
    eta_within_3: int = 0
    eta_points: int = 0
    vehicle_stats: dict[str, VehicleStats] = field(default_factory=dict)

    @property
    def average_wait_min(self) -> float:
        if self.served <= 0:
            return 0.0
        return round(self.total_wait_min / self.served, 2)

    @property
    def unserved_rate(self) -> float:
        if self.total_demand <= 0:
            return 0.0
        return round(100.0 * self.unserved / self.total_demand, 1)

    @property
    def eta_mae(self) -> float:
        if not self.eta_abs_errors:
            return 0.0
        return round(sum(self.eta_abs_errors) / len(self.eta_abs_errors), 2)

    @property
    def eta_within_3_percent(self) -> float:
        if self.eta_points <= 0:
            return 0.0
        return round(100.0 * self.eta_within_3 / self.eta_points, 1)


def simulate(
    network: NetworkModel,
    scenario: Scenario,
    plan: Plan,
    demand: list[DemandBatch],
) -> SimulationResult:
    """Replay ``plan`` against ``demand`` and return measured outcomes."""

    passengers = expand_passengers(demand)
    total_demand = len(passengers)

    waiting_by_stop: dict[str, deque[Passenger]] = defaultdict(deque)
    for passenger in passengers:
        waiting_by_stop[passenger.stop_id].append(passenger)

    window_end = parse_period(scenario.affectedPeriod)[1]
    horizon_end = window_end + scenario.evaluationHorizonMin

    max_arrival_by_stop: dict[str, float] = {}
    trips_sorted = sorted(plan.trips, key=lambda t: (t.departure_min, t.trip_id))

    trips_sim: list[TripSim] = []
    vehicle_stats: dict[str, VehicleStats] = {}
    eta_abs_errors: list[float] = []
    eta_within_3 = 0
    served = 0
    total_wait = 0.0
    total_travel = 0.0
    distance = 0.0

    for trip in trips_sorted:
        route = network.route(trip.route_id)
        vehicle = network.vehicle(trip.vehicle_id)
        factor = congestion_factor(demand, trip.departure_min)
        actual_offsets = [offset * factor for offset in route.offsets_min]
        terminal_arrival = trip.departure_min + actual_offsets[-1]

        onboard = 0
        onboard_peak = 0
        ride_minutes = 0.0
        boardings: dict[str, int] = {}

        for index, stop_id in enumerate(route.stop_ids[:-1]):
            arrival = trip.departure_min + actual_offsets[index]
            boarded = board_waiting(
                waiting_by_stop[stop_id], arrival, onboard, vehicle.capacity
            )
            if boarded:
                boardings[stop_id] = len(boarded)
                for passenger in boarded:
                    total_wait += max(0.0, arrival - passenger.arrival_min)
                    ride_minutes += max(0.0, terminal_arrival - arrival)
                    served += 1
                    onboard += 1
                onboard_peak = max(onboard_peak, onboard)

            # Record the latest time a bus was present at this stop (whether or
            # not passengers boarded), used to classify unserved passengers.
            if arrival > max_arrival_by_stop.get(stop_id, float("-inf")):
                max_arrival_by_stop[stop_id] = arrival

            predicted = trip.departure_min + route.offsets_min[index]
            error = abs(arrival - predicted)
            eta_abs_errors.append(error)
            if error <= 3.0:
                eta_within_3 += 1

        completed = terminal_arrival <= horizon_end + 1e-9
        total_travel += actual_offsets[-1]
        distance += route.distance_km

        trips_sim.append(
            TripSim(
                trip_id=trip.trip_id,
                route_id=trip.route_id,
                vehicle_id=trip.vehicle_id,
                departure_min=float(trip.departure_min),
                terminal_arrival_min=terminal_arrival,
                boardings=boardings,
                onboard_peak=onboard_peak,
                ride_passenger_minutes=round(ride_minutes, 3),
                distance_km=route.distance_km,
                completed=completed,
            )
        )

        stats = vehicle_stats.setdefault(
            trip.vehicle_id,
            VehicleStats(vehicle_id=trip.vehicle_id, capacity=vehicle.capacity),
        )
        stats.trips += 1
        stats.boarded += sum(boardings.values())
        stats.ride_passenger_minutes += ride_minutes
        stats.capacity_minutes += vehicle.capacity * actual_offsets[-1]

    # Classify passengers who never boarded.
    missed_connections = 0
    capacity_denied = 0
    for stop_id, waiting in waiting_by_stop.items():
        last_service = max_arrival_by_stop.get(stop_id, float("-inf"))
        for passenger in waiting:
            if passenger.arrival_min > last_service:
                missed_connections += 1
            else:
                capacity_denied += 1

    unserved = missed_connections + capacity_denied

    return SimulationResult(
        label=plan.label,
        trips=trips_sim,
        served=served,
        unserved=unserved,
        missed_connections=missed_connections,
        capacity_denied=capacity_denied,
        total_wait_min=round(total_wait, 3),
        total_travel_min=round(total_travel, 3),
        distance_km=round(distance, 3),
        total_demand=total_demand,
        eta_abs_errors=eta_abs_errors,
        eta_within_3=eta_within_3,
        eta_points=len(eta_abs_errors),
        vehicle_stats=vehicle_stats,
    )
