export type EvaluationStatus = "completed" | "infeasible";

export type PerformanceMetric = {
  baseline: number;
  optimized: number;
  unit: string;
  lowerIsBetter: boolean;
};

export type PerformanceMetrics = {
  averageWaitingTime?: PerformanceMetric;
  unservedPassengers?: PerformanceMetric;
  capacityViolations?: PerformanceMetric;
  vehicleDistance?: PerformanceMetric;
  operatingCost?: PerformanceMetric;
};

export type PassengerOutcome = {
  total?: number;
  baselineServed?: number;
  baselineUnserved?: number;
  optimizedServed?: number;
  optimizedUnserved?: number;
};

export type FleetUtilization = {
  vehicleId: string;
  baseline: number;
  optimized: number;
};

export type PerformanceRun = {
  runId: string;
  scenarioId: string;
  scenarioName: string;
  status: EvaluationStatus;
  createdAt: string;
  metrics?: PerformanceMetrics;
  passengerOutcome?: PassengerOutcome;
  fleetUtilization?: FleetUtilization[];
  keyFinding?: string;
};

export type PerformanceLabData = { runs: PerformanceRun[] };
