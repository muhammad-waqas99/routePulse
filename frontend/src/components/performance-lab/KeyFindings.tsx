import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Lightbulb,
  Route,
  Users,
} from "lucide-react";

import type {
  PerformanceMetrics,
  PassengerOutcome,
} from "../../types/performanceLab";

type KeyFindingsProps = {
  metrics: PerformanceMetrics;
  passengerOutcome?: PassengerOutcome;
  keyFinding?: string;
};

function getPercentageChange(baseline: number, optimized: number) {
  if (baseline === 0) return null;

  return ((baseline - optimized) / baseline) * 100;
}

function formatChange(value: number | null) {
  if (value === null) return "No baseline available";

  if (value === 0) return "No change";

  return `${Math.abs(value).toFixed(1)}% ${value > 0 ? "lower" : "higher"}`;
}

export default function KeyFindings({
  metrics,
  passengerOutcome,
  keyFinding,
}: KeyFindingsProps) {
  const waitingChange = getPercentageChange(
    metrics.averageWaitingTime.baseline,
    metrics.averageWaitingTime.optimized,
  );

  const unservedChange = getPercentageChange(
    metrics.unservedPassengers.baseline,
    metrics.unservedPassengers.optimized,
  );

  const distanceChange = getPercentageChange(
    metrics.vehicleDistance.baseline,
    metrics.vehicleDistance.optimized,
  );

  return (
    <section className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-primary">
          <Lightbulb size={20} />
        </span>

        <div className="min-w-0">
          <h3 className="font-semibold text-foreground">Key Findings</h3>
          <p className="mt-1 text-sm text-secondary">
            Summary of the selected evaluation run.
          </p>
        </div>
      </div>

      <div className="mt-5 grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <article className="min-w-0 rounded-lg border border-border p-4">
          <div className="flex items-center gap-2 text-sm text-secondary">
            <Activity size={17} />
            Average Waiting Time
          </div>

          <p className="mt-3 break-words text-xl font-semibold text-foreground">
            {metrics.averageWaitingTime.optimized.toFixed(1)} min
          </p>

          <p className="mt-1 text-sm text-secondary">
            {formatChange(waitingChange)} vs baseline
          </p>
        </article>

        <article className="min-w-0 rounded-lg border border-border p-4">
          <div className="flex items-center gap-2 text-sm text-secondary">
            <Users size={17} />
            Unserved Passengers
          </div>

          <p className="mt-3 wrap-break-word text-xl font-semibold text-foreground">
            {metrics.unservedPassengers.optimized.toLocaleString()}
          </p>

          <p className="mt-1 text-sm text-secondary">
            {formatChange(unservedChange)} vs baseline
          </p>

          {passengerOutcome && (
            <p className="mt-2 text-xs text-secondary">
              {passengerOutcome.optimizedServed.toLocaleString()} of{" "}
              {passengerOutcome.total.toLocaleString()} passengers served
            </p>
          )}
        </article>

        <article className="min-w-0 rounded-lg border border-border p-4">
          <div className="flex items-center gap-2 text-sm text-secondary">
            <Route size={17} />
            Vehicle Distance
          </div>

          <p className="mt-3 wrap-break-word text-xl font-semibold text-foreground">
            {metrics.vehicleDistance.optimized.toFixed(1)} km
          </p>

          <p className="mt-1 text-sm text-secondary">
            {distanceChange === null
              ? "Baseline comparison unavailable"
              : `${Math.abs(distanceChange).toFixed(1)}% ${
                  distanceChange > 0 ? "lower" : distanceChange < 0 ? "higher" : "change-free"
                } vs baseline`}
          </p>

          <p className="mt-2 text-xs text-secondary">
            Consider alongside service quality and fleet constraints.
          </p>
        </article>
      </div>

      {keyFinding && (
        <div className="mt-4 flex items-start gap-2 rounded-lg bg-slate-50 p-4">
          {waitingChange !== null && waitingChange > 0 ? (
            <ArrowDownRight
              size={18}
              className="mt-0.5 shrink-0 text-emerald-700"
            />
          ) : (
            <ArrowUpRight
              size={18}
              className="mt-0.5 shrink-0 text-secondary"
            />
          )}

          <p className="text-sm leading-6 text-foreground">{keyFinding}</p>
        </div>
      )}
    </section>
  );
}
