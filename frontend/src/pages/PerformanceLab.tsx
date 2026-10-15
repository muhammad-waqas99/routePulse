import { useMemo, useState } from "react";

import PerformanceLabHeader from "../components/performance-lab/PerformanceLabHeader";
import PerformanceKpiCards from "../components/performance-lab/PerformanceKpiCards";
import PerformanceComparison from "../components/performance-lab/PerformanceComparison";
import PerformanceCharts from "../components/performance-lab/PerformanceCharts";
import FleetUtilization from "../components/performance-lab/FleetUtilization";
import KeyFindings from "../components/performance-lab/KeyFindings";
import RunHistory from "../components/performance-lab/RunHistory";
import RunStatus from "../components/performance-lab/RunStatus";
import { ErrorState, LoadingState } from "../components/common/AsyncState";

import { useEvaluationRuns } from "../hooks/useEvaluationRuns";

export default function PerformanceLab() {
  const { data, loading, error, reload } = useEvaluationRuns();

  const [selectedScenarioId, setSelectedScenarioId] = useState("");
  const [selectedRunId, setSelectedRunId] = useState("");

  const runs = useMemo(() => data ?? [], [data]);

  const scenarioOptions = useMemo(() => {
    const seen = new Map<string, string>();

    for (const run of runs) {
      if (!seen.has(run.scenarioId)) {
        seen.set(run.scenarioId, run.scenarioName);
      }
    }

    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [runs]);

  const defaultRun = useMemo(
    () =>
      runs.find((run) => run.scenarioId === "demand_spike") ?? runs[0],
    [runs],
  );

  const activeScenarioId = selectedScenarioId || defaultRun?.scenarioId || "";

  const scenarioRuns = useMemo(
    () => runs.filter((run) => run.scenarioId === activeScenarioId),
    [runs, activeScenarioId],
  );

  const selectedRun = useMemo(
    () =>
      scenarioRuns.find((run) => run.runId === selectedRunId) ??
      scenarioRuns[0],
    [scenarioRuns, selectedRunId],
  );

  function handleScenarioChange(scenarioId: string) {
    setSelectedScenarioId(scenarioId);

    const firstRun = runs.find((run) => run.scenarioId === scenarioId);

    setSelectedRunId(firstRun?.runId ?? "");
  }

  function handleRunChange(runId: string) {
    setSelectedRunId(runId);
  }

  if (loading) {
    return <LoadingState label="Loading evaluation runs..." />;
  }

  if (error || !data) {
    return (
      <ErrorState
        message={error ?? "No evaluation data was returned."}
        onRetry={reload}
      />
    );
  }

  const metrics = selectedRun?.metrics;

  return (
    <div className="min-w-0 space-y-6">
      <PerformanceLabHeader
        scenarios={scenarioOptions}
        runs={scenarioRuns}
        selectedScenarioId={activeScenarioId}
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
