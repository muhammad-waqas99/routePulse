import apiClient from "./client";
import type {
  OptimizeResponse,
} from "../types/recoveryPlanner";

export const runOptimization = async (
  scenarioId: string
): Promise<OptimizeResponse> => {
  const response = await apiClient.post<OptimizeResponse>(
    "/api/optimize",
    { scenarioId }
  );

  return response.data;
};