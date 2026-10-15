import { Activity } from "lucide-react";
import type { PerformanceRun } from "../../types/performanceLab";

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
};

export default function PerformanceLabHeader({
  scenarios,
  runs,
  selectedScenarioId,
  selectedRunId,
  onScenarioChange,
  onRunChange,
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

        <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">
          Compare the original timetable with the optimized plan
          using simulation-based performance metrics.
        </p>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 lg:w-[min(100%,30rem)]">
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
          Evaluation Run
          <select
            value={selectedRunId}
            onChange={(event) => onRunChange(event.target.value)}
          className="mt-2 min-h-11 w-full min-w-0 rounded-lg border border-border bg-white px-3 text-sm font-normal outline-none focus:border-primary focus:ring-2 focus:ring-primary/15"
          >
            {runs.map((run) => (
              <option key={run.runId} value={run.runId}>
                #{run.runId} · {run.status}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
