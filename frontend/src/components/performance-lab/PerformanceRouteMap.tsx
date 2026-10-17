import { useMemo } from "react";

import SimulationChangeMap from "../recovery-planner/SimulationChangeMap";
import { useOperationsOverview } from "../../hooks/useOperationsOverview";
import type {
  BackendEvaluationResponse,
  OptimizationResult,
  OptimizationTrip,
} from "../../types/optimization";

function formatDeparture(minutes: number) {
  const normalized = ((Math.trunc(minutes) % 1440) + 1440) % 1440;
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
}

function mapPlan(plan: NonNullable<BackendEvaluationResponse["baseline_plan"]>): OptimizationTrip[] {
  return [
    ...plan.assignments.map((trip) => ({ trip, isExtra: false })),
    ...plan.extra_trips.map((trip) => ({ trip, isExtra: true })),
  ].map(({ trip, isExtra }) => ({
    tripId: trip.trip_id,
    routeId: trip.route_id,
    vehicleId: trip.vehicle_id,
    departureTime: formatDeparture(trip.departure_min),
    isExtra,
  }));
}

export default function PerformanceRouteMap({ evaluation }: { evaluation: BackendEvaluationResponse | null }) {
  const { data, isLoading, error } = useOperationsOverview();
  const result = useMemo<OptimizationResult | null>(() => {
    if (!evaluation?.baseline_plan || !evaluation.candidate_plan) return null;
    const validation = evaluation.comparison.candidate_validation;
    const originalTrips = mapPlan(evaluation.baseline_plan);
    const proposedTrips = mapPlan(evaluation.candidate_plan);
    const baseline = evaluation.baseline?.metrics;
    const candidate = evaluation.candidate?.metrics;
    return {
      status: validation.feasible && evaluation.candidate ? "feasible" : "infeasible",
      originalTrips,
      proposedTrips,
      totalTrips: Math.max(originalTrips.length, proposedTrips.length),
      unassignedTripIds: evaluation.candidate_plan.unassigned_trip_ids,
      constraints: [],
      hardViolationCount: validation.hard_violation_count,
      runId: evaluation.evaluation_id ?? evaluation.baseline?.run_id ?? "unknown",
      scenarioId: evaluation.scenario_id,
      scenarioName: evaluation.scenario_id.replaceAll("_", " "),
      message: evaluation.notes.join(" "),
      warnings: evaluation.notes,
      validation: {
        valid: validation.feasible,
        hardViolationCount: validation.hard_violation_count,
        unverifiedConstraints: validation.unverified_constraints.map((item) => item.code ?? "unknown"),
        constraints: [],
      },
      baselineMetrics: baseline ? {
        averageWaitingTimeMin: baseline.avg_wait_min,
        unservedPassengers: baseline.unserved_passengers,
        servedPassengers: baseline.served_passengers,
        vehicleDistanceKm: baseline.vehicle_km,
        capacityViolations: baseline.capacity_violations,
      } : null,
      optimizedMetrics: candidate ? {
        averageWaitingTimeMin: candidate.avg_wait_min,
        unservedPassengers: candidate.unserved_passengers,
        servedPassengers: candidate.served_passengers,
        vehicleDistanceKm: candidate.vehicle_km,
        capacityViolations: candidate.capacity_violations,
      } : null,
      backendResult: evaluation,
    };
  }, [evaluation]);

  if (!result) return null;
  return <SimulationChangeMap result={result} data={data} loading={isLoading} error={error} />;
}
