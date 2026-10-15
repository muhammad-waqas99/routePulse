import { apiEndpoints } from "../config/api";
import type { Scenario } from "../types/scenarios";
import { fetchEnvelope } from "./http";

export function fetchScenarios(signal?: AbortSignal): Promise<Scenario[]> {
  return fetchEnvelope<Scenario[]>(apiEndpoints.scenarios, signal);
}
