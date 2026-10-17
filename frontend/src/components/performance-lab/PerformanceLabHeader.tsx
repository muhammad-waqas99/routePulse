import { Activity, Play } from "lucide-react";
import type { PerformanceRun } from "../../types/performanceLab";
import { scenarioLabel } from "../../lib/presentation";

type ScenarioOption = {
  value: string;
  label: string;
};

type PerformanceLabHeaderProps = {
  scenarios: ScenarioOption[];
  runs: PerformanceRun[];
  selectedScenarioId: string;
  selectedRunId: string;
  onScenarioChange: (scenarioId: string) => void;
  onRunChange: (runId: string) => void;
  onRunEvaluation: () => void;
  isRunning: boolean;
};

function runDate(value: string) {
  const date = new Date(value);
  return value && !Number.isNaN(date.getTime()) ? date.toLocaleString() : "Saved run";
}

export default function PerformanceLabHeader({
  scenarios,
  runs,
  selectedScenarioId,
  selectedRunId,
  onScenarioChange,
  onRunChange,
  onRunEvaluation,
  isRunning,
}: PerformanceLabHeaderProps) {
  return (
    <section className="flex min-w-0 flex-col gap-4 rounded-xl border border-border bg-white p-4 sm:p-6 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-sm font-medium text-primary">
          <Activity size={17} />
          Simulation Analytics
        </div>

        <h2 className="mt-2 text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
          Performance Lab
        </h2>

      </div>

      <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 lg:w-[min(100%,34rem)]">
        <label className="min-w-0 text-sm font-medium text-foreground">
          Scenario
          <select
            value={selectedScenarioId}
            onChange={(event) => onScenarioChange(event.target.value)}
            className="mt-2 min-h-11 w-full min-w-0 rounded-lg border border-border bg-white px-3 text-sm font-normal outline-none focus:border-primary focus:ring-2 focus:ring-primary/15"
          >
            {scenarios.map((scenario) => (
              <option key={scenario.value} value={scenario.value}>
                {scenario.label}
              </option>
            ))}
          </select>
        </label>

        <label className="min-w-0 text-sm font-medium text-foreground">
          Saved run
          <select
            value={selectedRunId}
            onChange={(event) => onRunChange(event.target.value)}
          className="mt-2 min-h-11 w-full min-w-0 rounded-lg border border-border bg-white px-3 text-sm font-normal outline-none focus:border-primary focus:ring-2 focus:ring-primary/15"
          >
            {!runs.length && <option value="">No saved runs</option>}
            {runs.map((run) => (
              <option key={run.runId} value={run.runId}>
                {runDate(run.createdAt)} · {scenarioLabel(run.scenarioName)} · {run.status === "completed" ? "Feasible" : "Infeasible"}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={onRunEvaluation}
          disabled={isRunning}
          aria-busy={isRunning}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 disabled:cursor-wait disabled:opacity-60 sm:col-span-2"
        >
          <Play size={16} fill="currentColor" />
          {isRunning ? "Running evaluation…" : "Run optimization and analysis"}
        </button>
      </div>
    </section>
  );
}
