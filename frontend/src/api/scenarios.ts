import apiClient from "./client";
import type { Scenario } from "../types/scenarios";

interface BackendScenario {
  scenario_id: string;
  evaluation_horizon_min: number;
  demand_multipliers: Record<string, number>;
  travel_time_multipliers: Record<string, number>;
  unavailable_vehicle_ids: string[];
}

const labels: Record<string, { name: string; description: string }> = {
  normal: { name: "Normal Operations", description: "Standard campus service." },
  demand_surge: { name: "Demand Surge", description: "Higher passenger demand." },
  vehicle_failure: { name: "Vehicle Failure", description: "Reduced vehicle availability." },
  road_closure: { name: "Road Closure", description: "Longer travel times." },
  traffic_delay: { name: "Traffic Delay", description: "Traffic-related delays." },
};

export const getScenarios = async (): Promise<Scenario[]> => {
  const response = await apiClient.get<BackendScenario[]>("/scenarios");
  return response.data.map((scenario) => {
    const label = labels[scenario.scenario_id] ?? {
      name: scenario.scenario_id.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()),
      description: "Disruption scenario.",
    };
    const isDisruption = scenario.unavailable_vehicle_ids.length > 0 ||
      Object.keys(scenario.travel_time_multipliers).length > 0;
    return {
      id: scenario.scenario_id,
      name: label.name,
      category: scenario.scenario_id === "normal" ? "Normal" : isDisruption ? "Disruption" : "Stress Test",
      description: label.description,
      evaluationHorizonMin: scenario.evaluation_horizon_min,
      demandMultipliers: scenario.demand_multipliers,
      travelTimeMultipliers: scenario.travel_time_multipliers,
      unavailableVehicleIds: scenario.unavailable_vehicle_ids,
    };
  });
};
