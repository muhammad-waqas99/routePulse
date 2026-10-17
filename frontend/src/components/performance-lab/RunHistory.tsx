import { useMemo, useState } from "react";
import { CheckCircle2, Clock3, XCircle } from "lucide-react";
import type { PerformanceRun } from "../../types/performanceLab";
import { scenarioLabel } from "../../lib/presentation";

type RunHistoryProps = {
  runs: PerformanceRun[];
  selectedRunId: string;
  onSelectRun: (runId: string) => void;
};

function formatDate(dateString: string) {
  if (!dateString) return "Saved evaluation";
  const date = new Date(dateString);
  return Number.isNaN(date.getTime()) ? "Saved evaluation" : new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export default function RunHistory({ runs, selectedRunId, onSelectRun }: RunHistoryProps) {
  const [visibleCount, setVisibleCount] = useState(6);
  const recentRuns = useMemo(() => [...runs].sort((a, b) => {
    const aTime = Date.parse(a.createdAt) || 0;
    const bTime = Date.parse(b.createdAt) || 0;
    return bTime - aTime;
  }), [runs]);
  const visibleRuns = recentRuns.slice(0, visibleCount);

  return (
    <section className="min-w-0 rounded-xl border border-border bg-surface">
      <div className="border-b border-border p-4 sm:p-5">
        <h3 className="font-semibold text-foreground">Recent runs</h3>
      </div>
      {runs.length === 0 ? (
        <div className="px-5 py-10 text-center"><Clock3 size={25} className="mx-auto text-secondary" /><p className="mt-3 text-sm font-medium text-foreground">No evaluation runs yet</p><p className="mt-1 text-sm text-secondary">Completed evaluations will appear here.</p></div>
      ) : (
        <ul className="grid min-w-0 gap-3 p-3 sm:grid-cols-2 sm:p-4 xl:grid-cols-3">
          {visibleRuns.map((run) => {
            const selected = run.runId === selectedRunId;
            const feasible = run.status === "completed";
            const result = run.metrics?.averageWaitingTime ?? run.metrics?.unservedPassengers ?? run.metrics?.vehicleDistance ?? run.metrics?.operatingCost;
            const resultLabel = run.metrics?.averageWaitingTime ? "Wait" : run.metrics?.unservedPassengers ? "Unserved" : run.metrics?.vehicleDistance ? "Distance" : run.metrics?.operatingCost ? "Cost" : "";
            const resultChange = result ? result.optimized - result.baseline : null;
            const improved = result && resultChange !== null && (result.lowerIsBetter ? resultChange < 0 : resultChange > 0);
            return <li key={run.runId} className={`min-w-0 rounded-lg border p-3 ${selected ? "border-primary bg-primary-soft/50" : "border-border bg-white"}`}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0"><p className="truncate text-sm font-semibold text-foreground">{scenarioLabel(run.scenarioName)}</p><p className="mt-1 text-xs text-secondary">{formatDate(run.createdAt)}</p></div>
                <span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-1 text-[11px] font-medium ${feasible ? "bg-success-soft text-success" : "bg-danger-soft text-danger"}`}>{feasible ? <CheckCircle2 size={13} /> : <XCircle size={13} />}{feasible ? "Feasible" : "Infeasible"}</span>
              </div>
              {result && resultChange !== null && <p className={`mt-2 inline-flex rounded-full px-2 py-1 text-xs font-medium ${resultChange === 0 ? "bg-surface-secondary text-secondary" : improved ? "bg-success-soft text-success" : "bg-warning-soft text-warning"}`}>
                {resultChange === 0 ? "No change" : `${improved ? "Improved" : "Trade-off"} · `}{resultLabel} {resultChange > 0 ? "+" : resultChange < 0 ? "−" : ""}{Math.abs(resultChange).toLocaleString(undefined, { maximumFractionDigits: 1 })}{result.unit === "min" ? " min" : result.unit === "km" ? " km" : result.unit === "cost units" ? " units" : ""}
              </p>}
              <button type="button" onClick={() => onSelectRun(run.runId)} aria-pressed={selected} className="mt-3 min-h-10 w-full rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30">{selected ? "Selected run" : "View analysis"}</button>
            </li>;
          })}
        </ul>
      )}
      {recentRuns.length > visibleRuns.length && <div className="px-4 pb-4 text-center"><button type="button" onClick={() => setVisibleCount((count) => count + 6)} className="min-h-10 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary">Show more runs</button></div>}
    </section>
  );
}
