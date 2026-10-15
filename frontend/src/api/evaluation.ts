import apiClient from "./client";
import type { ApiResponse } from "../types/api";
import type {
  PerformanceLabData,
  PerformanceRun,
} from "../types/performanceLab";

export const getPerformanceLab = async (): Promise<PerformanceLabData> => {
  const response = await apiClient.get<ApiResponse<PerformanceLabData>>(
    "/api/evaluation"
  );

  return response.data.data;
};

export const getPerformanceRun = async (
  runId: string
): Promise<PerformanceRun> => {
  const response = await apiClient.get<ApiResponse<PerformanceRun>>(
    `/api/evaluation/${encodeURIComponent(runId)}`
  );

  return response.data.data;
};