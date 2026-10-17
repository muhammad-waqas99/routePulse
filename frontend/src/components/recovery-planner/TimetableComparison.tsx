import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { OptimizationResult, OptimizationTrip } from "../../types/optimization";
import { humanizeIdentifier } from "../../lib/presentation";

interface Props {
  result: OptimizationResult;
}

interface TripChange {
  id: string;
  before: OptimizationTrip | null;
  after: OptimizationTrip | null;
  labels: string[];
}

const categoryColors: Record<string, string> = {
  Changed: "var(--primary)",
  Unchanged: "var(--border-strong)",
  "Vehicle changed": "var(--info)",
  "Route changed": "var(--primary)",
  "Departure time changed": "var(--warning)",
  "Multiple changes": "var(--danger)",
  Added: "var(--success)",
  Unassigned: "var(--danger)",
};

function getLabels(before: OptimizationTrip | null, after: OptimizationTrip | null): string[] {
  if (!before && after) return ["Added"];
  if (before && !after) return ["Unassigned"];
  if (!before || !after) return [];

  const changes: string[] = [];
  if (before.routeId !== after.routeId) changes.push("Route changed");
  if (before.vehicleId !== after.vehicleId) changes.push("Vehicle changed");
  if (before.departureTime !== after.departureTime) changes.push("Departure time changed");
  return changes;
}

function categoryFor(labels: string[]) {
  if (labels.length > 1) return "Multiple changes";
  return labels[0] ?? "Unchanged";
}

function badgeTone(labels: string[]) {
  if (labels.includes("Added")) return "bg-success-soft text-success";
  if (labels.includes("Unassigned")) return "bg-danger-soft text-danger";
  if (labels.includes("Departure time changed")) return "bg-warning-soft text-warning";
  return "bg-primary-soft text-primary";
}

function hourLabel(value: string) {
  const hour = Number(value.slice(0, 2));
  return Number.isFinite(hour) ? `${String(hour).padStart(2, "0")}:00` : "Other";
}

function ChangeChart({ title, data, height = 180 }: { title: string; data: Array<{ name: string; count: number }>; height?: number }) {
  if (!data.length) return null;
  return (
    <article className="min-w-0 rounded-lg border border-border bg-white p-3 sm:p-4">
      <h4 className="text-sm font-semibold text-foreground">{title}</h4>
      <div className="mt-2 min-w-0" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 14, left: 0, bottom: 4 }} barCategoryGap="28%">
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" width={96} tick={{ fontSize: 10, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
            <Tooltip
              formatter={(value) => [Number(value).toLocaleString(), "Services"]}
              contentStyle={{ borderRadius: 10, borderColor: "var(--border)", background: "var(--surface)" }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={18}>
              {data.map((item) => <Cell key={item.name} fill={categoryColors[item.name] ?? "var(--primary)"} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

export default function TimetableComparison({ result }: Props) {
  const { changes, unchangedCount, categoryData, routeData, vehicleData, timeData } = useMemo(() => {
    const baselineById = new Map(result.originalTrips.map((trip) => [trip.tripId, trip]));
    const candidateById = new Map(result.proposedTrips.map((trip) => [trip.tripId, trip]));
    const changes: TripChange[] = [];
    const routeServices = new Map<string, Set<string>>();
    const vehicleChanges = new Map<string, number>();
    const timeChanges = new Map<string, number>();
    const categories = new Map<string, number>();
    let unchangedCount = 0;

    for (const before of result.originalTrips) {
      const after = candidateById.get(before.tripId) ?? null;
      const labels = getLabels(before, after);
      if (!labels.length) {
        unchangedCount += 1;
        continue;
      }
      changes.push({ id: before.tripId, before, after, labels });
      const category = categoryFor(labels);
      categories.set(category, (categories.get(category) ?? 0) + 1);

      const affectedRoutes = new Set([before.routeId, ...(after ? [after.routeId] : [])]);
      for (const routeId of affectedRoutes) {
        const services = routeServices.get(routeId) ?? new Set<string>();
        services.add(before.tripId);
        routeServices.set(routeId, services);
      }
      if (labels.includes("Vehicle changed") && after) {
        vehicleChanges.set(after.vehicleId, (vehicleChanges.get(after.vehicleId) ?? 0) + 1);
      }
      if (labels.includes("Departure time changed")) {
        const departure = after?.departureTime ?? before.departureTime;
        const hour = hourLabel(departure);
        timeChanges.set(hour, (timeChanges.get(hour) ?? 0) + 1);
      }
    }

    for (const after of result.proposedTrips) {
      if (baselineById.has(after.tripId)) continue;
      changes.push({ id: after.tripId, before: null, after, labels: ["Added"] });
      categories.set("Added", (categories.get("Added") ?? 0) + 1);
      const services = routeServices.get(after.routeId) ?? new Set<string>();
      services.add(after.tripId);
      routeServices.set(after.routeId, services);
    }

    for (const id of result.unassignedTripIds) {
      const before = baselineById.get(id);
      if (!before || candidateById.has(id) || changes.some((change) => change.id === id)) continue;
      changes.push({ id, before, after: null, labels: ["Unassigned"] });
      categories.set("Unassigned", (categories.get("Unassigned") ?? 0) + 1);
      const services = routeServices.get(before.routeId) ?? new Set<string>();
      services.add(id);
      routeServices.set(before.routeId, services);
    }

    return {
      changes,
      unchangedCount,
      categoryData: [...categories].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count),
      routeData: [...routeServices].map(([routeId, services]) => ({ name: humanizeIdentifier(routeId), count: services.size })).sort((a, b) => b.count - a.count).slice(0, 6),
      vehicleData: [...vehicleChanges].map(([vehicleId, count]) => ({ name: humanizeIdentifier(vehicleId), count })).sort((a, b) => b.count - a.count).slice(0, 6),
      timeData: [...timeChanges].map(([name, count]) => ({ name, count })).sort((a, b) => a.name.localeCompare(b.name)),
    };
  }, [result.originalTrips, result.proposedTrips, result.unassignedTripIds]);

  const textFor = (trip: OptimizationTrip | null) => trip
    ? `${humanizeIdentifier(trip.routeId)} · ${humanizeIdentifier(trip.vehicleId)} · ${trip.departureTime}`
    : "Not assigned";
  const visibleChanges = changes.slice(0, 6);
  const overviewData = [
    { name: "Changed", count: changes.length },
    { name: "Unchanged", count: unchangedCount },
  ];

  return (
    <section className="min-w-0 space-y-3 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-foreground">Schedule changes</h3>
        <div className="flex gap-2 text-xs">
          <span className="rounded-full bg-primary-soft px-3 py-1.5 font-medium text-primary">{changes.length.toLocaleString()} changed</span>
          <span className="rounded-full bg-surface-secondary px-3 py-1.5 font-medium text-secondary">{unchangedCount.toLocaleString()} unchanged</span>
        </div>
      </div>

      <div className="grid min-w-0 gap-3 lg:grid-cols-2">
        <ChangeChart title="Changed vs unchanged" data={overviewData} height={144} />
        <ChangeChart title="Change categories" data={categoryData} height={Math.max(144, categoryData.length * 28 + 24)} />
      </div>
      <div className="grid min-w-0 gap-3 md:grid-cols-2 xl:grid-cols-3">
        <ChangeChart title="Services by route" data={routeData} height={Math.max(150, routeData.length * 27 + 24)} />
        <ChangeChart title="Vehicle reassignments" data={vehicleData} height={Math.max(150, vehicleData.length * 27 + 24)} />
        <ChangeChart title="Departure changes" data={timeData} height={Math.max(150, timeData.length * 27 + 24)} />
      </div>

      {changes.length === 0 ? <p className="rounded-lg bg-surface-secondary px-3 py-2 text-sm text-secondary">No schedule changes</p> : <>
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="hidden w-full text-left text-sm md:table">
            <thead className="bg-surface-secondary text-xs text-secondary"><tr><th className="px-3 py-2.5 font-medium">Service</th><th className="px-3 py-2.5 font-medium">Before</th><th className="px-3 py-2.5 font-medium">After</th><th className="px-3 py-2.5 font-medium">Change</th></tr></thead>
            <tbody className="divide-y divide-border">{visibleChanges.map((change, index) => <tr key={change.id} className="transition-colors odd:bg-white even:bg-surface-secondary/40 hover:bg-primary-soft/40">
              <td className="whitespace-nowrap px-3 py-2.5 font-medium text-foreground">Service {index + 1}</td>
              <td className="max-w-52 break-words px-3 py-2.5 text-secondary">{textFor(change.before)}</td>
              <td className="max-w-52 break-words px-3 py-2.5 font-medium text-foreground">{textFor(change.after)}</td>
              <td className="px-3 py-2.5"><div className="flex flex-wrap gap-1">{change.labels.map((label) => <span key={label} className={`rounded-full px-2 py-1 text-xs font-medium ${badgeTone(change.labels)}`}>{label}</span>)}</div></td>
            </tr>)}</tbody>
          </table>
          <ul className="divide-y divide-border md:hidden">{visibleChanges.map((change, index) => <li key={change.id} className="space-y-2 p-3 text-sm odd:bg-white even:bg-surface-secondary/40">
            <div className="flex items-center justify-between gap-2"><span className="font-medium text-foreground">Service {index + 1}</span><span className={`rounded-full px-2 py-1 text-xs font-medium ${badgeTone(change.labels)}`}>{change.labels.join(" · ")}</span></div>
            <div className="grid grid-cols-2 gap-2"><div className="min-w-0"><p className="text-xs text-secondary">Before</p><p className="break-words text-secondary">{textFor(change.before)}</p></div><div className="min-w-0"><p className="text-xs text-secondary">After</p><p className="break-words text-foreground">{textFor(change.after)}</p></div></div>
          </li>)}</ul>
        </div>
        {changes.length > visibleChanges.length && <p className="text-xs text-secondary">Showing {visibleChanges.length} of {changes.length.toLocaleString()} changed services</p>}
      </>}
    </section>
  );
}
