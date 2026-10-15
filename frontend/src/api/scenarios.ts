import apiClient from "./client";
import type { ApiResponse } from "../types/api";
import type { Scenario } from "../types/scenarios";

export const getScenarios = async (): Promise<Scenario[]> => {
  const response = await apiClient.get<ApiResponse<Scenario[]>>(
    "/api/scenarios"
  );

  return response.data.data;
};