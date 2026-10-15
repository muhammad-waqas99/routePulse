import apiClient from "./client";
import type { ApiResponse } from "../types/api";
import type { OperationsData } from "../types/operations";

export const getOperationsOverview = async (): Promise<OperationsData> => {
  const response = await apiClient.get<ApiResponse<OperationsData>>(
    "/api/operations/overview"
  );

  return response.data.data;
};