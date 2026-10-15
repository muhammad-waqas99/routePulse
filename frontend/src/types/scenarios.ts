export type ScenarioType =
  | "normal"
  | "demand-spike"
  | "vehicle-unavailable";

export type ScenarioCategory =
  | "Normal"
  | "Stress Test"
  | "Disruption";

export interface Scenario {
  id: string;
  name: string;
  category: ScenarioCategory;
  description: string;
  type: ScenarioType;

  demandMultiplierPercent: number;
  availableVehicles: number;
  affectedPeriod: string;
  evaluationHorizonMin: number;
}
