export type OptimizationStatus =
  | "optimal"
  | "feasible"
  | "infeasible"
  | "unknown";

export type RunStage =
  | "idle"
  | "loading-scenario"
  | "optimizing"
  | "validating"
  | "evaluating"
  | "completed"
  | "error";

export interface TimetableTrip {
  tripId: string;
  routeId: string;
  vehicleId: string;
  departureTime: string;
}

export interface ConstraintCheck {
  id: string;
  label: string;
  passed: boolean;
  detail?: string;
}

export interface OptimizationMetrics {
  averageWaitingTimeMin: number;
  unservedPassengers: number;
  missedConnections: number;
  vehicleDistanceKm: number;
}

export interface RecoveryPlanResult {
  status: OptimizationStatus;
  originalTrips: TimetableTrip[];
  proposedTrips: TimetableTrip[];
  totalTrips: number;
  constraints: ConstraintCheck[];
  hardViolationCount: number;
  metrics: OptimizationMetrics;
}

export interface PlanSummary {
  label: string;
  trips: TimetableTrip[];
  totalTrips: number;
  vehiclesUsed: number;
  totalDistanceKm: number;
}

export interface ValidationResult {
  valid: boolean;
  hardViolationCount: number;
  constraints: ConstraintCheck[];
}

export interface SimulationSummary {
  label: string;
  servedPassengers: number;
  unservedPassengers: number;
  missedConnections: number;
  capacityDeniedPassengers: number;
  averageWaitingTimeMin: number;
  tripsCompleted: number;
  tripsTotal: number;
  vehicleDistanceKm: number;
  totalTravelTimeMin: number;
  capacityViolations: number;
}

export interface MetricDifference {
  metric: string;
  baseline: number;
  optimized: number;
  difference: number;
  lowerIsBetter: boolean;
  improved: boolean;
}

export interface OptimizeResponse extends RecoveryPlanResult {
  runId: string;
  scenarioId: string;
  scenarioName: string;
  message: string;
  baselinePlan: PlanSummary;
  optimizedPlan: PlanSummary;
  validation: ValidationResult;
  simulation: Record<string, SimulationSummary>;
  baselineMetrics: OptimizationMetrics;
  optimizedMetrics: OptimizationMetrics;
  differences: MetricDifference[];
  warnings: string[];
}