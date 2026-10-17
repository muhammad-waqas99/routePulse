import apiClient from "./client";
import type { OperationsData } from "../types/operations";

export const getOperationsOverview =
  async (): Promise<OperationsData> => {
    const [overviewResponse, networkResponse] = await Promise.all([
      apiClient.get<OperationsData>("/operations/overview"),
      apiClient.get<{ routes: Array<{ route_id: string; segment_travel_min: number[]; segment_distance_km: number[] }> }>("/network"),
    ]);
    const routeDetails = new Map(networkResponse.data.routes.map((route) => [route.route_id, route]));
    return {
      ...overviewResponse.data,
      routes: overviewResponse.data.routes.map((route) => {
        const detail = routeDetails.get(route.id);
        return detail ? { ...route, segmentTravelMin: detail.segment_travel_min, segmentDistanceKm: detail.segment_distance_km } : route;
      }),
    };
  };
