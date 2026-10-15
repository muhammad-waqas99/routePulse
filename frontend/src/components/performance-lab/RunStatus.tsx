import { Activity, AlertTriangle, Database } from "lucide-react";

type RunStatusProps = {
  type: "no-run" | "infeasible" | "no-metrics";
  runId?: string;
};

const statusContent = {
  "no-run": {
    title: "No evaluation runs available",
    description:
      "Run an evaluation to view its performance results here.",
    icon: Activity,
    iconClass: "text-secondary",
  },
  infeasible: {
    title: "Optimization run is infeasible",
    description:
      "A feasible plan was not found or the candidate plan failed validation. Performance metrics are unavailable for this run.",
    icon: AlertTriangle,
    iconClass: "text-red-600",
  },
  "no-metrics": {
    title: "Metrics unavailable",
    description:
      "This run does not contain saved performance metrics.",
    icon: Database,
    iconClass: "text-secondary",
  },
};

export default function RunStatus({ type, runId }: RunStatusProps) {
  const content = statusContent[type];
  const Icon = content.icon;

  return (
    <section
      role="status"
      className={`rounded-xl border bg-white p-5 sm:p-6 ${
        type === "infeasible" ? "border-red-200" : "border-border"
      }`}
    >
      <div className="flex items-start gap-3">
        <Icon
          size={23}
          className={`mt-0.5 shrink-0 ${content.iconClass}`}
        />

        <div className="min-w-0">
          <h3 className="font-semibold text-foreground">
            {content.title}
            {runId ? ` · Run #${runId}` : ""}
          </h3>

          <p className="mt-1 text-sm leading-6 text-secondary">
            {content.description}
          </p>
        </div>
      </div>
    </section>
  );
}
