import {
  Play,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

import { scenarios } from "../config/scenarios";
import ScenarioSelector from "../components/recovery-planner/ScenarioSelector";
import ScenarioDetails from "../components/recovery-planner/ScenarioDetails";
import OptimizationProgress from "../components/recovery-planner/OptimizationProgress";
import TimetableComparison from "../components/recovery-planner/TimetableComparison";
import ConstraintValidation from "../components/recovery-planner/ConstraintValidation";

import { useMockOptimization } from "../hooks/useMockOptimization";

import { useState } from "react";

interface RecoveryPlannerProps {
  onViewPerformance: () => void;
}

export default function RecoveryPlanner({
  onViewPerformance,
}: RecoveryPlannerProps) {
   

  const [selectedScenarioId, setSelectedScenarioId] =
    useState("normal_operations");

  const {
    stage,
    result,
    isRunning,
    run,
    reset,
  } = useMockOptimization();

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


      <ScenarioSelector
        scenarios={scenarios}
        selectedScenarioId={selectedScenarioId}
        disabled={isRunning}
        onSelect={handleSelectScenario}
      />

      {selectedScenario && (
        <ScenarioDetails scenario={selectedScenario} />
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
          onClick={run}
          disabled={isRunning}
          className="mt-5 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-wait disabled:opacity-70 sm:w-auto"
        >
          {isRunning ? (
            <span className="animate-spin">◌</span>
          ) : (
            <Play size={16} />
          )}
          {isRunning ? "Running optimization..." : "Run Optimization"}
        </button>

        {isRunning && <OptimizationProgress stage={stage} />}

        {!isRunning && !result && (
          <div className="mt-6 flex min-h-52 flex-col items-center justify-center rounded-lg border border-dashed border-border px-5 py-8 text-center">
            <div className="rounded-full bg-slate-100 p-3 text-secondary">
              <ShieldCheck size={23} />
            </div>
            <h3 className="mt-4 font-semibold text-foreground">
              No optimization run yet
            </h3>
            <p className="mt-2 max-w-md text-sm leading-6 text-secondary">
              Select a scenario and run the demo to see the proposed
              timetable, constraint checks, and evaluation metrics.
            </p>
          </div>
        )}

        {result && !isRunning && (
          <div className="mt-6 min-w-0 space-y-6">
            <div className="flex flex-col gap-3 rounded-xl border border-border bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3">
                <CheckCircle2
                  size={22}
                  className="mt-0.5 shrink-0 text-emerald-600"
                />
                <div>
                  <h3 className="font-semibold text-foreground">
                    Demo run completed
                  </h3>
                  <p className="mt-1 text-sm text-secondary">
                    Scenario: {selectedScenario?.name}
                  </p>
                </div>
              </div>

              <span className="w-fit rounded-full border border-border bg-white px-3 py-1.5 text-xs font-medium capitalize text-foreground">
                {result.status} solution
              </span>
            </div>

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
                Want to test another run?
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
