
import apiClient from "./client";

import type {
  OptimizationRequest,
  OptimizationResult,
} from "../types/optimization";

export const runOptimization = async (
  payload: OptimizationRequest,
): Promise<OptimizationResult> => {
  const response = await apiClient.post<OptimizationResult>(
    "/api/optimize",
    payload,
  );

  return response.data;
};
