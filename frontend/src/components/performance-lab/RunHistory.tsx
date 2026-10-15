import { CheckCircle2, Clock3, XCircle } from "lucide-react";

import type { PerformanceRun } from "../../types/performanceLab";

type RunHistoryProps = {
  runs: PerformanceRun[];
  selectedRunId: string;
  onSelectRun: (runId: string) => void;
};

function formatDate(dateString: string) {
  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return dateString;
  }

  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function StatusBadge({ status }: { status: PerformanceRun["status"] }) {
  if (status === "completed") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        <CheckCircle2 size={14} />
        Completed
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700">
      <XCircle size={14} />
      Infeasible
    </span>
  );
}

export default function RunHistory({
  runs,
  selectedRunId,
  onSelectRun,
}: RunHistoryProps) {
  return (
    <section className="min-w-0 rounded-xl border border-border bg-white">
      <div className="border-b border-border p-4 sm:p-5">
        <h3 className="font-semibold text-foreground">Run History</h3>
        <p className="mt-1 text-sm text-secondary">
          Review previous evaluations for this scenario.
        </p>
      </div>

      {runs.length === 0 ? (
        <div className="px-5 py-10 text-center">
          <Clock3 size={25} className="mx-auto text-secondary" />
          <p className="mt-3 text-sm font-medium text-foreground">
            No evaluation runs yet
          </p>
          <p className="mt-1 text-sm text-secondary">
            Completed evaluations will appear here.
          </p>
        </div>
      ) : (
        <div className="min-w-0 overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-secondary">
              <tr>
                <th className="px-4 py-3 font-medium sm:px-5">Run</th>
                <th className="px-4 py-3 font-medium">Scenario</th>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border">
              {runs.map((run) => {
                const isSelected = run.runId === selectedRunId;

                return (
                  <tr
                    key={run.runId}
                    className={
                      isSelected ? "bg-blue-50/60" : "hover:bg-slate-50"
                    }
                  >
                    <td className="whitespace-nowrap px-4 py-4 font-medium text-foreground sm:px-5">
                      #{run.runId}
                    </td>

                    <td className="px-4 py-4 text-secondary">
                      {run.scenarioName}
                    </td>

                    <td className="whitespace-nowrap px-4 py-4 text-secondary">
                      {formatDate(run.createdAt)}
                    </td>

                    <td className="px-4 py-4">
                      <StatusBadge status={run.status} />
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        onClick={() => onSelectRun(run.runId)}
                        aria-pressed={isSelected}
                        className="min-h-10 rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                      >
                        {isSelected ? "Selected" : "View Run"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
