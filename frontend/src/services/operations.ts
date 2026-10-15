import { apiEndpoints } from "../config/api";
import type { OperationsData } from "../types/operations";
import { fetchEnvelope } from "./http";

export function fetchOperationsOverview(
  signal?: AbortSignal,
): Promise<OperationsData> {
  return fetchEnvelope<OperationsData>(apiEndpoints.operationsOverview, signal);
}
