import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { OptimizationResult, RunMetrics } from "../../types/optimization";

type MetricKey = keyof RunMetrics;

const metrics: Array<{ key: MetricKey; label: string; unit: string }> = [
  { key: "averageWaitingTimeMin", label: "Average wait", unit: "min" },
  { key: "unservedPassengers", label: "Unserved", unit: "passengers" },
  { key: "servedPassengers", label: "Served", unit: "passengers" },
  { key: "capacityViolations", label: "Capacity issues", unit: "violations" },
  { key: "vehicleDistanceKm", label: "Vehicle distance", unit: "km" },
];

export default function OptimizationMetricsChart({ result }: { result: OptimizationResult }) {
  const [selected, setSelected] = useState<MetricKey>("unservedPassengers");
  const baseline = result.baselineMetrics;
  const candidate = result.optimizedMetrics;
  if (!baseline || !candidate) return null;

  const selectedMetric = metrics.find((metric) => metric.key === selected) ?? metrics[0];
  const chartData = [
    { name: "Baseline", value: baseline[selected] },
    { name: "Optimized", value: candidate[selected] },
  ];

  return (
    <section className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-foreground">Run results</h3>
        </div>
        <div className="flex max-w-full flex-wrap gap-1.5" aria-label="Choose optimization result metric">
          {metrics.map((metric) => (
            <button
              key={metric.key}
              type="button"
              aria-pressed={selected === metric.key}
              onClick={() => setSelected(metric.key)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${selected === metric.key ? "border-primary bg-primary-soft text-primary" : "border-border bg-white text-muted-foreground hover:text-foreground"}`}
            >
              {metric.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm">
        <span className="font-medium text-foreground">{selectedMetric.label}</span>
        <span className="text-secondary">{baseline[selected].toLocaleString()} → <strong className="text-primary">{candidate[selected].toLocaleString()}</strong> {selectedMetric.unit}</span>
      </div>
      <div className="mt-2 h-[240px] w-full min-w-0 sm:h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 12, right: 12, left: -14, bottom: 4 }} barCategoryGap="38%">
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "var(--muted)" }} />
            <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "var(--muted)" }} />
            <Tooltip formatter={(value) => [`${Number(value ?? 0).toLocaleString()} ${selectedMetric.unit}`, selectedMetric.label]} />
            <Bar dataKey="value" name={selectedMetric.label} radius={[6, 6, 0, 0]} maxBarSize={68}>
              {chartData.map((entry) => <Cell key={entry.name} fill={entry.name === "Baseline" ? "var(--text-subtle)" : "var(--primary)"} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
