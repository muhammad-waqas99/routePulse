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
