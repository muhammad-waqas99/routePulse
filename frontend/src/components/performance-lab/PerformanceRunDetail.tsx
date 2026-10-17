import { useMemo } from "react";
import { CheckCircle2, CircleHelp, Route, ShieldAlert, TrendingUp } from "lucide-react";
import type { BackendEvaluationResponse, BackendPlan } from "../../types/optimization";
import { humanizeIdentifier, scenarioLabel } from "../../lib/presentation";

interface Props {
  evaluation: BackendEvaluationResponse | null;
  loading: boolean;
  error: string | null;
}

type Assignment = NonNullable<BackendPlan>["assignments"][number];
type Change = { ordinal: number; before: Assignment | null; after: Assignment | null; label: string };

function clock(minutes: number) {
  const day = Math.floor(minutes / 1440);
  const normalized = ((Math.trunc(minutes) % 1440) + 1440) % 1440;
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}${day ? ` +${day}d` : ""}`;
}

function serviceText(value: Assignment | null) {
  if (!value) return "—";
  return `${humanizeIdentifier(value.route_id)} · ${humanizeIdentifier(value.vehicle_id)} · ${clock(value.departure_min)}`;
}

function humanizeDetail(value: string) {
  return value.replace(/\b(route|vehicle|bus|stop|trip)[_-]?(\d+)\b/gi, (_match, kind: string, digits: string) => `${kind.toLowerCase() === "bus" ? "Vehicle" : kind[0].toUpperCase() + kind.slice(1)} ${Number(digits)}`);
}

function changedAssignments(beforePlan: BackendPlan | null, afterPlan: BackendPlan | null): Change[] {
  const before = beforePlan ? [...beforePlan.assignments, ...beforePlan.extra_trips] : [];
  const after = afterPlan ? [...afterPlan.assignments, ...afterPlan.extra_trips] : [];
  const beforeByTrip = new Map(before.map((row) => [row.trip_id, row]));
  const afterByTrip = new Map(after.map((row) => [row.trip_id, row]));
  const changes: Change[] = [];
  let ordinal = 1;
  for (const old of before) {
    const next = afterByTrip.get(old.trip_id) ?? null;
    if (!next) changes.push({ ordinal: ordinal++, before: old, after: null, label: "Removed" });
    else if (old.route_id !== next.route_id || old.vehicle_id !== next.vehicle_id || old.departure_min !== next.departure_min) {
      const changedFields = [old.route_id !== next.route_id && "Route", old.vehicle_id !== next.vehicle_id && "Vehicle", old.departure_min !== next.departure_min && "Time"].filter(Boolean).join(" · ");
      changes.push({ ordinal: ordinal++, before: old, after: next, label: changedFields });
    }
  }
  for (const next of after) {
    if (!beforeByTrip.has(next.trip_id)) changes.push({ ordinal: ordinal++, before: null, after: next, label: "Added" });
  }
  return changes;
}

export default function PerformanceRunDetail({ evaluation, loading, error }: Props) {
  const changes = useMemo(() => changedAssignments(evaluation?.baseline_plan ?? null, evaluation?.candidate_plan ?? null), [evaluation]);

  if (loading) return <section className="rounded-xl border border-border bg-white p-5 text-sm text-secondary">Loading operational analysis…</section>;
  if (error) return <section className="rounded-xl border border-warning-border bg-warning-soft p-4 text-sm text-warning">Run detail could not be loaded: {error}</section>;
  if (!evaluation) return null;

  const candidate = evaluation.candidate;
  const validation = evaluation.comparison.candidate_validation;
  const eventCounts = Object.entries((candidate?.events ?? []).reduce<Record<string, number>>((counts, event) => {
    counts[event.event_type] = (counts[event.event_type] ?? 0) + 1;
    return counts;
  }, {})).sort((a, b) => b[1] - a[1]);
  const extraTrips = evaluation.candidate_plan?.extra_trips.length ?? 0;
  const unassignedTrips = evaluation.candidate_plan?.unassigned_trip_ids.length ?? 0;
  const violations = validation?.violations ?? [];
  const unverified = validation?.unverified_constraints ?? [];
  const findings = [...violations.map((issue) => ({ type: "Issue", text: issue.message ?? issue.detail ?? issue.reason ?? (issue.code ? humanizeIdentifier(issue.code) : "Constraint issue") })), ...unverified.map((issue) => ({ type: "Review", text: issue.reason ?? (issue.code ? humanizeIdentifier(issue.code) : "Could not be verified") }))];

  const affectedRoutes = new Set<string>();
  const affectedVehicles = new Set<string>();
  for (const change of changes) {
    for (const assignment of [change.before, change.after]) {
      if (assignment) {
        affectedRoutes.add(assignment.route_id);
        affectedVehicles.add(assignment.vehicle_id);
      }
    }
  }

  const summaries = [
    { label: "Services changed", value: changes.length, icon: <Route size={17} />, tone: "primary" },
    { label: "Routes affected", value: affectedRoutes.size, icon: <Route size={17} />, tone: "primary" },
    { label: "Vehicles involved", value: affectedVehicles.size, icon: <TrendingUp size={17} />, tone: "primary" },
    { label: "New services", value: extraTrips, icon: <TrendingUp size={17} />, tone: "good" },
    { label: "Unassigned services", value: unassignedTrips, icon: <ShieldAlert size={17} />, tone: "warning" },
    { label: "Constraint findings", value: findings.length, icon: <CircleHelp size={17} />, tone: "warning" },
  ].filter((item) => item.value > 0);

  const shownChanges = changes.slice(0, 6);

  return (
    <section className="min-w-0 space-y-4 rounded-xl border border-border bg-surface p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-foreground">Operational analysis</h3>
          <p className="mt-1 text-sm text-secondary">{scenarioLabel(evaluation.scenario_id)}</p>
        </div>
        <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold ${candidate?.feasible ? "bg-success-soft text-success" : "bg-danger-soft text-danger"}`}>
          {candidate?.feasible ? <CheckCircle2 size={14} /> : <ShieldAlert size={14} />}
          {candidate?.feasible ? "Feasible" : "Needs review"}
        </span>
      </div>

      {summaries.length > 0 && <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {summaries.map((item) => <article key={item.label} className={`min-w-0 rounded-lg border p-3 ${item.tone === "warning" ? "border-warning-border bg-warning-soft/50" : item.tone === "good" ? "border-success-border bg-success-soft/50" : "border-border bg-white"}`}>
          <div className="flex items-center justify-between gap-2"><p className="text-xs font-medium text-secondary">{item.label}</p><span className={item.tone === "warning" ? "text-warning" : item.tone === "good" ? "text-success" : "text-primary"}>{item.icon}</span></div>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-foreground">{item.value.toLocaleString()}</p>
        </article>)}
      </div>}

      {changes.length > 0 && <section className="min-w-0 overflow-hidden rounded-lg border border-border bg-white">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border p-3 sm:px-4">
          <h4 className="text-sm font-semibold text-foreground">Service changes</h4>
          <span className="rounded-full bg-primary-soft px-2.5 py-1 text-xs font-medium text-primary">{Math.min(changes.length, shownChanges.length)} of {changes.length.toLocaleString()}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="hidden w-full min-w-[500px] text-left text-sm md:table">
            <thead className="bg-surface-secondary text-xs text-secondary"><tr><th className="px-3 py-2.5 font-medium">Service</th><th className="px-3 py-2.5 font-medium">Change</th><th className="px-3 py-2.5 font-medium">Before</th><th className="px-3 py-2.5 font-medium">After</th></tr></thead>
            <tbody className="divide-y divide-border">{shownChanges.map((change) => <tr key={change.ordinal} className="transition-colors hover:bg-surface-secondary/70"><td className="whitespace-nowrap px-3 py-2.5 font-medium text-foreground">Service {change.ordinal}</td><td className="px-3 py-2.5"><span className={`rounded-full px-2 py-1 text-xs font-medium ${change.label === "Added" ? "bg-success-soft text-success" : change.label === "Removed" ? "bg-danger-soft text-danger" : "bg-warning-soft text-warning"}`}>{change.label}</span></td><td className="max-w-56 break-words px-3 py-2.5 text-secondary">{serviceText(change.before)}</td><td className="max-w-56 break-words px-3 py-2.5 font-medium text-foreground">{serviceText(change.after)}</td></tr>)}</tbody>
          </table>
          <ul className="divide-y divide-border md:hidden">
            {shownChanges.map((change) => <li key={change.ordinal} className="space-y-2 p-3 text-sm">
              <div className="flex items-center justify-between gap-2"><span className="font-medium text-foreground">Service {change.ordinal}</span><span className={`rounded-full px-2 py-1 text-xs font-medium ${change.label === "Added" ? "bg-success-soft text-success" : change.label === "Removed" ? "bg-danger-soft text-danger" : "bg-warning-soft text-warning"}`}>{change.label}</span></div>
              <div className="grid grid-cols-2 gap-2"><div className="min-w-0"><p className="text-xs text-secondary">Before</p><p className="break-words text-secondary">{serviceText(change.before)}</p></div><div className="min-w-0"><p className="text-xs text-secondary">After</p><p className="break-words text-foreground">{serviceText(change.after)}</p></div></div>
            </li>)}
          </ul>
        </div>
      </section>}

      <div className="grid min-w-0 gap-4 lg:grid-cols-2">
        {eventCounts.length > 0 && <section className="min-w-0 rounded-lg border border-border bg-white p-3 sm:p-4">
          <h4 className="text-sm font-semibold text-foreground">Run activity</h4>
          <ul className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">{eventCounts.slice(0, 6).map(([event, count]) => <li key={event} className="min-w-0 rounded-lg bg-surface-secondary p-2.5"><p className="truncate text-xs text-secondary">{humanizeIdentifier(event)}</p><p className="mt-1 text-lg font-semibold tabular-nums text-foreground">{count.toLocaleString()}</p></li>)}</ul>
        </section>}

        <section className="min-w-0 rounded-lg border border-border bg-white p-3 sm:p-4">
          <div className="flex items-start justify-between gap-2"><h4 className="text-sm font-semibold text-foreground">Constraints</h4><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${validation?.feasible ? "bg-success-soft text-success" : "bg-warning-soft text-warning"}`}>{validation?.feasible ? "Passed" : "Review"}</span></div>
          {findings.length > 0 && <details className="mt-3 rounded-lg border border-border p-3"><summary className="cursor-pointer text-sm font-medium text-foreground">View {findings.length} finding{findings.length === 1 ? "" : "s"}</summary><ul className="mt-3 space-y-2">{findings.slice(0, 8).map((finding, index) => <li key={`${finding.type}-${index}`} className="rounded-md bg-surface-secondary p-2.5"><p className="text-xs font-medium text-secondary">{finding.type}</p><p className="mt-1 break-words text-sm text-foreground">{humanizeDetail(String(finding.text))}</p></li>)}</ul>{findings.length > 8 && <p className="mt-2 text-xs text-secondary">+{findings.length - 8} more</p>}</details>}
        </section>
      </div>
    </section>
  );
}
