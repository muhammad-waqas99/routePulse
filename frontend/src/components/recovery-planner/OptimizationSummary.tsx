import {
  ArrowRight,
  BusFront,
  Clock3,
  TrendingUp,
} from "lucide-react";
import type { RecoveryPlanResult } from "../../types/recoveryPlanner";

interface Props {
  result: RecoveryPlanResult;
}

export default function OptimizationSummary({ result }: Props) {
  const metrics = [
    {
      label: "Average Waiting Time",
      value: `${result.metrics.averageWaitingTimeMin} min`,
      icon: Clock3,
    },
    {
      label: "Unserved Passengers",
      value: String(result.metrics.unservedPassengers),
      icon: BusFront,
    },
    {
      label: "Missed Connections",
      value: String(result.metrics.missedConnections),
      icon: ArrowRight,
    },
    {
      label: "Vehicle Distance",
      value: `${result.metrics.vehicleDistanceKm} km`,
      icon: TrendingUp,
    },
  ];

  return (
    <section className="min-w-0 space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-foreground">
          Optimization Summary
        </h3>
        <p className="mt-1 text-sm text-secondary">
          Evaluation metrics for the proposed plan.
        </p>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <div
              key={metric.label}
              className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5"
            >
              <div className="flex items-center gap-2 text-secondary">
                <Icon size={17} />
                <span className="text-sm">{metric.label}</span>
              </div>
              <p className="mt-4 wrap-break-word text-2xl font-semibold text-foreground">
                {metric.value}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
