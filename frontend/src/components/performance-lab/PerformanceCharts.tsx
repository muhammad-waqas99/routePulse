import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PerformanceMetrics } from "../../types/performanceLab";
import type { BackendEvaluationResponse } from "../../types/optimization";

type Datum = { key: string; label: string; short: string; baseline: number; optimized: number; unit: string };
type Group = { title: string; keys: string[]; unit: string };

const definitions: Record<string, { label: string; short: string; unit: string }> = {
  served_passengers: { label: "Passengers served", short: "Served", unit: "passengers" },
  unserved_passengers: { label: "Passengers unserved", short: "Unserved", unit: "passengers" },
  abandoned_passengers: { label: "Passengers who left the queue", short: "Abandoned", unit: "passengers" },
  total_demand: { label: "Total passenger demand", short: "Demand", unit: "passengers" },
  completed_journeys: { label: "Completed journeys", short: "Completed", unit: "journeys" },
  passengers_affected_by_breakdowns: { label: "Passengers affected by breakdowns", short: "Affected", unit: "passengers" },
  avg_wait_min: { label: "Average wait", short: "Average", unit: "min" },
  median_wait_min: { label: "Median wait", short: "Median", unit: "min" },
  max_wait_min: { label: "Longest wait", short: "Longest", unit: "min" },
  eta_mae_min: { label: "ETA prediction error", short: "ETA error", unit: "min" },
  missed_connections: { label: "Missed connections", short: "Missed", unit: "events" },
  capacity_violations: { label: "Capacity violations", short: "Capacity", unit: "events" },
  breakdown_count: { label: "Vehicle breakdowns", short: "Breakdowns", unit: "events" },
  vehicle_departures: { label: "Vehicle departures", short: "Departures", unit: "trips" },
  vehicle_arrivals: { label: "Vehicle arrivals", short: "Arrivals", unit: "trips" },
  max_segment_load: { label: "Peak onboard load", short: "Peak load", unit: "passengers" },
  eta_observations: { label: "ETA observations", short: "ETAs", unit: "observations" },
  vehicle_km: { label: "Vehicle distance", short: "Distance", unit: "km" },
  operating_cost: { label: "Operating cost", short: "Cost", unit: "cost units" },
};

const groups: Group[] = [
  { title: "Passenger outcomes", keys: ["served_passengers", "unserved_passengers", "abandoned_passengers", "total_demand", "completed_journeys", "passengers_affected_by_breakdowns"], unit: "passengers / journeys" },
  { title: "Waiting time and ETA", keys: ["avg_wait_min", "median_wait_min", "max_wait_min", "eta_mae_min"], unit: "minutes" },
  { title: "Service and fleet events", keys: ["missed_connections", "capacity_violations", "breakdown_count", "vehicle_departures", "vehicle_arrivals", "max_segment_load", "eta_observations"], unit: "count" },
  { title: "Vehicle distance", keys: ["vehicle_km"], unit: "km" },
  { title: "Operating cost", keys: ["operating_cost"], unit: "units" },
];

function numericPair(before: unknown, after: unknown): [number, number] | null {
  if (typeof before !== "number" || !Number.isFinite(before) || typeof after !== "number" || !Number.isFinite(after)) return null;
  return [before, after];
}

function formatValue(value: number, unit: string) {
  const number = Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 1 });
  return unit === "min" ? `${number} min` : unit === "km" ? `${number} km` : unit === "cost units" ? `${number} units` : `${number} ${unit}`;
}

function fromEvaluation(evaluation: BackendEvaluationResponse | null | undefined): Datum[] {
  const before = evaluation?.baseline?.metrics;
  const after = evaluation?.candidate?.metrics;
  if (!before || !after) return [];
  return Object.keys(definitions).flatMap((key) => {
    if (key === "operating_cost" && (before.cost_available !== true || after.cost_available !== true)) return [];
    const oldValue = before[key as keyof typeof before];
    const newValue = after[key as keyof typeof after];
    const pair = numericPair(oldValue, newValue);
    if (!pair) return [];
    const definition = definitions[key];
    return [{ key, label: definition.label, short: definition.short, baseline: pair[0], optimized: pair[1], unit: definition.unit }];
  });
}

function fromSummary(metrics: PerformanceMetrics): Datum[] {
  const values = [
    ["avg_wait_min", "Average wait", "Average", metrics.averageWaitingTime],
    ["unserved_passengers", "Passengers unserved", "Unserved", metrics.unservedPassengers],
    ["capacity_violations", "Capacity violations", "Capacity", metrics.capacityViolations],
    ["vehicle_km", "Vehicle distance", "Distance", metrics.vehicleDistance],
    ["operating_cost", "Operating cost", "Cost", metrics.operatingCost],
  ] as const;
  return values.flatMap(([key, label, short, metric]) => metric ? [{ key, label, short, baseline: metric.baseline, optimized: metric.optimized, unit: metric.unit }] : []);
}

function ComparisonChart({ title, unit, data }: { title: string; unit: string; data: Datum[] }) {
  const tradeoffMetric = data.length === 1 && (data[0].key === "vehicle_km" || data[0].key === "operating_cost") ? data[0] : null;
  const change = tradeoffMetric ? tradeoffMetric.optimized - tradeoffMetric.baseline : null;
  const impact = change === null ? "neutral" : change > 0 ? "tradeoff" : change < 0 ? "improved" : "neutral";
  return (
    <article className="min-w-0 rounded-xl border border-border bg-surface p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h4 className="font-semibold text-foreground">{title}</h4>
        {tradeoffMetric && change !== null && <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${impact === "tradeoff" ? "bg-warning-soft text-warning" : impact === "improved" ? "bg-success-soft text-success" : "bg-surface-secondary text-secondary"}`}>
          {impact === "tradeoff" ? "Trade-off" : impact === "improved" ? "Reduced" : "No change"} · {change > 0 ? "+" : change < 0 ? "−" : ""}{formatValue(Math.abs(change), tradeoffMetric.unit)}
        </span>}
      </div>
      <div className="mt-3 h-[255px] min-w-0 sm:h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 4 }} barCategoryGap="24%">
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="short" tick={{ fontSize: 10, fill: "var(--muted)" }} interval={0} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: "var(--muted)" }} axisLine={false} tickLine={false} width={48} />
            <Tooltip
              labelFormatter={(_label, payload) => (payload?.[0]?.payload as Datum | undefined)?.label ?? ""}
              formatter={(value, name, item) => [formatValue(Number(value), (item.payload as Datum).unit), name]}
              contentStyle={{ borderRadius: 10, borderColor: "var(--border)", background: "var(--surface)" }}
            />
            <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="baseline" name="Baseline" fill="var(--text-subtle)" radius={[4, 4, 0, 0]} maxBarSize={30} />
            <Bar dataKey="optimized" name="Optimized" fill={impact === "tradeoff" ? "var(--warning)" : "var(--primary)"} radius={[4, 4, 0, 0]} maxBarSize={30} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-1 text-[11px] text-muted-foreground">{unit}</p>
    </article>
  );
}

export default function PerformanceCharts({ metrics, evaluation }: { metrics: PerformanceMetrics; evaluation?: BackendEvaluationResponse | null }) {
  const available = useMemo(() => {
    const detailed = fromEvaluation(evaluation);
    return detailed.length ? detailed : fromSummary(metrics);
  }, [evaluation, metrics]);
  const availableByKey = new Map(available.map((item) => [item.key, item]));
  const charts = groups.flatMap((group) => {
    const data = group.keys.flatMap((key) => {
      const row = availableByKey.get(key);
      return row ? [row] : [];
    });
    if (!data.length) return [];
    return [{ ...group, data }];
  });

  if (!charts.length) return null;

  return (
    <section className="min-w-0 space-y-4" aria-label="Baseline and optimized charts">
      <div>
        <h3 className="text-lg font-semibold text-foreground">Performance charts</h3>
      </div>
      <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">
        {charts.map((chart) => <ComparisonChart key={chart.title} {...chart} />)}
      </div>
    </section>
  );
}
