
import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import type { PerformanceMetrics } from "../../types/performanceLab";

type PerformanceComparisonProps = {
  metrics: PerformanceMetrics;
};

function formatValue(value: number, unit: string) {
  if (unit === "min") return `${value.toFixed(1)} min`;
  if (unit === "km") return `${value.toFixed(1)} km`;
  if (unit === "percent") return `${value.toFixed(1)}%`;

  return value.toLocaleString();
}

export default function PerformanceComparison({
  metrics,
}: PerformanceComparisonProps) {
  const rows = [
    {
      label: "Average Waiting Time",
      metric: metrics.averageWaitingTime,
    },
    {
      label: "Unserved Passengers",
      metric: metrics.unservedPassengers,
    },
    {
      label: "Missed Connections",
      metric: metrics.missedConnections,
    },
    {
      label: "ETA Mean Absolute Error",
      metric: metrics.etaMae,
    },
    {
      label: "Unserved Rate",
      metric: metrics.unservedRate,
    },
    {
      label: "Capacity Violations",
      metric: metrics.capacityViolations,
    },
    {
      label: "Vehicle Distance",
      metric: metrics.vehicleDistance,
    },
  ];

  return (
    <section className="min-w-0 rounded-xl border border-border bg-white">
      <div className="border-b border-border p-4 sm:p-5">
        <h3 className="font-semibold text-foreground">
          Baseline vs Optimized
        </h3>
        <p className="mt-1 text-sm text-secondary">
          Compare the measured metrics for both plans.
        </p>
      </div>

      <div className="min-w-0 overflow-x-auto">
        <table className="w-full min-w-155 text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-secondary">
            <tr>
              <th className="px-4 py-3 font-medium sm:px-5">Metric</th>
              <th className="px-4 py-3 font-medium">Baseline</th>
              <th className="px-4 py-3 font-medium">Optimized</th>
              <th className="px-4 py-3 font-medium">Change</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-border">
            {rows.map(({ label, metric }) => {
              const difference = metric.optimized - metric.baseline;
              const percentChange =
                metric.baseline === 0
                  ? null
                  : (Math.abs(difference) / Math.abs(metric.baseline)) * 100;

              const isVehicleDistance = label === "Vehicle Distance";
              const improved =
                difference === 0
                  ? null
                  : metric.lowerIsBetter
                    ? difference < 0
                    : difference > 0;

              return (
                <tr key={label} className="align-middle">
                  <td className="px-4 py-4 font-medium text-foreground sm:px-5">
                    {label}
                  </td>

                  <td className="whitespace-nowrap px-4 py-4 text-secondary">
                    {formatValue(metric.baseline, metric.unit)}
                  </td>

                  <td className="whitespace-nowrap px-4 py-4 font-medium text-foreground">
                    {formatValue(metric.optimized, metric.unit)}
                  </td>

                  <td className="px-4 py-4">
                    <span
                      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-1 text-xs font-medium ${
                        difference === 0
                          ? "bg-slate-100 text-slate-600"
                          : isVehicleDistance
                            ? "bg-amber-50 text-amber-700"
                            : improved
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-red-50 text-red-700"
                      }`}
                    >
                      {difference === 0 ? (
                        <Minus size={13} />
                      ) : difference < 0 ? (
                        <ArrowDown size={13} />
                      ) : (
                        <ArrowUp size={13} />
                      )}

                      {difference === 0
                        ? "No change"
                        : `${difference > 0 ? "+" : ""}${difference.toFixed(1)}${
                            percentChange === null
                              ? ""
                              : ` (${percentChange.toFixed(1)}%)`
                          }`}
                    </span>

                    {isVehicleDistance && difference !== 0 && (
                      <p className="mt-1 text-xs text-secondary">
                        Distance trade-off
                      </p>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
