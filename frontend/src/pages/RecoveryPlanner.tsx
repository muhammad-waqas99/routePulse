
import {
  Play,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

import { useEffect, useState } from "react";

import { getScenarios } from "../api/scenarios";
import type { Scenario } from "../types/scenarios";

import ScenarioSelector from "../components/recovery-planner/ScenarioSelector";
import ScenarioDetails from "../components/recovery-planner/ScenarioDetails";
import OptimizationProgress from "../components/recovery-planner/OptimizationProgress";
import TimetableComparison from "../components/recovery-planner/TimetableComparison";
import ConstraintValidation from "../components/recovery-planner/ConstraintValidation";

import { useOptimization } from "../hooks/useOptimization"

interface RecoveryPlannerProps {
  onViewPerformance: () => void;
}

export default function RecoveryPlanner({
  onViewPerformance,
}: RecoveryPlannerProps) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenariosLoading, setScenariosLoading] = useState(true);
  const [scenariosError, setScenariosError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [selectedScenarioId, setSelectedScenarioId] = useState("");

  const {
    stage,
    result,
    error: optimizationError,
    isRunning,
    run,
    reset,
  } = useOptimization();

  useEffect(() => {
    let cancelled = false;

    async function loadScenarios() {
      setScenariosLoading(true);
      setScenariosError(null);

      try {
        const data = await getScenarios();

        if (cancelled) return;

        setScenarios(data);

        setSelectedScenarioId((currentId) => {
          if (data.some((scenario) => scenario.id === currentId)) {
            return currentId;
          }

          return (
            data.find((scenario) => scenario.id === "normal_operations")
              ?.id ??
            data[0]?.id ??
            ""
          );
        });
      } catch (error: unknown) {
        if (cancelled) return;

        setScenariosError(
          error instanceof Error
            ? error.message
            : "Failed to load scenarios.",
        );
      } finally {
        if (!cancelled) {
          setScenariosLoading(false);
        }
      }
    }

    void loadScenarios();

    return () => {
      cancelled = true;
    };
  }, [retryCount]);

  const selectedScenario = scenarios.find(
    (scenario) => scenario.id === selectedScenarioId,
  );

  function handleSelectScenario(scenarioId: string) {
    if (isRunning) return;

    setSelectedScenarioId(scenarioId);
    reset();
  }

  return (
    <div className="min-w-0 space-y-6">
      {scenariosLoading ? (
        <div
          className="rounded-xl border border-border bg-white p-5"
          role="status"
        >
          <p className="text-sm text-secondary">
            Loading scenarios...
          </p>
        </div>
      ) : scenariosError ? (
        <div
          className="rounded-xl border border-border bg-white p-5"
          role="alert"
        >
          <h2 className="font-semibold text-foreground">
            Unable to load scenarios
          </h2>

          <p className="mt-2 break-words text-sm text-secondary">
            {scenariosError}
          </p>

          <button
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
            className="mt-4 min-h-11 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Retry
          </button>
        </div>
      ) : scenarios.length === 0 ? (
        <div className="rounded-xl border border-border bg-white p-5">
          <p className="text-sm text-secondary">
            No scenarios are available.
          </p>

          <button
            type="button"
            onClick={() => setRetryCount((count) => count + 1)}
            className="mt-4 min-h-11 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Reload Scenarios
          </button>
        </div>
      ) : (
        <>
          <ScenarioSelector
            scenarios={scenarios}
            selectedScenarioId={selectedScenarioId}
            disabled={isRunning}
            onSelect={handleSelectScenario}
          />

          {selectedScenario && (
            <ScenarioDetails scenario={selectedScenario} />
          )}
        </>
      )}

      <section className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-6">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            Run Optimization
          </h2>

          <p className="mt-1 text-sm text-secondary">
            Generate a constraint-aware plan for the selected scenario.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void run(selectedScenarioId)}
          disabled={
            isRunning ||
            scenariosLoading ||
            !selectedScenario ||
            Boolean(scenariosError)
          }
          className="mt-5 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {isRunning ? (
            <span className="animate-spin" aria-hidden="true">
              ◌
            </span>
          ) : (
            <Play size={16} />
          )}

          {isRunning ? "Running optimization..." : "Run Optimization"}
        </button>

        {optimizationError && (
          <div
            className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4"
            role="alert"
          >
            <h3 className="font-medium text-red-800">
              Optimization request failed
            </h3>

            <p className="mt-1 break-words text-sm text-red-700">
              {optimizationError}
            </p>

            <button
              type="button"
              onClick={() => void run(selectedScenarioId)}
              disabled={!selectedScenarioId}
              className="mt-3 min-h-10 rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-100 disabled:opacity-60"
            >
              Try Again
            </button>
          </div>
        )}

        {isRunning && <OptimizationProgress stage={stage} />}

        {!isRunning && !result && !optimizationError && (
          <div className="mt-6 flex min-h-52 flex-col items-center justify-center rounded-lg border border-dashed border-border px-5 py-8 text-center">
            <div className="rounded-full bg-slate-100 p-3 text-secondary">
              <ShieldCheck size={23} />
            </div>

            <h3 className="mt-4 font-semibold text-foreground">
              No optimization run yet
            </h3>

            <p className="mt-2 max-w-md text-sm leading-6 text-secondary">
              Select a scenario and run the optimization to view the
              proposed timetable, validation results, and metrics.
            </p>
          </div>
        )}

        {result && !isRunning && (
          <div className="mt-6 min-w-0 space-y-6">
            <div
              className={`flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between ${
                result.status === "optimal"
                  ? "border-emerald-200 bg-emerald-50"
                  : "border-amber-200 bg-amber-50"
              }`}
            >
              <div className="flex min-w-0 items-start gap-3">
                {result.status === "optimal" ? (
                  <CheckCircle2
                    size={22}
                    className="mt-0.5 shrink-0 text-emerald-600"
                  />
                ) : (
                  <AlertTriangle
                    size={22}
                    className="mt-0.5 shrink-0 text-amber-700"
                  />
                )}

                <div className="min-w-0">
                  <h3 className="font-semibold text-foreground">
                    {result.status === "optimal"
                      ? "Optimization completed"
                      : "No feasible solution found"}
                  </h3>

                  <p className="mt-1 text-sm text-secondary">
                    Scenario: {result.scenarioName}
                  </p>

                  {result.message && (
                    <p className="mt-2 break-words text-sm text-secondary">
                      {result.message}
                    </p>
                  )}

                  <p className="mt-2 text-xs text-secondary">
                    Run ID: {result.runId}
                  </p>
                </div>
              </div>

              <span className="w-fit shrink-0 rounded-full border border-border bg-white px-3 py-1.5 text-xs font-medium capitalize text-foreground">
                {result.status}
              </span>
            </div>

            {result.warnings.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <h3 className="font-semibold text-amber-900">
                  Optimization warnings
                </h3>

                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">
                  {result.warnings.map((warning, index) => (
                    <li key={`${index}-${warning}`}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            <TimetableComparison result={result} />

            <ConstraintValidation result={result} />

            <button
              type="button"
              onClick={onViewPerformance}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white transition hover:opacity-90 sm:w-auto"
            >
              View Full Performance
            </button>

            <div className="flex flex-col gap-3 border-t border-border pt-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-secondary">
                Want to test another scenario?
              </p>

              <button
                type="button"
                onClick={reset}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-foreground transition hover:bg-slate-50"
              >
                <RotateCcw size={16} />
                Reset Results
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
