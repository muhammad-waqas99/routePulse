import apiClient from "./client";
import type {
  BackendEvaluationResponse,
  BackendPlan,
  BackendSimulationResult,
  BackendValidationReport,
  OptimizationConstraint,
  OptimizationResult,
  OptimizationTrip,
  RunMetrics,
} from "../types/optimization";
import { humanizeIdentifier } from "../lib/presentation";

function formatDeparture(value: number): string {
  const minute = Math.floor(value);
  return `${String(Math.floor(minute / 60) % 24).padStart(2, "0")}:${String(minute % 60).padStart(2, "0")}`;
}

function toTrips(plan: BackendPlan | null): OptimizationTrip[] {
  if (!plan) return [];
  return [
    ...plan.assignments.map((item) => ({ item, isExtra: false })),
    ...plan.extra_trips.map((item) => ({ item, isExtra: true })),
  ].map(({ item, isExtra }) => ({
    tripId: item.trip_id,
    routeId: item.route_id,
    vehicleId: item.vehicle_id,
    departureTime: formatDeparture(item.departure_min),
    isExtra,
  }));
}

function toMetrics(run: BackendSimulationResult | null): RunMetrics | null {
  if (!run) return null;
  return {
    averageWaitingTimeMin: run.metrics.avg_wait_min,
    unservedPassengers: run.metrics.unserved_passengers,
    servedPassengers: run.metrics.served_passengers,
    vehicleDistanceKm: run.metrics.vehicle_km,
    capacityViolations: run.metrics.capacity_violations,
  };
}

function toValidation(report: BackendValidationReport | undefined): OptimizationConstraint[] {
  if (!report) return [];
  const issues: Array<Record<string, unknown> & { state: "failed" | "unverified"; code?: string }> = [
    ...report.violations.map((item) => ({ ...item, state: "failed" as const })),
    ...report.unverified_constraints.map((item) => ({ ...item, state: "unverified" as const })),
  ];
  const issueCodes = new Set(issues.map((item) => item.code).filter((code): code is string => Boolean(code)));
  return [...issueCodes].map((code) => {
    const matching = issues.filter((item) => item.code === code);
    const failed = matching.some((item) => item.state === "failed");
    const detail = matching.slice(0, 2).map((item) => {
      const message = [item.reason, item.message, item.detail]
        .find((value): value is string => typeof value === "string");
      const context = ["trip_id", "vehicle_id", "route_id", "stop_id"]
        .filter((key) => typeof item[key] === "string")
        .map((key) => humanizeIdentifier(String(item[key])));
      return [message, ...context].filter(Boolean).join(" · ");
    }).filter(Boolean).join("; ");
    const occurrenceSummary = matching.length > 2 ? ` · and ${matching.length - 2} more` : "";
    return {
      id: code,
      label: humanizeIdentifier(code),
      status: failed ? "failed" : "unverified",
      passed: false,
      detail: `${matching.length} occurrence(s)${detail ? ` · ${detail}` : ""}${occurrenceSummary}`,
    };
  });
}

export const runOptimization = async (scenarioId: string): Promise<OptimizationResult> => {
  const response = await apiClient.post<BackendEvaluationResponse>("/evaluate", {
    scenario_id: scenarioId,
  });
  const data = response.data;
  const validation = data.comparison.candidate_validation;
  const constraints = toValidation(validation);
  const baselineTrips = toTrips(data.baseline_plan);
  const proposedTrips = toTrips(data.candidate_plan);
  const baselineMetrics = toMetrics(data.baseline);
  const optimizedMetrics = toMetrics(data.candidate);
  const status = validation?.feasible && data.candidate ? "feasible" : "infeasible";
  const unverified = validation?.unverified_constraints.map((item) => item.code ?? "unknown") ?? [];
  const warnings = data.notes ?? [];

  return {
    status,
    originalTrips: baselineTrips,
    proposedTrips,
    totalTrips: Math.max(baselineTrips.length, proposedTrips.length),
    unassignedTripIds: data.candidate_plan?.unassigned_trip_ids ?? [],
    constraints,
    hardViolationCount: validation?.hard_violation_count ?? 0,
    runId: data.evaluation_id ?? data.baseline?.run_id ?? "unavailable",
    scenarioId: data.scenario_id,
    scenarioName: data.scenario_id,
    message: warnings.join(" "),
    warnings,
    validation: {
      valid: Boolean(validation?.feasible),
      hardViolationCount: validation?.hard_violation_count ?? 0,
      unverifiedConstraints: unverified,
      constraints,
    },
    baselineMetrics,
    optimizedMetrics,
    backendResult: data,
  };
};
