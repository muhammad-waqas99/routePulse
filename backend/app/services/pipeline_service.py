"""End-to-end optimization pipeline.

Flow for a scenario:

    load network + scenario
      -> build baseline plan (published timetable, pruned for disruptions)
      -> construct optimized plan (heuristic + local search)
      -> validate the optimized plan independently
      -> simulate baseline and optimized plans under identical demand
      -> compute metrics, compare, persist an evaluation run
      -> return the response envelope

The result is never asserted to be good; every number comes from the steps
above.
"""

from __future__ import annotations

from app.evaluation.comparison import (
    build_differences,
    build_eta_within_three,
    build_fleet_utilization,
    build_key_finding,
    build_passenger_outcome,
    build_performance_metrics,
)
from app.evaluation.metrics import compute_plan_metrics
from app.optimizer.model import NetworkModel, Plan, format_time
from app.optimizer.solve import (
    InfeasibleError,
    assign_existing_boardings,
    build_baseline_plan,
    build_optimized_plan,
)
from app.schemas.evaluation import PerformanceRun
from app.schemas.optimization import (
    OptimizeResponse,
    PlanSummary,
    SimulationSummary,
    TimetableTrip,
    ValidationResult,
)
from app.schemas.scenario import Scenario
from app.services import operations_service, run_store
from app.services.scenario_service import get_scenario
from app.simulation.engine import SimulationResult, simulate
from app.validation.constraints import validate_plan


def _to_timetable_trips(plan: Plan) -> list[TimetableTrip]:
    return [
        TimetableTrip(
            tripId=trip.trip_id,
            routeId=trip.route_id,
            vehicleId=trip.vehicle_id,
            departureTime=format_time(trip.departure_min),
        )
        for trip in sorted(plan.trips, key=lambda t: (t.departure_min, t.trip_id))
    ]


def _plan_summary(network: NetworkModel, plan: Plan) -> PlanSummary:
    distance = sum(network.route(trip.route_id).distance_km for trip in plan.trips)
    return PlanSummary(
        label=plan.label,
        trips=_to_timetable_trips(plan),
        totalTrips=len(plan.trips),
        vehiclesUsed=sorted({trip.vehicle_id for trip in plan.trips}),
        totalDistanceKm=round(distance, 2),
    )


def _simulation_summary(
    sim: SimulationResult, plan: Plan, metrics
) -> SimulationSummary:
    return SimulationSummary(
        label=plan.label,
        servedPassengers=sim.served,
        unservedPassengers=sim.unserved,
        missedConnections=sim.missed_connections,
        capacityDeniedPassengers=sim.capacity_denied,
        averageWaitingTimeMin=sim.average_wait_min,
        tripsCompleted=metrics.trips_completed,
        tripsTotal=metrics.trips_total,
        vehicleDistanceKm=sim.distance_km,
        totalTravelTimeMin=sim.total_travel_min,
        capacityViolations=sim.capacity_denied,
    )


def _infeasible_response(
    scenario: Scenario, reason: str
) -> tuple[OptimizeResponse, PerformanceRun]:
    """Build a structured failure response (never a fake success)."""

    run_id = run_store.next_run_id()
    run = PerformanceRun(
        runId=run_id,
        scenarioId=scenario.id,
        scenarioName=scenario.name,
        status="infeasible",
        createdAt=run_store.now_iso(),
    )

    empty_plan = PlanSummary(
        label="No feasible plan",
        trips=[],
        totalTrips=0,
        vehiclesUsed=[],
        totalDistanceKm=0.0,
    )
    failed_validation = ValidationResult(
        valid=False,
        hardViolationCount=6,
        constraints=[
            {"id": cid, "label": label, "passed": False, "detail": reason}  # type: ignore[arg-type]
            for cid, label in [
                ("vehicle-assignment", "Vehicle assignment"),
                ("vehicle-availability", "Vehicle availability"),
                ("departure-windows", "Departure windows"),
                ("vehicle-turnaround", "Vehicle turnaround"),
                ("segment-capacity", "Segment capacity"),
                ("transfer-buffer", "Transfer buffer"),
            ]
        ],
    )

    response = OptimizeResponse(
        status="infeasible",
        originalTrips=[],
        proposedTrips=[],
        totalTrips=0,
        constraints=failed_validation.constraints,
        hardViolationCount=failed_validation.hardViolationCount,
        metrics={
            "averageWaitingTimeMin": 0.0,
            "unservedPassengers": 0,
            "missedConnections": 0,
            "vehicleDistanceKm": 0.0,
        },
        runId=run_id,
        scenarioId=scenario.id,
        scenarioName=scenario.name,
        message=f"No feasible plan could be produced: {reason}",
        baselinePlan=empty_plan,
        optimizedPlan=empty_plan,
        validation=failed_validation,
        simulation={},
        baselineMetrics={
            "averageWaitingTimeMin": 0.0,
            "unservedPassengers": 0,
            "missedConnections": 0,
            "vehicleDistanceKm": 0.0,
        },
        optimizedMetrics={
            "averageWaitingTimeMin": 0.0,
            "unservedPassengers": 0,
            "missedConnections": 0,
            "vehicleDistanceKm": 0.0,
        },
        differences=[],
        warnings=[reason],
    )
    return response, run


def run_optimization(scenario_id: str) -> OptimizeResponse:
    """Run the full pipeline for a scenario id and persist the run."""

    scenario = get_scenario(scenario_id)
    network = operations_service.get_network_model()

    try:
        optimized_plan = build_optimized_plan(network, scenario)
    except InfeasibleError as exc:
        response, run = _infeasible_response(scenario, str(exc))
        run_store.save_run(run)
        return response

    baseline_plan = build_baseline_plan(network, scenario)
    demand = _demand_for(network, scenario)

    # Baseline boardings are derived (not trusted) purely so the plan is
    # self-consistent if it is ever validated.
    assign_existing_boardings(network, demand, baseline_plan.trips)

    baseline_sim = simulate(network, scenario, baseline_plan, demand)
    optimized_sim = simulate(network, scenario, optimized_plan, demand)

    baseline_metrics = compute_plan_metrics(baseline_sim, baseline_plan)
    optimized_metrics = compute_plan_metrics(optimized_sim, optimized_plan)

    validation = validate_plan(network, scenario, optimized_plan)

    if not validation.valid:
        status = "infeasible"
    elif optimized_sim.unserved == 0 and optimized_sim.capacity_denied == 0:
        status = "optimal"
    else:
        status = "feasible"

    warnings: list[str] = []
    if optimized_sim.unserved > 0:
        warnings.append(
            f"{optimized_sim.unserved} passenger(s) could not be served within "
            "the operating window and available fleet."
        )
    if not validation.valid:
        warnings.append("The optimized plan failed independent validation.")

    run_id = run_store.next_run_id()

    response = OptimizeResponse(
        status=status,  # type: ignore[arg-type]
        originalTrips=_to_timetable_trips(baseline_plan),
        proposedTrips=_to_timetable_trips(optimized_plan),
        totalTrips=len(optimized_plan.trips),
        constraints=validation.constraints,
        hardViolationCount=validation.hardViolationCount,
        metrics=optimized_metrics.to_optimization_metrics(),
        runId=run_id,
        scenarioId=scenario.id,
        scenarioName=scenario.name,
        message=(
            "Optimization completed and the plan passed independent validation."
            if validation.valid
            else "Optimization produced a plan that failed validation."
        ),
        baselinePlan=_plan_summary(network, baseline_plan),
        optimizedPlan=_plan_summary(network, optimized_plan),
        validation=validation,
        simulation={
            "baseline": _simulation_summary(baseline_sim, baseline_plan, baseline_metrics),
            "optimized": _simulation_summary(
                optimized_sim, optimized_plan, optimized_metrics
            ),
        },
        baselineMetrics=baseline_metrics.to_optimization_metrics(),
        optimizedMetrics=optimized_metrics.to_optimization_metrics(),
        differences=build_differences(baseline_metrics, optimized_metrics),
        warnings=warnings,
    )

    performance = build_performance_run(
        run_id=run_id,
        scenario=scenario,
        status="completed" if validation.valid else "infeasible",
        baseline_sim=baseline_sim,
        optimized_sim=optimized_sim,
        baseline_metrics=baseline_metrics,
        optimized_metrics=optimized_metrics,
    )
    run_store.save_run(performance)

    return response


def _demand_for(network: NetworkModel, scenario: Scenario):
    from app.optimizer.model import build_demand

    return build_demand(network, scenario)


def build_performance_run(
    run_id: str,
    scenario: Scenario,
    status: str,
    baseline_sim: SimulationResult,
    optimized_sim: SimulationResult,
    baseline_metrics,
    optimized_metrics,
) -> PerformanceRun:
    """Assemble the Performance Lab payload for a completed run."""

    if status != "completed":
        return PerformanceRun(
            runId=run_id,
            scenarioId=scenario.id,
            scenarioName=scenario.name,
            status="infeasible",
            createdAt=run_store.now_iso(),
        )

    return PerformanceRun(
        runId=run_id,
        scenarioId=scenario.id,
        scenarioName=scenario.name,
        status="completed",
        createdAt=run_store.now_iso(),
        metrics=build_performance_metrics(baseline_metrics, optimized_metrics),
        passengerOutcome=build_passenger_outcome(baseline_sim, optimized_sim),
        fleetUtilization=build_fleet_utilization(baseline_sim, optimized_sim),
        etaWithinThreeMinutes=build_eta_within_three(baseline_sim, optimized_sim),
        keyFinding=build_key_finding(baseline_metrics, optimized_metrics, scenario.name),
    )


def seed_runs() -> int:
    """Compute and store an initial evaluation run for every scenario.

    Called on startup so the Performance Lab has real, computed data without
    the user having to run anything first.
    """

    count = 0
    from app.services.scenario_service import list_scenarios

    for scenario in list_scenarios():
        run_optimization(scenario.id)
        count += 1
    return count
