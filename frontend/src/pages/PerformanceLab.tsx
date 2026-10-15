
import { useMemo, useState } from "react";

import PerformanceLabHeader from "../components/performance-lab/PerformanceLabHeader";
import PerformanceKpiCards from "../components/performance-lab/PerformanceKpiCards";
import PerformanceComparison from "../components/performance-lab/PerformanceComparison";
import PerformanceCharts from "../components/performance-lab/PerformanceCharts";
import FleetUtilization from "../components/performance-lab/FleetUtilization";
import KeyFindings from "../components/performance-lab/KeyFindings";
import RunHistory from "../components/performance-lab/RunHistory";
import RunStatus from "../components/performance-lab/RunStatus";

import { performanceLabMockData } from "../mocks/performanceLab";

const scenarioOptions = [
  { value: "normal_operations", label: "Normal Operations" },
  { value: "demand_spike", label: "Demand Spike" },
  { value: "vehicle_unavailable", label: "Vehicle Unavailable" },
];

export default function PerformanceLab() {
  const [selectedScenarioId, setSelectedScenarioId] =
    useState("demand_spike");

  const [selectedRunId, setSelectedRunId] = useState("1042");

  const runs = performanceLabMockData.runs;

  const scenarioRuns = useMemo(
    () =>
      runs.filter((run) => run.scenarioId === selectedScenarioId),
    [runs, selectedScenarioId],
  );

  const selectedRun = useMemo(
    () =>
      scenarioRuns.find((run) => run.runId === selectedRunId) ??
      scenarioRuns[0],
    [scenarioRuns, selectedRunId],
  );

  function handleScenarioChange(scenarioId: string) {
    setSelectedScenarioId(scenarioId);

    const firstRun = runs.find(
      (run) => run.scenarioId === scenarioId,
    );

    setSelectedRunId(firstRun?.runId ?? "");
  }

  function handleRunChange(runId: string) {
    setSelectedRunId(runId);
  }

  const metrics = selectedRun?.metrics;


  return (
    <div className="min-w-0 space-y-6">
      <PerformanceLabHeader
        scenarios={scenarioOptions}
        runs={scenarioRuns}
        selectedScenarioId={selectedScenarioId}
        selectedRunId={selectedRun?.runId ?? ""}
        onScenarioChange={handleScenarioChange}
        onRunChange={handleRunChange}
      />

      {!selectedRun ? (
        <RunStatus type="no-run" />
      ) : selectedRun.status === "infeasible" ? (
        <RunStatus
          type="infeasible"
          runId={selectedRun.runId}
        />
      ) : !metrics ? (
        <RunStatus
          type="no-metrics"
          runId={selectedRun.runId}
        />
      ) : (
        <>
          <section className="space-y-2">
            <p className="text-sm text-secondary">
              Evaluation Run{" "}
              <span className="font-semibold text-foreground">
                #{selectedRun.runId}
              </span>
              {" · "}
              <span className="text-foreground">
                {selectedRun.scenarioName}
              </span>
            </p>

            <PerformanceKpiCards metrics={metrics} />
          </section>

          <PerformanceComparison metrics={metrics} />

          <PerformanceCharts metrics={metrics} />

          <FleetUtilization
            vehicles={selectedRun.fleetUtilization ?? []}
          />

          <KeyFindings
            metrics={metrics}
            passengerOutcome={selectedRun.passengerOutcome}
            keyFinding={selectedRun.keyFinding}
          />
        </>
      )}

      <RunHistory
        runs={scenarioRuns}
        selectedRunId={selectedRun?.runId ?? ""}
        onSelectRun={handleRunChange}
      />
    </div>
  );
}
