export type ScenarioCategory = "Normal" | "Stress Test" | "Disruption";

export interface Scenario {
  id: string;
  name: string;
  category: ScenarioCategory;
  description: string;
  evaluationHorizonMin: number;
  demandMultipliers: Record<string, number>;
  travelTimeMultipliers: Record<string, number>;
  unavailableVehicleIds: string[];
}
