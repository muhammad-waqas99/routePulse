
import { useEffect, useMemo, useState } from "react";

import PerformanceLabHeader from "../components/performance-lab/PerformanceLabHeader";
import PerformanceKpiCards from "../components/performance-lab/PerformanceKpiCards";
import PerformanceComparison from "../components/performance-lab/PerformanceComparison";
import PerformanceCharts from "../components/performance-lab/PerformanceCharts";
import FleetUtilization from "../components/performance-lab/FleetUtilization";
import KeyFindings from "../components/performance-lab/KeyFindings";
import RunHistory from "../components/performance-lab/RunHistory";
import RunStatus from "../components/performance-lab/RunStatus";

import { getPerformanceLab } from "../api/evaluation";
import type {
  PerformanceLabData,
 
} from "../types/performanceLab";

export default function PerformanceLab() {
  const [data, setData] = useState<PerformanceLabData | null>(null);

  const [selectedScenarioId, setSelectedScenarioId] = useState("");
  const [selectedRunId, setSelectedRunId] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchEvaluation() {
      try {
        setIsLoading(true);
        setError(null);

        const evaluationData = await getPerformanceLab();

        if (!isMounted) return;

        setData(evaluationData);

        const firstRun = evaluationData.runs[0];

        if (firstRun) {
          setSelectedScenarioId(firstRun.scenarioId);
          setSelectedRunId(firstRun.runId);
        }
      } catch (error: unknown) {
        if (!isMounted) return;

        setError(
          error instanceof Error
            ? error.message
            : "Failed to load evaluation data.",
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void fetchEvaluation();

    return () => {
      isMounted = false;
    };
  }, []);

  const runs = data?.runs ?? [];

  const scenarioOptions = useMemo(() => {
    const uniqueScenarios = new Map<string, string>();

    for (const run of runs) {
      if (!uniqueScenarios.has(run.scenarioId)) {
        uniqueScenarios.set(run.scenarioId, run.scenarioName);
      }
    }

    return Array.from(uniqueScenarios, ([value, label]) => ({
      value,
      label,
    }));
  }, [runs]);

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

  if (isLoading) {
    return (
      <div
        className="flex min-h-48 items-center justify-center"
        role="status"
        aria-live="polite"
      >
        <p className="text-sm text-secondary">
          Loading evaluation data...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4 rounded-xl border border-border p-5 sm:p-6">
        <h2 className="font-semibold text-foreground">
          Unable to load Evaluation
        </h2>

        <p className="break-words text-sm text-secondary">
          {error}
        </p>

        <button
          type="button"
          onClick={() => window.location.reload()}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white"
        >
          Retry
        </button>
      </div>
    );
  }

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
