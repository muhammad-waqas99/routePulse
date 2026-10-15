import type { Scenario } from "../types/scenarios";

export const scenarios: Scenario[] = [
  {
    id: "normal_operations",
    name: "Normal Operations",
    category: "Normal",
    description:
      "Baseline transportation demand and vehicle availability.",
    type: "normal",
    demandMultiplierPercent: 0,
    availableVehicles: 4,
    affectedPeriod: "08:00–10:00",
    evaluationHorizonMin: 120,
  },
  {
    id: "demand_spike",
    name: "Demand Spike",
    category: "Stress Test",
    description:
      "Passenger demand increases during peak periods.",
    type: "demand-spike",
    demandMultiplierPercent: 50,
    availableVehicles: 4,
    affectedPeriod: "08:00–10:00",
    evaluationHorizonMin: 120,
  },
  {
    id: "vehicle_unavailable",
    name: "Vehicle Unavailable",
    category: "Disruption",
    description:
      "One vehicle becomes unavailable during the operating window.",
    type: "vehicle-unavailable",
    demandMultiplierPercent: 0,
    availableVehicles: 3,
    affectedPeriod: "08:15–09:45",
    evaluationHorizonMin: 120,
  },
];
