"""Campus simulators.

Two simulators live here:

* :class:`Simulator` -- the original minimal *time-stepped* demo (kept for the
  dispatcher demo and its tests).
* :class:`DiscreteEventSimulator` and :func:`simulate` -- the plan-executing
  discrete-event engine. It consumes a :class:`Plan` and
  a :class:`Scenario`, validates the plan independently, then advances a
  ``heapq`` event queue (passenger arrivals, vehicle departures/arrivals,
  waiting deadlines, breakdowns) to produce auditable outcome metrics.

The simulator is the authority on outcomes; the optimizer only proposes actions.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional

from app.optimizer.state import BusState, OptimizationState, StopQueue
from app.schemas.network import Network
from app.schemas.plan import Plan
from app.schemas.scenario import PassengerDemand, Scenario
from app.simulation import boarding, metrics as metrics_module, travel_time
from app.simulation.events import (
    PASSENGER_ARRIVAL,
    VEHICLE_ARRIVAL,
    VEHICLE_BREAKDOWN,
    VEHICLE_DEPARTURE,
    WAITING_DEADLINE,
    EventQueue,
)
from app.simulation.models import (
    EventLogEntry,
    SimulationResult,
    VehicleHistoryEntry,
)
from app.simulation.state import (
    BROKEN_DOWN,
    IDLE,
    IN_TRANSIT,
    PassengerGroup,
    SimVehicle,
)
from app.validation.constraints import validate_plan


@dataclass
class SimBus:
    bus_id: str
    current_stop: str
    capacity: int
    status: str = "idle"                         
    target_stop: str | None = None
    remaining_min: float = 0.0


@dataclass
class SimResult:
    boarded: int = 0
    unserved: int = 0
    total_wait_min: float = 0.0
    actions: list[tuple] = field(default_factory=list)

    @property
    def avg_wait_min(self) -> float:
        return round(self.total_wait_min / self.boarded, 2) if self.boarded else 0.0


class Simulator:
    """Minimal rolling-horizon simulator (demo-grade)."""

    def __init__(self, network: Network, travel_matrix: dict[tuple[str, str], float]):
        self.network = network
        self.travel_matrix = travel_matrix
        self.buses = {
            v.vehicle_id: SimBus(v.vehicle_id, v.initial_stop_id, v.capacity)
            for v in network.vehicles
        }
        self.queues: dict[str, list[float]] = {s.stop_id: [] for s in network.stops}
        self.result = SimResult()

                                                                          
    def inject(self, arrivals: dict[str, list[float]]) -> None:
        """Inject passenger arrival times per stop."""
        for stop_id, times in arrivals.items():
            self.queues.setdefault(stop_id, []).extend(times)

    def snapshot(self, time_min: int) -> OptimizationState:
        buses = {
            b.bus_id: BusState(b.bus_id, b.current_stop, b.capacity, status=b.status)
            for b in self.buses.values()
        }
        queues = {
            s: StopQueue(s, waiting=len(self.queues.get(s, [])))
            for s in self.network.stops_by_id
        }
        return OptimizationState(
            time_min=time_min, buses=buses, queues=queues, travel_matrix=self.travel_matrix
        )

    def step(self, time_min: int, step_min: int, dispatch_fn) -> None:
        """Dispatch idle buses, then advance time and board on arrival."""
        state = self.snapshot(time_min)
        plan = dispatch_fn(state, time_min)
        for action in plan.actions:
            bus = self.buses[action.bus_id]
            if bus.status == "idle" and action.target_stop:
                bus.status = "dispatched"
                bus.target_stop = action.target_stop
                bus.remaining_min = self.travel_matrix.get(
                    (bus.current_stop, action.target_stop), float(step_min)
                )
                self.result.actions.append(
                    (time_min, action.bus_id, action.target_stop, action.reason)
                )
        self._advance(time_min + step_min, step_min)

    def run(self, horizon_min: int, step_min: int, dispatch_fn) -> SimResult:
        for t in range(0, horizon_min, step_min):
            self.step(t, step_min, dispatch_fn)
                                                             
        self.result.unserved = sum(len(q) for q in self.queues.values())
        return self.result

                                                                          
    def _advance(self, time_min: int, step_min: int) -> None:
        for bus in self.buses.values():
            if bus.status == "dispatched":
                bus.remaining_min -= step_min
                if bus.remaining_min <= 0:
                    self._arrive(bus, time_min)

    def _arrive(self, bus: SimBus, time_min: int) -> None:
        bus.current_stop = bus.target_stop or bus.current_stop
        bus.target_stop = None
        bus.status = "idle"
        queue = sorted(self.queues.get(bus.current_stop, []))
        boarded = 0
        remaining: list[float] = []
        for arrival in queue:
            if boarded < bus.capacity:
                boarded += 1
                self.result.boarded += 1
                self.result.total_wait_min += max(0.0, time_min - arrival)
            else:
                remaining.append(arrival)
        self.queues[bus.current_stop] = remaining


                                                                               
                                          
                                                                               
_DEFAULT_MAX_EVENTS = 2_000_000


def _make_run_id(scenario_id: str, plan: Plan, seed: int, start_min: int, horizon_min: int) -> str:
    """Deterministic run id for a (plan, scenario, seed, window) tuple."""
    digest = hashlib.sha1()
    digest.update(f"{scenario_id}|{seed}|{start_min}|{horizon_min}|{plan.plan_type}".encode())
    for assignment in sorted(
        plan.assignments, key=lambda a: (a.departure_min, a.trip_id, a.vehicle_id)
    ):
        digest.update(
            f"{assignment.trip_id}:{assignment.route_id}:{assignment.vehicle_id}:{assignment.departure_min}".encode()
        )
    for assignment in sorted(
        plan.extra_trips, key=lambda a: (a.departure_min, a.trip_id, a.vehicle_id)
    ):
        digest.update(
            f"X{assignment.trip_id}:{assignment.route_id}:{assignment.vehicle_id}:{assignment.departure_min}".encode()
        )
    return f"run_{plan.plan_type}_{digest.hexdigest()[:10]}"


class DiscreteEventSimulator:
    """Deterministic discrete-event execution of a :class:`Plan`.

    The simulator validates the plan first (recording the report) and then
    executes its executable assignments. Non-executable assignments (unknown
    trip/route/vehicle, unavailable vehicles, duplicates) are skipped and only
    surfaces through the validation report; the simulator never silently repairs
    a plan.
    """

    def __init__(
        self,
        network: Network,
        plan: Plan,
        scenario: Optional[Scenario] = None,
        demand: Optional[list[PassengerDemand]] = None,
        seed: int = 42,
        horizon_min: Optional[int] = None,
        start_min: Optional[int] = None,
        breakdowns: Optional[list[tuple[str, int]]] = None,
        segment_multipliers: Optional[dict[tuple[str, int], float]] = None,
        max_events: int = _DEFAULT_MAX_EVENTS,
        run_id: Optional[str] = None,
    ) -> None:
        self.network = network
        self.plan = plan
        self.scenario = scenario if scenario is not None else Scenario(scenario_id=plan.plan_type)
        self.demand = list(demand or [])
                                                                               
                                                                                
        self._demand_supplied = demand is not None
        self.seed = seed
        self.breakdowns = list(breakdowns or [])
        self.segment_multipliers = segment_multipliers or {}
        self.max_events = max_events

        self.routes = network.routes_by_id
        self.vehicles = network.vehicles_by_id
        self.canonical_trips = {t.trip_id: t for t in network.trips}
        self.unavailable = set(self.scenario.unavailable_vehicle_ids)

        self.stop_index_maps: dict[str, dict[str, int]] = {
            route.route_id: {stop_id: i for i, stop_id in enumerate(route.stop_ids)}
            for route in network.routes
        }

                                                                                 
        self.executable: list[tuple[str, str, str, int]] = []
        self._build_execution_list()

        self.horizon_min = int(
            horizon_min
            if horizon_min is not None
            else self.scenario.evaluation_horizon_min
        )
        self.start_min = self._resolve_start(start_min)
        self.end_time = self.start_min + self.horizon_min
        self.run_id = run_id or _make_run_id(
            self.scenario.scenario_id, plan, seed, self.start_min, self.horizon_min
        )

        self.queue = EventQueue()
        self.sim_vehicles: dict[str, SimVehicle] = {}
        for _trip_id, _route_id, vehicle_id, _dep in self.executable:
            vehicle = self.vehicles[vehicle_id]
            self.sim_vehicles.setdefault(
                vehicle_id,
                SimVehicle(vehicle=vehicle, current_stop_id=vehicle.initial_stop_id),
            )

        self.waiting: dict[str, list[PassengerGroup]] = {}
        self.groups: dict[str, PassengerGroup] = {}
        self.trip_status: dict[str, str] = {}
        self._pending: dict[str, object] = {}

        self.events: list[EventLogEntry] = []
        self.vehicle_histories: list[VehicleHistoryEntry] = []
        self.notes: list[str] = []
        self._truncated = False

        self.counters: dict[str, float] = {
            "total_demand": 0,
            "vehicle_km": 0.0,
            "operating_cost": 0.0,
            "cost_available": True,
            "vehicle_departures": 0,
            "vehicle_arrivals": 0,
            "capacity_violations": 0,
            "max_segment_load": 0,
            "breakdown_count": 0,
            "affected_by_breakdowns": 0,
            "missed_connections": 0,
            "eta_observations": 0,
            "eta_mae_sum": 0.0,
            "skipped_departures": 0,
        }

                                                                          
           
                                                                          
    def _build_execution_list(self) -> None:
        seen_trips: set[str] = set()
        for assignment in self.plan.assignments:
            route = self.routes.get(assignment.route_id)
            vehicle = self.vehicles.get(assignment.vehicle_id)
            if route is None or vehicle is None:
                continue
            if assignment.vehicle_id in self.unavailable:
                continue
            if assignment.trip_id in seen_trips:
                continue                                                 
            seen_trips.add(assignment.trip_id)
            self.executable.append(
                (
                    assignment.trip_id,
                    assignment.route_id,
                    assignment.vehicle_id,
                    int(assignment.departure_min),
                )
            )
        for assignment in self.plan.extra_trips:
            route = self.routes.get(assignment.route_id)
            vehicle = self.vehicles.get(assignment.vehicle_id)
            if route is None or vehicle is None:
                continue
            if assignment.vehicle_id in self.unavailable:
                continue
            self.executable.append(
                (
                    assignment.trip_id,
                    assignment.route_id,
                    assignment.vehicle_id,
                    int(assignment.departure_min),
                )
            )
        self.executable.sort(key=lambda item: (item[3], item[0], item[2]))

    def _resolve_start(self, start_min: Optional[int]) -> int:
        candidates: list[int] = [item[3] for item in self.executable]
        candidates.extend(
            int(group.arrival_time_min) for group in self.demand
        )
        if start_min is not None:
            return int(start_min)
        if not candidates:
            return 0
                                                                                
                                                      
        if self.executable:
            return min(item[3] for item in self.executable)
        return min(candidates)

    def _schedule_initial_events(self) -> None:
        for trip_id, route_id, vehicle_id, departure in self.executable:
            self.trip_status.setdefault(trip_id, "scheduled")
            if departure < self.start_min or departure > self.end_time:
                continue
            self.queue.schedule(
                departure,
                VEHICLE_DEPARTURE,
                {
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "vehicle_id": vehicle_id,
                    "stop_index": 0,
                },
            )

        for vehicle_id, time_min in self.breakdowns:
            if self.start_min <= time_min <= self.end_time and vehicle_id in self.sim_vehicles:
                self.queue.schedule(
                    time_min,
                    VEHICLE_BREAKDOWN,
                    {"vehicle_id": vehicle_id},
                )

        self._schedule_demand()

    def _schedule_demand(self) -> None:
        for group in self.demand:
            multiplier = self.scenario.demand_multipliers.get(group.origin_stop_id, 1.0)
            count = int(round(group.passenger_count * multiplier))
            if count <= 0:
                continue
            arrival = max(int(group.arrival_time_min), self.start_min)
            if arrival > self.end_time:
                continue

            demand_id = group.demand_id
            if demand_id in self.groups:
                suffix = 1
                while f"{demand_id}#{suffix}" in self.groups:
                    suffix += 1
                demand_id = f"{demand_id}#{suffix}"

            tracked = PassengerGroup(
                demand_id=demand_id,
                origin_stop_id=group.origin_stop_id,
                destination_stop_id=group.destination_stop_id,
                arrival_time_min=float(arrival),
                max_wait_min=group.max_wait_min,
                original_count=count,
                waiting=count,
                transfer_allowed=group.transfer_allowed,
            )
            self.groups[demand_id] = tracked
            self.counters["total_demand"] += count
            self.queue.schedule(
                arrival, PASSENGER_ARRIVAL, {"demand_id": demand_id}
            )
            deadline = arrival + group.max_wait_min
            if deadline <= self.end_time:
                self.queue.schedule(
                    deadline, WAITING_DEADLINE, {"demand_id": demand_id}
                )

                                                                          
              
                                                                          
    def run(self) -> SimulationResult:
        validation = validate_plan(
            self.network,
            self.plan,
            self.scenario,
            demand=self.demand if self._demand_supplied else None,
        )
        self._schedule_initial_events()

        processed = 0
        while True:
            next_time = self.queue.peek_time()
            if next_time is None or next_time > self.end_time:
                break
            event = self.queue.pop()
            processed += 1
            if processed > self.max_events:
                self.notes.append("event budget exceeded; simulation truncated")
                self._truncated = True
                break
            self._dispatch(event)

        skipped = int(self.counters.get("skipped_departures", 0))
        if skipped:
            self.notes.append(
                f"{skipped} departure(s) not executed: vehicle still on a previous "
                "trip or out of service (see validation report)"
            )
        self.notes.append(
            "passenger transfers are not modelled; missed_connections is always 0"
        )

        metrics, outcomes = metrics_module.summarize(
            self.groups, self.sim_vehicles, self.counters
        )

        return SimulationResult(
            run_id=self.run_id,
            scenario_id=self.scenario.scenario_id,
            plan_type=self.plan.plan_type,
            seed=self.seed,
            start_min=self.start_min,
            horizon_min=self.horizon_min,
            status="OK" if validation["feasible"] else "INVALID_PLAN",
            feasible=validation["feasible"],
            validation={
                "feasible": validation["feasible"],
                "hard_violation_count": validation["hard_violation_count"],
                "violations": validation["violations"],
                "unverified_constraints": validation["unverified_constraints"],
            },
            metrics=metrics,
            passenger_outcomes=outcomes,
            events=self.events,
            vehicle_histories=self.vehicle_histories,
            notes=self.notes,
        )

    def _dispatch(self, event) -> None:
        handler = {
            PASSENGER_ARRIVAL: self._on_passenger_arrival,
            VEHICLE_DEPARTURE: self._on_vehicle_departure,
            VEHICLE_ARRIVAL: self._on_vehicle_arrival,
            WAITING_DEADLINE: self._on_waiting_deadline,
            VEHICLE_BREAKDOWN: self._on_vehicle_breakdown,
        }.get(event.event_type)
        if handler is not None:
            handler(event)

                                                                          
              
                                                                          
    def _on_passenger_arrival(self, event) -> None:
        group = self.groups[event.payload["demand_id"]]
        if group.waiting <= 0:
            return
        self.waiting.setdefault(group.origin_stop_id, []).append(group)
        self._log(
            event.time_min,
            PASSENGER_ARRIVAL,
            stop_id=group.origin_stop_id,
            passengers=group.waiting,
            detail=group.demand_id,
        )

    def _on_waiting_deadline(self, event) -> None:
        group = self.groups[event.payload["demand_id"]]
        if group.waiting <= 0:
            return
        abandoned = group.waiting
        group.abandoned += abandoned
        group.waiting = 0
        self._log(
            event.time_min,
            WAITING_DEADLINE,
            stop_id=group.origin_stop_id,
            passengers=abandoned,
            detail=group.demand_id,
        )

    def _on_vehicle_departure(self, event) -> None:
        payload = event.payload
        trip_id = payload["trip_id"]
        route_id = payload["route_id"]
        vehicle_id = payload["vehicle_id"]
        stop_index = payload["stop_index"]

        if self.trip_status.get(trip_id) == "cancelled":
            return
        vehicle = self.sim_vehicles[vehicle_id]
        if vehicle.status == BROKEN_DOWN:
            self.counters["skipped_departures"] += 1
            return
        route = self.routes[route_id]
        stops = route.stop_ids
        if stop_index >= len(stops):
            return

        if stop_index == 0:
            if vehicle.status == IN_TRANSIT and vehicle.trip_id != trip_id:
                                                                               
                                                                               
                                                
                self.counters["skipped_departures"] += 1
                return
            vehicle.current_stop_id = stops[0]
        vehicle.status = IN_TRANSIT
        vehicle.trip_id = trip_id
        vehicle.route_id = route_id

        waiting = self.waiting.get(stops[stop_index], [])
        boarded = boarding.board_at_stop(
            vehicle,
            waiting,
            self.stop_index_maps[route_id],
            stop_index,
            event.time_min,
        )
        load = vehicle.load
        if load > vehicle.vehicle.capacity:
            self.counters["capacity_violations"] += 1
        self.counters["max_segment_load"] = max(self.counters["max_segment_load"], load)
        self.counters["vehicle_departures"] += 1
        self.trip_status[trip_id] = "active"

        self._log(
            event.time_min, VEHICLE_DEPARTURE, trip_id, vehicle_id,
            stops[stop_index], stop_index, passengers=boarded, load=load,
        )
        self.vehicle_histories.append(
            VehicleHistoryEntry(
                time_min=event.time_min, event="departure", vehicle_id=vehicle_id,
                trip_id=trip_id, route_id=route_id, stop_id=stops[stop_index],
                segment_index=stop_index, onboard=boarded, load=load,
            )
        )

        duration = travel_time.segment_duration_min(
            route, stop_index, self.scenario, self.segment_multipliers
        )
        pending = self.queue.schedule(
            event.time_min + duration,
            VEHICLE_ARRIVAL,
            {
                "trip_id": trip_id,
                "route_id": route_id,
                "vehicle_id": vehicle_id,
                "stop_index": stop_index + 1,
            },
        )
        self._pending[vehicle_id] = pending

    def _on_vehicle_arrival(self, event) -> None:
        payload = event.payload
        trip_id = payload["trip_id"]
        route_id = payload["route_id"]
        vehicle_id = payload["vehicle_id"]
        stop_index = payload["stop_index"]

        if self.trip_status.get(trip_id) == "cancelled":
            return
        vehicle = self.sim_vehicles[vehicle_id]
        if vehicle.trip_id != trip_id:
            return                 
        route = self.routes[route_id]
        stops = route.stop_ids
        if stop_index >= len(stops):
            return
        stop_id = stops[stop_index]
        vehicle.current_stop_id = stop_id

        segment_index = stop_index - 1
        if 0 <= segment_index < len(route.segment_distance_km):
            distance = route.segment_distance_km[segment_index]
            self.counters["vehicle_km"] += distance
            self.counters["operating_cost"] += distance * vehicle.vehicle.cost_per_km
        self._pending.pop(vehicle_id, None)

        completed = boarding.alight_at_stop(vehicle, stop_id)
        self.counters["vehicle_arrivals"] += 1
        self._log(
            event.time_min, VEHICLE_ARRIVAL, trip_id, vehicle_id,
            stop_id, segment_index, passengers=completed, load=vehicle.load,
        )
        self.vehicle_histories.append(
            VehicleHistoryEntry(
                time_min=event.time_min, event="arrival", vehicle_id=vehicle_id,
                trip_id=trip_id, route_id=route_id, stop_id=stop_id,
                segment_index=segment_index, onboard=completed, load=vehicle.load,
            )
        )

        if stop_index == len(stops) - 1:
            self.trip_status[trip_id] = "completed"
            vehicle.status = IDLE
            vehicle.trip_id = None
            vehicle.route_id = None
        else:
            self.queue.schedule(
                event.time_min,
                VEHICLE_DEPARTURE,
                {
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "vehicle_id": vehicle_id,
                    "stop_index": stop_index,
                },
            )

    def _on_vehicle_breakdown(self, event) -> None:
        vehicle_id = event.payload["vehicle_id"]
        vehicle = self.sim_vehicles.get(vehicle_id)
        if vehicle is None or vehicle.status == BROKEN_DOWN:
            return
        vehicle.status = BROKEN_DOWN
        self.counters["breakdown_count"] += 1

        pending = self._pending.pop(vehicle_id, None)
        if pending is not None:
            self.queue.cancel(pending)
        if vehicle.trip_id is not None:
            self.trip_status[vehicle.trip_id] = "cancelled"

        onboard = vehicle.load
        if onboard:
            self.counters["affected_by_breakdowns"] += onboard
        self._log(
            event.time_min, VEHICLE_BREAKDOWN, vehicle.trip_id, vehicle_id,
            vehicle.current_stop_id, passengers=onboard, load=onboard,
        )
        self.vehicle_histories.append(
            VehicleHistoryEntry(
                time_min=event.time_min, event="breakdown", vehicle_id=vehicle_id,
                trip_id=vehicle.trip_id, route_id=vehicle.route_id,
                stop_id=vehicle.current_stop_id, onboard=onboard, load=onboard,
            )
        )
        vehicle.trip_id = None
        vehicle.route_id = None

                                                                          
             
                                                                          
    def _log(self, time_min, event_type, trip_id=None, vehicle_id=None,
             stop_id=None, segment_index=None, passengers=None, load=None,
             detail=None) -> None:
        self.events.append(
            EventLogEntry(
                time_min=time_min,
                event_type=event_type,
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                stop_id=stop_id,
                segment_index=segment_index,
                passengers=passengers,
                load=load,
                detail=detail,
            )
        )


def simulate(
    network: Network,
    plan: Plan,
    scenario: Optional[Scenario] = None,
    demand: Optional[list[PassengerDemand]] = None,
    seed: int = 42,
    horizon_min: Optional[int] = None,
    start_min: Optional[int] = None,
    breakdowns: Optional[list[tuple[str, int]]] = None,
    segment_multipliers: Optional[dict[tuple[str, int], float]] = None,
    run_id: Optional[str] = None,
) -> SimulationResult:
    """Validate and simulate ``plan``; return a structured, auditable result.

    The canonical :class:`Scenario` schema has no timed-breakdown field, so
    timed failures are supplied via ``breakdowns`` (``(vehicle_id, time_min)``);
    whole-scenario vehicle removal uses ``Scenario.unavailable_vehicle_ids``.
    Segment-level travel-time multipliers use ``segment_multipliers``.
    """
    return DiscreteEventSimulator(
        network=network,
        plan=plan,
        scenario=scenario,
        demand=demand,
        seed=seed,
        horizon_min=horizon_min,
        start_min=start_min,
        breakdowns=breakdowns,
        segment_multipliers=segment_multipliers,
        run_id=run_id,
    ).run()
