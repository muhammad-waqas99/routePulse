import type { OptimizationResult } from "../../types/optimization";
import { scenarioLabel } from "../../lib/presentation";

interface Props {
  result: OptimizationResult;
}

function MetricCard({ title, baseline, candidate, unit, lowerIsBetter }: {
  title: string;
  baseline: number | null | undefined;
  candidate: number | null | undefined;
  unit: string;
  lowerIsBetter: boolean;
}) {
  if (typeof baseline !== "number" || !Number.isFinite(baseline) || typeof candidate !== "number" || !Number.isFinite(candidate)) return null;
  const format = (value: number) => `${Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 1 })}${unit ? ` ${unit}` : ""}`;
  const difference = candidate - baseline;
  const improved = difference === 0 ? null : lowerIsBetter ? difference < 0 : difference > 0;
  const tone = difference === 0 ? "neutral" : improved ? "good" : "warning";
  const toneClass = tone === "good" ? "bg-success-soft text-success" : tone === "warning" ? "bg-warning-soft text-warning" : "bg-surface-secondary text-secondary";

  return (
    <article className="min-w-0 rounded-lg border border-border bg-white p-3.5">
      <div className="flex items-center justify-between gap-2"><p className="text-xs font-medium text-secondary">{title}</p><span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${toneClass}`}>{difference === 0 ? "No change" : improved ? "Improved" : "Trade-off"}</span></div>
      <p className="mt-2 text-lg font-semibold text-foreground">{format(candidate)}</p>
      <p className="mt-1 text-xs text-secondary">Baseline {format(baseline)}</p>
      {difference !== 0 && <p className={`mt-1 text-xs font-medium ${tone === "warning" ? "text-warning" : "text-success"}`}>{difference > 0 ? "+" : "−"}{format(Math.abs(difference))}</p>}
    </article>
  );
}

export default function EvaluationDetails({ result }: Props) {
  const { baseline, candidate } = result.backendResult;
  const baselineOutcomes = baseline?.passenger_outcomes;
  const candidateOutcomes = candidate?.passenger_outcomes;
  const baselineMetrics = baseline?.metrics;
  const candidateMetrics = candidate?.metrics;
  const comparisonRows: Array<[string, number | null | undefined, number | null | undefined, string, boolean]> = [
    ["Average wait", baselineMetrics?.avg_wait_min, candidateMetrics?.avg_wait_min, "min", true],
    ["Passengers served", baselineOutcomes?.served, candidateOutcomes?.served, "", false],
    ["Passengers unserved", baselineOutcomes?.unserved, candidateOutcomes?.unserved, "", true],
    ["Vehicle distance", baselineMetrics?.vehicle_km, candidateMetrics?.vehicle_km, "km", true],
    ...(baselineMetrics?.cost_available === true && candidateMetrics?.cost_available === true
      ? [["Operating cost", baselineMetrics.operating_cost, candidateMetrics.operating_cost, "units", true] as [string, number, number, string, boolean]]
      : []),
  ].filter((row): row is [string, number, number, string, boolean] => typeof row[1] === "number" && Number.isFinite(row[1]) && typeof row[2] === "number" && Number.isFinite(row[2]));

  return (
    <section className="space-y-4 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-foreground">Simulation summary</h3>
        </div>
        <p className="text-xs text-secondary">{scenarioLabel(result.scenarioId)}{baseline ? ` · ${baseline.horizon_min.toLocaleString()} min` : ""}</p>
      </div>

      {comparisonRows.length > 0 && <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {comparisonRows.map(([title, oldValue, newValue, unit, lowerIsBetter]) => <MetricCard key={title} title={title} baseline={oldValue} candidate={newValue} unit={unit} lowerIsBetter={lowerIsBetter} />)}
      </div>}

    </section>
  );
}
