import type { Scenario } from "../types/scenarios";

export const scenarios: Scenario[] = [
  {
    id: "normal_operations",
    name: "Normal Operations",
    category: "Normal",
    description:
      "Baseline transportation demand and vehicle availability.",
    demandMultipliers: {},
    travelTimeMultipliers: {},
    unavailableVehicleIds: [],
    evaluationHorizonMin: 120,
  },
  {
    id: "demand_spike",
    name: "Demand Spike",
    category: "Stress Test",
    description:
      "Passenger demand increases during peak periods.",
    demandMultipliers: { campus: 1.5 },
    travelTimeMultipliers: {},
    unavailableVehicleIds: [],
    evaluationHorizonMin: 120,
  },
  {
    id: "vehicle_unavailable",
    name: "Vehicle Unavailable",
    category: "Disruption",
    description:
      "One vehicle becomes unavailable during the operating window.",
    demandMultipliers: {},
    travelTimeMultipliers: {},
    unavailableVehicleIds: ["BUS01"],
    evaluationHorizonMin: 120,
  },
];
