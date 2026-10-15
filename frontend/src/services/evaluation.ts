import { apiEndpoints } from "../config/api";
import type {
  PerformanceLabData,
  PerformanceRun,
} from "../types/performanceLab";
import { fetchEnvelope } from "./http";

export async function fetchEvaluationRuns(
  signal?: AbortSignal,
): Promise<PerformanceRun[]> {
  const data = await fetchEnvelope<PerformanceLabData>(
    apiEndpoints.evaluation,
    signal,
  );
  return data.runs;
}

export function fetchEvaluationRun(
  runId: string,
  signal?: AbortSignal,
): Promise<PerformanceRun> {
  return fetchEnvelope<PerformanceRun>(
    apiEndpoints.evaluationRun(runId),
    signal,
  );
}
