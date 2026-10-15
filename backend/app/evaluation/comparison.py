"""Compare baseline and optimized plans under equivalent conditions."""

from __future__ import annotations

from app.evaluation.metrics import LOWER_IS_BETTER, PlanMetrics
from app.schemas.evaluation import (
    EtaWithinThree,
    FleetUtilization,
    PassengerOutcome,
    PerformanceMetric,
    PerformanceMetrics,
)
from app.schemas.optimization import MetricDifference
from app.simulation.engine import SimulationResult


def _metric(baseline: float, optimized: float, unit: str, lower: bool) -> PerformanceMetric:
    return PerformanceMetric(
        baseline=round(float(baseline), 2),
        optimized=round(float(optimized), 2),
        unit=unit,  # type: ignore[arg-type]
        lowerIsBetter=lower,
    )


def build_performance_metrics(
    baseline: PlanMetrics, optimized: PlanMetrics
) -> PerformanceMetrics:
    """Assemble the frontend PerformanceMetrics comparison table."""

    return PerformanceMetrics(
        averageWaitingTime=_metric(
            baseline.average_waiting_time_min,
            optimized.average_waiting_time_min,
            "min",
            LOWER_IS_BETTER["averageWaitingTime"],
        ),
        unservedPassengers=_metric(
            baseline.unserved_passengers,
            optimized.unserved_passengers,
            "passengers",
            LOWER_IS_BETTER["unservedPassengers"],
        ),
        missedConnections=_metric(
            baseline.missed_connections,
            optimized.missed_connections,
            "passengers",
            LOWER_IS_BETTER["missedConnections"],
        ),
        etaMae=_metric(
            baseline.eta_mae, optimized.eta_mae, "min", LOWER_IS_BETTER["etaMae"]
        ),
        unservedRate=_metric(
            baseline.unserved_rate,
            optimized.unserved_rate,
            "percent",
            LOWER_IS_BETTER["unservedRate"],
        ),
        capacityViolations=_metric(
            baseline.capacity_violations,
            optimized.capacity_violations,
            "passengers",
            LOWER_IS_BETTER["capacityViolations"],
        ),
        vehicleDistance=_metric(
            baseline.vehicle_distance_km,
            optimized.vehicle_distance_km,
            "km",
            LOWER_IS_BETTER["vehicleDistance"],
        ),
    )


def build_differences(
    baseline: PlanMetrics, optimized: PlanMetrics
) -> list[MetricDifference]:
    rows = [
        ("averageWaitingTime", baseline.average_waiting_time_min, optimized.average_waiting_time_min),
        ("unservedPassengers", baseline.unserved_passengers, optimized.unserved_passengers),
        ("missedConnections", baseline.missed_connections, optimized.missed_connections),
        ("etaMae", baseline.eta_mae, optimized.eta_mae),
        ("unservedRate", baseline.unserved_rate, optimized.unserved_rate),
        ("capacityViolations", baseline.capacity_violations, optimized.capacity_violations),
        ("vehicleDistance", baseline.vehicle_distance_km, optimized.vehicle_distance_km),
    ]

    differences: list[MetricDifference] = []
    for name, base, opt in rows:
        lower = LOWER_IS_BETTER[name]
        difference = round(float(opt) - float(base), 2)
        improved = difference < 0 if lower else difference > 0
        differences.append(
            MetricDifference(
                metric=name,
                baseline=round(float(base), 2),
                optimized=round(float(opt), 2),
                difference=difference,
                lowerIsBetter=lower,
                improved=improved and difference != 0,
            )
        )
    return differences


def build_passenger_outcome(
    baseline: SimulationResult, optimized: SimulationResult
) -> PassengerOutcome:
    return PassengerOutcome(
        total=optimized.total_demand,
        baselineServed=baseline.served,
        baselineUnserved=baseline.unserved,
        optimizedServed=optimized.served,
        optimizedUnserved=optimized.unserved,
    )


def build_fleet_utilization(
    baseline: SimulationResult, optimized: SimulationResult
) -> list[FleetUtilization]:
    vehicle_ids = sorted(
        set(baseline.vehicle_stats) | set(optimized.vehicle_stats)
    )
    result: list[FleetUtilization] = []
    for vehicle_id in vehicle_ids:
        base = baseline.vehicle_stats.get(vehicle_id)
        opt = optimized.vehicle_stats.get(vehicle_id)
        result.append(
            FleetUtilization(
                vehicleId=vehicle_id,
                baseline=base.utilization_percent if base else 0.0,
                optimized=opt.utilization_percent if opt else 0.0,
            )
        )
    return result


def build_eta_within_three(
    baseline: SimulationResult, optimized: SimulationResult
) -> EtaWithinThree:
    return EtaWithinThree(
        baseline=baseline.eta_within_3_percent,
        optimized=optimized.eta_within_3_percent,
    )


def build_key_finding(
    baseline: PlanMetrics, optimized: PlanMetrics, scenario_name: str
) -> str:
    """Generate a data-derived summary sentence (never hardcoded)."""

    parts: list[str] = []

    unserved_delta = baseline.unserved_passengers - optimized.unserved_passengers
    if unserved_delta > 0:
        parts.append(
            f"served {unserved_delta} more passenger(s) than the baseline"
        )
    elif unserved_delta < 0:
        parts.append(
            f"left {abs(unserved_delta)} more passenger(s) unserved than the baseline"
        )
    else:
        parts.append("matched the baseline on unserved passengers")

    wait_delta = baseline.average_waiting_time_min - optimized.average_waiting_time_min
    if abs(wait_delta) >= 0.05:
        direction = "reduced" if wait_delta > 0 else "increased"
        parts.append(
            f"{direction} average waiting time by {abs(wait_delta):.1f} min "
            f"({baseline.average_waiting_time_min:.1f} -> "
            f"{optimized.average_waiting_time_min:.1f})"
        )

    distance_delta = optimized.vehicle_distance_km - baseline.vehicle_distance_km
    if distance_delta > 0.05:
        parts.append(
            f"at the cost of {distance_delta:.1f} extra vehicle-km"
        )

    return f"Under the {scenario_name} scenario, the optimized plan " + "; ".join(
        parts
    ) + "."
