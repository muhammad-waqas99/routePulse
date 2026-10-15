
export type OptimizationStatus = "optimal" | "infeasible";

export interface OptimizationRequest {
  scenarioId: string;
  seed?: number;
}

export interface OptimizationTrip {
  tripId: string;
  routeId: string;
  vehicleId: string;
  departureTime: string;
}

export interface OptimizationConstraint {
  id: string;
  label: string;
  passed: boolean;
  detail: string;
}

export interface OptimizationMetrics {
  averageWaitingTimeMin: number;
  unservedPassengers: number;
  missedConnections: number;
  vehicleDistanceKm: number;
}

export interface OptimizationPlan {
  label: string;
  trips: OptimizationTrip[];
  totalTrips: number;
  vehiclesUsed: string[];
  totalDistanceKm: number;
}

export interface OptimizationValidation {
  valid: boolean;
  hardViolationCount: number;
  constraints: OptimizationConstraint[];
}

export interface SimulationMetrics {
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

export interface OptimizationDifference {
  metric: string;
  baseline: number;
  optimized: number;
  difference: number;
  lowerIsBetter: boolean;
  improved: boolean;
}

export interface OptimizationResult {
  status: OptimizationStatus;
  originalTrips: OptimizationTrip[];
  proposedTrips: OptimizationTrip[];
  totalTrips: number;
  constraints: OptimizationConstraint[];
  hardViolationCount: number;
  metrics: OptimizationMetrics;
  runId: string;
  scenarioId: string;
  scenarioName: string;
  message: string;
  baselinePlan: OptimizationPlan;
  optimizedPlan: OptimizationPlan;
  validation: OptimizationValidation;
  simulation: Record<string, SimulationMetrics>;
  baselineMetrics: OptimizationMetrics;
  optimizedMetrics: OptimizationMetrics;
  differences: OptimizationDifference[];
  warnings: string[];
}
