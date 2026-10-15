import type {
  PerformanceLabData,
  PerformanceRun,
} from "../types/performanceLab";

const demandSpikeRun: PerformanceRun = {
  runId: "1042",
  scenarioId: "demand_spike",
  scenarioName: "Demand Spike",
  status: "completed",
  createdAt: "2026-10-15T09:00:00",
  metrics: {
    averageWaitingTime: {
      baseline: 12.1,
      optimized: 8.9,
      unit: "min",
      lowerIsBetter: true,
    },
    unservedPassengers: {
      baseline: 29,
      optimized: 14,
      unit: "passengers",
      lowerIsBetter: true,
    },
    missedConnections: {
      baseline: 7,
      optimized: 3,
      unit: "passengers",
      lowerIsBetter: true,
    },
    etaMae: {
      baseline: 5.1,
      optimized: 4.0,
      unit: "min",
      lowerIsBetter: true,
    },
    unservedRate: {
      baseline: 4.8,
      optimized: 2.3,
      unit: "percent",
      lowerIsBetter: true,
    },
    capacityViolations: {
      baseline: 5,
      optimized: 0,
      unit: "passengers",
      lowerIsBetter: true,
    },
    vehicleDistance: {
      baseline: 38.5,
      optimized: 42.1,
      unit: "km",
      lowerIsBetter: true,
    },
  },
  passengerOutcome: {
    total: 607,
    baselineServed: 578,
    baselineUnserved: 29,
    optimizedServed: 593,
    optimizedUnserved: 14,
  },
  etaWithinThreeMinutes: {
    baseline: 66,
    optimized: 79,
  },
  fleetUtilization: [
    { vehicleId: "BUS01", baseline: 83, optimized: 86 },
    { vehicleId: "BUS02", baseline: 70, optimized: 78 },
    { vehicleId: "BUS03", baseline: 78, optimized: 82 },
    { vehicleId: "BUS04", baseline: 46, optimized: 61 },
  ],
  keyFinding:
    "The optimized plan served more passengers during the demand spike by adding departures on R2 and rebalancing vehicles. Vehicle distance increased as additional service was allocated to higher-demand periods.",
};

const historicalRuns: PerformanceRun[] = [
  {
    runId: "1041",
    scenarioId: "vehicle_unavailable",
    scenarioName: "Vehicle Unavailable",
    status: "completed",
    createdAt: "2026-10-15T08:00:00",
  },
  {
    runId: "1040",
    scenarioId: "normal_operations",
    scenarioName: "Normal Operations",
    status: "completed",
    createdAt: "2026-10-14T15:00:00",
  },
  {
    runId: "1039",
    scenarioId: "demand_spike",
    scenarioName: "Demand Spike",
    status: "completed",
    createdAt: "2026-10-14T12:00:00",
    metrics: {
      averageWaitingTime: {
        baseline: 12.1,
        optimized: 8.9,
        unit: "min",
        lowerIsBetter: true,
      },
      unservedPassengers: {
        baseline: 29,
        optimized: 14,
        unit: "passengers",
        lowerIsBetter: true,
      },
      missedConnections: {
        baseline: 7,
        optimized: 3,
        unit: "passengers",
        lowerIsBetter: true,
      },
      etaMae: {
        baseline: 5.1,
        optimized: 4.0,
        unit: "min",
        lowerIsBetter: true,
      },
      unservedRate: {
        baseline: 4.8,
        optimized: 2.3,
        unit: "percent",
        lowerIsBetter: true,
      },
      capacityViolations: {
        baseline: 5,
        optimized: 0,
        unit: "passengers",
        lowerIsBetter: true,
      },
      vehicleDistance: {
        baseline: 38.5,
        optimized: 42.1,
        unit: "km",
        lowerIsBetter: true,
      },
    },
    passengerOutcome: {
      total: 607,
      baselineServed: 578,
      baselineUnserved: 29,
      optimizedServed: 593,
      optimizedUnserved: 14,
    },
    etaWithinThreeMinutes: {
      baseline: 66,
      optimized: 79,
    },
    fleetUtilization: [
      { vehicleId: "BUS01", baseline: 83, optimized: 86 },
      { vehicleId: "BUS02", baseline: 70, optimized: 78 },
      { vehicleId: "BUS03", baseline: 78, optimized: 82 },
      { vehicleId: "BUS04", baseline: 46, optimized: 61 },
    ],
    keyFinding:
      "The optimized plan served more passengers during the demand spike by adding departures on R2 and rebalancing vehicles. Vehicle distance increased as additional service was allocated to higher-demand periods.",
  },
  {
    runId: "1038",
    scenarioId: "vehicle_unavailable",
    scenarioName: "Vehicle Unavailable",
    status: "infeasible",
    createdAt: "2026-10-14T10:00:00",
  },
];

export const performanceLabMockData: PerformanceLabData = {
  runs: [demandSpikeRun, ...historicalRuns],
};
