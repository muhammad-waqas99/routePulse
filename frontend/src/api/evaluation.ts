import apiClient from "./client";
import type { BackendEvaluationResponse } from "../types/optimization";
import type {
  PerformanceLabData,
  PerformanceMetric,
  PerformanceMetrics,
  PerformanceRun,
} from "../types/performanceLab";
import { scenarioLabel } from "../lib/presentation";

interface BackendMetrics {
  avg_wait_min?: number | null;
  unserved_passengers?: number | null;
  served_passengers?: number | null;
  total_demand?: number | null;
  vehicle_km?: number | null;
  operating_cost?: number | null;
  cost_available?: boolean;
  capacity_violations?: number | null;
}

interface BackendSimulation {
  run_id: string;
  feasible: boolean;
  metrics: BackendMetrics;
}

interface BackendEvaluation {
  evaluation_id: string | null;
  created_at: string | null;
  scenario_id: string;
  baseline: BackendSimulation | null;
  candidate: BackendSimulation | null;
  notes: string[];
}

function metric(baseline: number | null | undefined, optimized: number | null | undefined, unit: string, lowerIsBetter = true): PerformanceMetric | undefined {
  if (typeof baseline !== "number" || !Number.isFinite(baseline) || typeof optimized !== "number" || !Number.isFinite(optimized)) return undefined;
  return { baseline, optimized, unit, lowerIsBetter };
}

function toRun(evaluation: BackendEvaluation): PerformanceRun {
  const baseline = evaluation.baseline?.metrics;
  const candidate = evaluation.candidate?.metrics;
  let metrics: PerformanceMetrics | undefined;
  let passengerOutcome: PerformanceRun["passengerOutcome"];

  if (baseline && candidate) {
    const values: PerformanceMetrics = {
      averageWaitingTime: metric(baseline.avg_wait_min, candidate.avg_wait_min, "min"),
      unservedPassengers: metric(baseline.unserved_passengers, candidate.unserved_passengers, "passengers"),
      capacityViolations: metric(baseline.capacity_violations, candidate.capacity_violations, "violations"),
      vehicleDistance: metric(baseline.vehicle_km, candidate.vehicle_km, "km"),
      operatingCost: baseline.cost_available === true && candidate.cost_available === true
        ? metric(baseline.operating_cost, candidate.operating_cost, "cost units")
        : undefined,
    };
    const presentMetrics = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined)) as PerformanceMetrics;
    metrics = Object.keys(presentMetrics).length ? presentMetrics : undefined;
    passengerOutcome = {
      total: typeof baseline.total_demand === "number" ? baseline.total_demand : undefined,
      baselineServed: typeof baseline.served_passengers === "number" ? baseline.served_passengers : undefined,
      baselineUnserved: typeof baseline.unserved_passengers === "number" ? baseline.unserved_passengers : undefined,
      optimizedServed: typeof candidate.served_passengers === "number" ? candidate.served_passengers : undefined,
      optimizedUnserved: typeof candidate.unserved_passengers === "number" ? candidate.unserved_passengers : undefined,
    };
  }

  const completed = Boolean(evaluation.candidate?.feasible && candidate);
  return {
    runId: evaluation.evaluation_id ?? evaluation.baseline?.run_id ?? "unknown",
    scenarioId: evaluation.scenario_id,
    scenarioName: scenarioLabel(evaluation.scenario_id),
    status: completed ? "completed" : "infeasible",
    createdAt: evaluation.created_at ?? "",
    metrics,
    passengerOutcome,
    fleetUtilization: [],
  };
}

export const getPerformanceLab = async (): Promise<PerformanceLabData> => {
  const response = await apiClient.get<BackendEvaluation[]>("/evaluations");
  return { runs: response.data.map(toRun) };
};

export const getPerformanceRun = async (runId: string): Promise<PerformanceRun> => {
  const response = await apiClient.get<BackendEvaluation>(`/evaluations/${encodeURIComponent(runId)}`);
  return toRun(response.data);
};

export const getPerformanceRunDetail = async (runId: string): Promise<BackendEvaluationResponse> => {
  const response = await apiClient.get<BackendEvaluationResponse>(`/evaluations/${encodeURIComponent(runId)}`);
  return response.data;
};
