import { Lightbulb } from "lucide-react";
import type { PerformanceMetrics } from "../../types/performanceLab";

export default function KeyFindings({ metrics, keyFinding }: { metrics: PerformanceMetrics; keyFinding?: string }) {
  const available = [
    ["Average wait", metrics.averageWaitingTime],
    ["Unserved passengers", metrics.unservedPassengers],
    ["Capacity violations", metrics.capacityViolations],
    ["Vehicle distance", metrics.vehicleDistance],
    ["Operating cost", metrics.operatingCost],
  ] as const;
  const findings = available.flatMap(([label, metric]) => {
    if (!metric) return [];
    const difference = metric.optimized - metric.baseline;
    const improved = metric.lowerIsBetter ? difference < 0 : difference > 0;
    const worse = metric.lowerIsBetter ? difference > 0 : difference < 0;
    const percent = metric.baseline === 0 ? null : Math.abs(difference / metric.baseline) * 100;
    const format = (value: number) => `${Number.isInteger(value) ? value.toLocaleString() : value.toFixed(1)}${metric.unit ? ` ${metric.unit}` : ""}`;
    const verdict = difference === 0 ? "No change" : improved ? "Improved" : worse ? "Trade-off" : "Changed";
    const tone = difference === 0 ? "neutral" : improved ? "good" : worse ? "warning" : "neutral";
    const change = difference === 0 ? "" : ` · ${difference > 0 ? "+" : "−"}${format(Math.abs(difference))}`;
    const percentage = percent === null ? "" : ` (${percent.toFixed(1)}%)`;
    return [{ label, verdict, tone, text: `${label}: ${format(metric.baseline)} → ${format(metric.optimized)}${change}${percentage}.` }];
  });

  if (!findings.length && !keyFinding) return null;

  return (
    <section className="min-w-0 rounded-xl border border-border bg-surface p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-primary"><Lightbulb size={20} /></span>
        <div className="min-w-0">
          <h3 className="font-semibold text-foreground">Key findings</h3>
        </div>
      </div>
      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {findings.map((finding) => <li key={finding.label} className={`rounded-lg border p-3 text-sm leading-5 ${finding.tone === "good" ? "border-success-border bg-success-soft/40 text-foreground" : finding.tone === "warning" ? "border-warning-border bg-warning-soft/50 text-foreground" : "border-border bg-white text-foreground"}`}><div className="flex flex-wrap items-center justify-between gap-2"><span className="font-medium">{finding.label}</span><span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${finding.tone === "good" ? "bg-success-soft text-success" : finding.tone === "warning" ? "bg-warning-soft text-warning" : "bg-surface-secondary text-secondary"}`}>{finding.verdict}</span></div><p className="mt-1">{finding.text}</p></li>)}
      </ul>
      {keyFinding && <p className="mt-3 rounded-lg bg-surface-secondary p-3 text-sm leading-5 text-secondary">{keyFinding}</p>}
    </section>
  );
}
