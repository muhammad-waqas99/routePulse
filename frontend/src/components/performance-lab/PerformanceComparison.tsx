import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import type { PerformanceMetrics } from "../../types/performanceLab";

type PerformanceComparisonProps = {
  metrics: PerformanceMetrics;
};

function formatValue(value: number, unit: string) {
  if (unit === "min") return `${value.toFixed(1)} min`;
  if (unit === "km") return `${value.toFixed(1)} km`;
  if (unit === "percent") return `${value.toFixed(1)}%`;
  const formatted = Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 1 });
  return unit === "cost units" ? `${formatted} units` : formatted;
}

export default function PerformanceComparison({ metrics }: PerformanceComparisonProps) {
  const rows = [
    { label: "Average wait", metric: metrics.averageWaitingTime },
    { label: "Unserved passengers", metric: metrics.unservedPassengers },
    { label: "Capacity violations", metric: metrics.capacityViolations },
    { label: "Vehicle distance", metric: metrics.vehicleDistance },
    { label: "Operating cost", metric: metrics.operatingCost },
  ].filter((row) => row.metric !== undefined);

  if (!rows.length) return null;

  return (
    <section className="rounded-xl border border-border bg-surface p-4 sm:p-5">
      <h3 className="font-semibold text-foreground">Baseline vs optimized</h3>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
        {rows.map(({ label, metric }) => {
          if (!metric) return null;
          const difference = metric.optimized - metric.baseline;
          const percentChange = metric.baseline === 0 ? null : Math.abs(difference / metric.baseline) * 100;
          const improved = difference === 0 ? null : metric.lowerIsBetter ? difference < 0 : difference > 0;
          const tone = difference === 0 ? "neutral" : improved ? "good" : "warning";
          const toneClass = tone === "good" ? "bg-success-soft text-success" : tone === "warning" ? "bg-warning-soft text-warning" : "bg-surface-secondary text-muted-foreground";
          const Icon = difference === 0 ? Minus : difference < 0 ? ArrowDown : ArrowUp;
          const magnitude = Math.max(Math.abs(metric.baseline), Math.abs(metric.optimized), 1);
          const baselineWidth = Math.max(4, (Math.abs(metric.baseline) / magnitude) * 100);
          const optimizedWidth = Math.max(4, (Math.abs(metric.optimized) / magnitude) * 100);

          return (
            <article key={label} className="min-w-0 rounded-lg border border-border p-3.5">
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-sm font-medium text-foreground">{label}</h4>
                <span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${toneClass}`}>
                  <Icon size={13} />
                  {difference === 0 ? "No change" : `${improved ? "Improved" : "Trade-off"} · ${difference > 0 ? "+" : "−"}${formatValue(Math.abs(difference), metric.unit)}`}
                </span>
              </div>
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-[72px] shrink-0 text-muted-foreground">Baseline</span>
                  <div className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-surface-secondary"><div className="h-full rounded-full bg-text-subtle" style={{ width: `${baselineWidth}%` }} /></div>
                  <span className="w-[76px] shrink-0 text-right font-medium tabular-nums text-foreground">{formatValue(metric.baseline, metric.unit)}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-[72px] shrink-0 text-muted-foreground">Optimized</span>
                  <div className={`h-2 min-w-0 flex-1 overflow-hidden rounded-full ${tone === "warning" ? "bg-warning-soft" : "bg-primary-soft"}`}><div className={`h-full rounded-full ${tone === "warning" ? "bg-warning" : "bg-primary"}`} style={{ width: `${optimizedWidth}%` }} /></div>
                  <span className="w-[76px] shrink-0 text-right font-semibold tabular-nums text-foreground">{formatValue(metric.optimized, metric.unit)}</span>
                </div>
              </div>
              {percentChange !== null && <p className={`mt-2 text-right text-[11px] ${tone === "warning" ? "text-warning" : tone === "good" ? "text-success" : "text-muted-foreground"}`}>{percentChange.toFixed(1)}% {tone === "warning" ? "trade-off" : tone === "good" ? "improvement" : "change"}</p>}
            </article>
          );
        })}
      </div>
    </section>
  );
}
