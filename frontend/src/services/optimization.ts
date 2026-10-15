import { apiEndpoints } from "../config/api";
import type { RecoveryPlanResult } from "../types/recoveryPlanner";
import { requestJson } from "./http";

export interface OptimizeResult extends RecoveryPlanResult {
  runId: string;
  scenarioId: string;
  scenarioName: string;
  message: string;
  warnings: string[];
}

export function runOptimization(
  scenarioId: string,
  signal?: AbortSignal,
): Promise<OptimizeResult> {
  return requestJson<OptimizeResult>(
    apiEndpoints.optimize,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenarioId }),
    },
    signal,
  );
}
