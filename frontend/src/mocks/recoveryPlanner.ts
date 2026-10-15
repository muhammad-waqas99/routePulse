import type { RecoveryPlanResult } from "../types/recoveryPlanner";

export const recoveryPlannerMockResult: RecoveryPlanResult = {
  status: "optimal",

  totalTrips: 18,

  originalTrips: [
    { tripId: "T101", routeId: "R1", vehicleId: "BUS01", departureTime: "08:00" },
    { tripId: "T102", routeId: "R1", vehicleId: "BUS03", departureTime: "08:15" },
    { tripId: "T104", routeId: "R1", vehicleId: "BUS03", departureTime: "08:45" },
    { tripId: "T201", routeId: "R2", vehicleId: "BUS02", departureTime: "08:10" },
    { tripId: "T203", routeId: "R2", vehicleId: "BUS02", departureTime: "08:30" },
    { tripId: "T205", routeId: "R2", vehicleId: "BUS02", departureTime: "08:50" },
    { tripId: "T301", routeId: "R3", vehicleId: "BUS04", departureTime: "08:20" },
    { tripId: "T302", routeId: "R3", vehicleId: "BUS04", departureTime: "08:45" },
  ],

  proposedTrips: [
    { tripId: "T101", routeId: "R1", vehicleId: "BUS01", departureTime: "08:00" },
    { tripId: "T102", routeId: "R1", vehicleId: "BUS03", departureTime: "08:15" },
    { tripId: "T104", routeId: "R1", vehicleId: "BUS03", departureTime: "08:45" },
    { tripId: "T201", routeId: "R2", vehicleId: "BUS02", departureTime: "08:10" },
    { tripId: "T203", routeId: "R2", vehicleId: "BUS02", departureTime: "08:30" },
    { tripId: "T205", routeId: "R2", vehicleId: "BUS02", departureTime: "08:50" },
    { tripId: "T301", routeId: "R3", vehicleId: "BUS04", departureTime: "08:20" },
    { tripId: "T302", routeId: "R3", vehicleId: "BUS04", departureTime: "08:40" },
  ],

  hardViolationCount: 0,

  constraints: [
    { id: "vehicle-assignment", label: "Vehicle assignment", passed: true },
    { id: "vehicle-availability", label: "Vehicle availability", passed: true },
    { id: "departure-windows", label: "Departure windows", passed: true },
    { id: "vehicle-turnaround", label: "Vehicle turnaround", passed: true },
    { id: "segment-capacity", label: "Segment capacity", passed: true },
    { id: "transfer-buffer", label: "Transfer buffer", passed: true },
  ],

  metrics: {
    averageWaitingTimeMin: 7.1,
    unservedPassengers: 4,
    missedConnections: 1,
    vehicleDistanceKm: 41.2,
  },
};
