
import { useEffect, useMemo, useState } from "react";

import PerformanceLabHeader from "../components/performance-lab/PerformanceLabHeader";
import PerformanceKpiCards from "../components/performance-lab/PerformanceKpiCards";
import PerformanceComparison from "../components/performance-lab/PerformanceComparison";
import PerformanceCharts from "../components/performance-lab/PerformanceCharts";
import FleetUtilization from "../components/performance-lab/FleetUtilization";
import KeyFindings from "../components/performance-lab/KeyFindings";
import RunHistory from "../components/performance-lab/RunHistory";
import RunStatus from "../components/performance-lab/RunStatus";
import PerformanceRunDetail from "../components/performance-lab/PerformanceRunDetail";
import PerformanceRouteMap from "../components/performance-lab/PerformanceRouteMap";
import ScenarioDetails from "../components/recovery-planner/ScenarioDetails";

import { getPerformanceLab, getPerformanceRunDetail } from "../api/evaluation";
import { runOptimization } from "../api/optimization";
import { getScenarios } from "../api/scenarios";
import type { PerformanceLabData, PerformanceMetrics } from "../types/performanceLab";
import type { BackendEvaluationResponse } from "../types/optimization";
import type { Scenario } from "../types/scenarios";

function metricPair(baseline: number | undefined, optimized: number | undefined, unit: string) {
  return typeof baseline === "number" && Number.isFinite(baseline) && typeof optimized === "number" && Number.isFinite(optimized)
    ? { baseline, optimized, unit, lowerIsBetter: true }
    : undefined;
}

function metricsFromDetail(evaluation: BackendEvaluationResponse | null): PerformanceMetrics | undefined {
  const before = evaluation?.baseline?.metrics;
  const after = evaluation?.candidate?.metrics;
  if (!before || !after) return undefined;
  const metrics: PerformanceMetrics = {
    averageWaitingTime: metricPair(before.avg_wait_min, after.avg_wait_min, "min"),
    unservedPassengers: metricPair(before.unserved_passengers, after.unserved_passengers, "passengers"),
    capacityViolations: metricPair(before.capacity_violations, after.capacity_violations, "violations"),
    vehicleDistance: metricPair(before.vehicle_km, after.vehicle_km, "km"),
    operatingCost: before.cost_available === true && after.cost_available === true
      ? metricPair(before.operating_cost, after.operating_cost, "cost units")
      : undefined,
  };
  return Object.values(metrics).some((metric) => metric !== undefined) ? metrics : undefined;
}

export default function PerformanceLab() {
  const [data, setData] = useState<PerformanceLabData | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);

  const [selectedScenarioId, setSelectedScenarioId] = useState("normal");
  const [selectedRunId, setSelectedRunId] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<BackendEvaluationResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(true);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchEvaluation() {
      try {
        setIsLoading(true);
        setError(null);

        const [evaluationData, scenarioData] = await Promise.all([getPerformanceLab(), getScenarios()]);

        if (!isMounted) return;

        setData(evaluationData);
        setScenarios(scenarioData);

        const firstRun = evaluationData.runs[0];
        const initialScenarioId = firstRun?.scenarioId ?? scenarioData.find((scenario) => scenario.id === "normal")?.id ?? scenarioData[0]?.id ?? "normal";
        setSelectedScenarioId(initialScenarioId);
        setSelectedRunId(evaluationData.runs.find((run) => run.scenarioId === initialScenarioId)?.runId ?? "");
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

  const runs = useMemo(() => data?.runs ?? [], [data]);

  const scenarioOptions = useMemo(() => {
    const options = scenarios.map((scenario) => ({ value: scenario.id, label: scenario.name }));
    if (!options.length) {
      for (const run of runs) if (!options.some((scenario) => scenario.value === run.scenarioId)) options.push({ value: run.scenarioId, label: run.scenarioName });
    }
    return options.length ? options : [{ value: "normal", label: "Normal Operations" }];
  }, [runs, scenarios]);

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
  const selectedScenario = scenarios.find((scenario) => scenario.id === selectedScenarioId);

  function handleScenarioChange(scenarioId: string) {
    const firstRun = runs.find((run) => run.scenarioId === scenarioId);
    setSelectedScenarioId(scenarioId);
    setSelectedRunId(firstRun?.runId ?? "");
    setRunDetail(null);
    setDetailError(null);
    setDetailLoading(Boolean(firstRun));
  }

  function handleRunChange(runId: string) {
    const selected = runs.find((run) => run.runId === runId);
    if (selected) setSelectedScenarioId(selected.scenarioId);
    setSelectedRunId(runId);
    setRunDetail(null);
    setDetailError(null);
    setDetailLoading(Boolean(runId));
  }

  async function handleRunEvaluation() {
    const scenarioId = selectedScenarioId || "normal";
    setIsRunning(true);
    setDetailLoading(true);
    setRunError(null);
    try {
      const result = await runOptimization(scenarioId);
      setRunDetail(result.backendResult);
      setSelectedScenarioId(scenarioId);
      setSelectedRunId(result.runId);
      const refreshed = await getPerformanceLab();
      setData(refreshed);
      const matchingRun = refreshed.runs.find((run) => run.runId === result.runId);
      if (matchingRun) {
        setSelectedScenarioId(matchingRun.scenarioId);
        setSelectedRunId(matchingRun.runId);
      }
    } catch (runFailure: unknown) {
      setRunError(runFailure instanceof Error ? runFailure.message : "Could not run the evaluation.");
      setDetailLoading(false);
    } finally {
      setIsRunning(false);
    }
  }

  const selectedRunDetail = runDetail && (
    runDetail.evaluation_id === selectedRun?.runId || runDetail.baseline?.run_id === selectedRun?.runId
  ) ? runDetail : null;
  const detailedMetrics = useMemo(() => metricsFromDetail(selectedRunDetail), [selectedRunDetail]);
  const metrics = selectedRun?.metrics ?? detailedMetrics;
  const fleetUtilization = useMemo(() => {
    const summarize = (run: NonNullable<BackendEvaluationResponse["baseline"]>) => {
      const tripsByVehicle = new Map<string, Map<string, { first: number; last: number }>>();
      for (const event of run.vehicle_histories) {
        if (!event.trip_id) continue;
        const trips = tripsByVehicle.get(event.vehicle_id) ?? new Map<string, { first: number; last: number }>();
        const range = trips.get(event.trip_id) ?? { first: event.time_min, last: event.time_min };
        range.first = Math.min(range.first, event.time_min);
        range.last = Math.max(range.last, event.time_min);
        trips.set(event.trip_id, range);
        tripsByVehicle.set(event.vehicle_id, trips);
      }
      return new Map([...tripsByVehicle].map(([vehicleId, trips]) => {
        const activeMinutes = [...trips.values()].reduce((sum, range) => sum + Math.max(0, range.last - range.first), 0);
        return [vehicleId, Math.min(100, (activeMinutes / Math.max(1, run.horizon_min)) * 100)];
      }));
    };
    const baseline = selectedRunDetail?.baseline ? summarize(selectedRunDetail.baseline) : new Map<string, number>();
    const optimized = selectedRunDetail?.candidate ? summarize(selectedRunDetail.candidate) : new Map<string, number>();
    return [...baseline.keys()].filter((vehicleId) => optimized.has(vehicleId)).sort().map((vehicleId) => ({
      vehicleId,
      baseline: Number(baseline.get(vehicleId)!.toFixed(1)),
      optimized: Number(optimized.get(vehicleId)!.toFixed(1)),
    }));
  }, [selectedRunDetail]);

  useEffect(() => {
    if (!selectedRun?.runId || selectedRun.runId === "unknown") return;
    let isMounted = true;
    void getPerformanceRunDetail(selectedRun.runId)
      .then((detail) => { if (isMounted) setRunDetail(detail); })
      .catch((fetchError: unknown) => {
        if (isMounted) setDetailError(fetchError instanceof Error ? fetchError.message : "Could not load complete run detail.");
      })
      .finally(() => { if (isMounted) setDetailLoading(false); });
    return () => { isMounted = false; };
  }, [selectedRun?.runId]);

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
        onRunEvaluation={handleRunEvaluation}
        isRunning={isRunning}
      />

      {selectedScenario && <ScenarioDetails scenario={selectedScenario} />}

      {runError && <p role="alert" className="rounded-lg border border-danger-border bg-danger-soft p-3 text-sm text-danger">{runError}</p>}

      {!selectedRun ? <RunStatus type="no-run" /> : (
        <>
          {selectedRun.status === "infeasible" && <RunStatus type="infeasible" />}
          {!metrics && !selectedRunDetail && !detailLoading && <RunStatus type="no-metrics" />}
          {metrics && <>
          <PerformanceKpiCards metrics={metrics} />

          <PerformanceComparison metrics={metrics} />

          <PerformanceCharts metrics={metrics} evaluation={selectedRunDetail} />

          <PerformanceRouteMap evaluation={selectedRunDetail} />

          <FleetUtilization
            vehicles={fleetUtilization.length ? fleetUtilization : selectedRun.fleetUtilization ?? []}
          />

          <KeyFindings
            metrics={metrics}
            keyFinding={selectedRun.keyFinding}
          />
          </>}
        </>
      )}

      {selectedRun && <PerformanceRunDetail evaluation={selectedRunDetail} loading={detailLoading} error={detailError} />}
      <RunHistory
        runs={runs}
        selectedRunId={selectedRun?.runId ?? ""}
        onSelectRun={handleRunChange}
      />
    </div>
  );
}
