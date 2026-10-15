"""Turn a raw simulation result into reportable metrics.

Every field here is derived from the simulation output; nothing is hardcoded.
Units and direction (higher/lower is better) are documented where consumed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.optimizer.model import Plan
from app.schemas.optimization import OptimizationMetrics
from app.simulation.engine import SimulationResult

# Metrics where a lower value is better (used for the comparison view).
LOWER_IS_BETTER = {
    "averageWaitingTime": True,
    "unservedPassengers": True,
    "missedConnections": True,
    "etaMae": True,
    "unservedRate": True,
    "capacityViolations": True,
    "vehicleDistance": True,
}


@dataclass
class PlanMetrics:
    average_waiting_time_min: float
    unserved_passengers: int
    missed_connections: int
    vehicle_distance_km: float
    unserved_rate: float
    capacity_violations: int
    eta_mae: float
    eta_within_3_percent: float
    served: int
    total_demand: int
    total_travel_min: float
    trips_completed: int
    trips_total: int
    fleet_utilization: dict[str, float] = field(default_factory=dict)

    def to_optimization_metrics(self) -> OptimizationMetrics:
        return OptimizationMetrics(
            averageWaitingTimeMin=self.average_waiting_time_min,
            unservedPassengers=self.unserved_passengers,
            missedConnections=self.missed_connections,
            vehicleDistanceKm=self.vehicle_distance_km,
        )


def compute_plan_metrics(sim: SimulationResult, plan: Plan) -> PlanMetrics:
    """Compute metrics for a single simulated plan."""

    trips_completed = sum(1 for trip in sim.trips if trip.completed)

    return PlanMetrics(
        average_waiting_time_min=sim.average_wait_min,
        unserved_passengers=sim.unserved,
        missed_connections=sim.missed_connections,
        vehicle_distance_km=sim.distance_km,
        unserved_rate=sim.unserved_rate,
        capacity_violations=sim.capacity_denied,
        eta_mae=sim.eta_mae,
        eta_within_3_percent=sim.eta_within_3_percent,
        served=sim.served,
        total_demand=sim.total_demand,
        total_travel_min=sim.total_travel_min,
        trips_completed=trips_completed,
        trips_total=len(plan.trips),
        fleet_utilization={
            vehicle_id: stats.utilization_percent
            for vehicle_id, stats in sim.vehicle_stats.items()
        },
    )
