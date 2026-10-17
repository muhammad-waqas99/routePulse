export type OptimizationStatus = "feasible" | "infeasible";

export interface OptimizationTrip {
  tripId: string;
  routeId: string;
  vehicleId: string;
  departureTime: string;
  isExtra?: boolean;
}

export interface OptimizationConstraint {
  id: string;
  label: string;
  status: "passed" | "failed" | "unverified";
  detail: string;
  passed: boolean;
}

export interface RunMetrics {
  averageWaitingTimeMin: number;
  unservedPassengers: number;
  servedPassengers: number;
  vehicleDistanceKm: number;
  capacityViolations: number;
}

export interface BackendMetrics {
  eta_mae_min: number | null;
  avg_wait_min: number;
  unserved_passengers: number;
  missed_connections: number;
  capacity_violations: number;
  vehicle_km: number;
  served_passengers: number;
  abandoned_passengers: number;
  total_demand: number;
  completed_journeys: number;
  median_wait_min: number;
  max_wait_min: number;
  passengers_affected_by_breakdowns: number;
  breakdown_count: number;
  vehicle_departures: number;
  vehicle_arrivals: number;
  operating_cost: number;
  cost_available: boolean;
  max_segment_load: number;
  eta_observations: number;
}

export interface BackendValidationReport {
  feasible: boolean;
  hard_violation_count: number;
  violations: Array<Record<string, unknown> & { code?: string }>;
  unverified_constraints: Array<Record<string, unknown> & { code?: string; reason?: string }>;
}

export interface BackendPassengerOutcomes {
  total_demand: number;
  served: number;
  unserved: number;
  abandoned: number;
  stranded_onboard: number;
  waiting_at_horizon: number;
  affected_by_breakdowns: number;
}

export interface BackendEvent {
  time_min: number;
  event_type: string;
  trip_id: string | null;
  vehicle_id: string | null;
  stop_id: string | null;
  segment_index: number | null;
  passengers: number | null;
  load: number | null;
  detail: string | null;
}

export interface BackendVehicleHistoryEntry {
  time_min: number;
  event: string;
  vehicle_id: string;
  trip_id: string | null;
  route_id: string | null;
  stop_id: string | null;
  segment_index: number | null;
  onboard: number;
  load: number;
}

export interface BackendSimulationResult {
  run_id: string;
  scenario_id: string;
  plan_type: string;
  seed: number;
  start_min: number;
  horizon_min: number;
  status: string;
  feasible: boolean;
  validation: BackendValidationReport;
  metrics: BackendMetrics;
  passenger_outcomes: BackendPassengerOutcomes;
  events: BackendEvent[];
  vehicle_histories: BackendVehicleHistoryEntry[];
  notes: string[];
}

export interface BackendPlan {
  plan_type: string;
  assignments: Array<{
    trip_id: string;
    route_id: string;
    vehicle_id: string;
    departure_min: number;
  }>;
  extra_trips: Array<{
    trip_id: string;
    route_id: string;
    vehicle_id: string;
    departure_min: number;
  }>;
  unassigned_trip_ids: string[];
  solver_status: string;
}

export interface BackendEvaluationResponse {
  evaluation_id: string | null;
  created_at: string | null;
  scenario_id: string;
  baseline: BackendSimulationResult | null;
  candidate: BackendSimulationResult | null;
  baseline_plan: BackendPlan | null;
  candidate_plan: BackendPlan | null;
  comparison: {
    baseline: { run_id: string; feasible: boolean; metrics: BackendMetrics };
    candidate: { run_id: string; feasible: boolean; metrics: BackendMetrics } | null;
    deltas: Record<string, number>;
    directions: Record<string, string>;
    notes: string[];
    candidate_validation: BackendValidationReport;
  };
  notes: string[];
}

export interface OptimizationResult {
  status: OptimizationStatus;
  originalTrips: OptimizationTrip[];
  proposedTrips: OptimizationTrip[];
  totalTrips: number;
  unassignedTripIds: string[];
  constraints: OptimizationConstraint[];
  hardViolationCount: number;
  runId: string;
  scenarioId: string;
  scenarioName: string;
  message: string;
  warnings: string[];
  validation: {
    valid: boolean;
    hardViolationCount: number;
    unverifiedConstraints: string[];
    constraints: OptimizationConstraint[];
  };
  baselineMetrics: RunMetrics | null;
  optimizedMetrics: RunMetrics | null;
  backendResult: BackendEvaluationResponse;
}
