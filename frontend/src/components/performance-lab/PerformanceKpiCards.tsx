
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Clock3,
  GitCompareArrows,
  Users,
} from "lucide-react";

import type { PerformanceMetrics } from "../../types/performanceLab";

type PerformanceKpiCardsProps = {
  metrics: PerformanceMetrics;
};

type KpiCardProps = {
  title: string;
  value: number;
  baseline: number;
  unit: string;
  icon: React.ReactNode;
};

function formatMetric(value: number, unit: string) {
  if (unit === "min") return `${value.toFixed(1)} min`;
  if (unit === "km") return `${value.toFixed(1)} km`;
  if (unit === "percent") return `${value.toFixed(1)}%`;

  return value.toLocaleString();
}

function KpiCard({
  title,
  value,
  baseline,
  unit,
  icon,
}: KpiCardProps) {
  const improvement =
    baseline === 0 ? null : ((baseline - value) / baseline) * 100;

  const isLower = improvement !== null && improvement > 0;
  const isHigher = improvement !== null && improvement < 0;

  return (
    <article className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-secondary">{title}</p>

        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-secondary">
          {icon}
        </span>
      </div>

      <p className="mt-4 wrap-break-word text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
        {formatMetric(value, unit)}
      </p>

      <p className="mt-2 text-xs text-secondary">
        Baseline: {formatMetric(baseline, unit)}
      </p>

      {improvement !== null && (
        <div
          className={`mt-3 inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
            isLower
              ? "bg-emerald-50 text-emerald-700"
              : isHigher
                ? "bg-amber-50 text-amber-700"
                : "bg-slate-100 text-slate-600"
          }`}
        >
          {isLower ? (
            <ArrowDownRight size={14} />
          ) : isHigher ? (
            <ArrowUpRight size={14} />
          ) : null}

          {improvement === 0
            ? "No change"
            : `${Math.abs(improvement).toFixed(1)}% ${
                isLower ? "lower" : "higher"
              }`}
        </div>
      )}
    </article>
  );
}

export default function PerformanceKpiCards({
  metrics,
}: PerformanceKpiCardsProps) {
  const cards = [
    {
      title: "Average Waiting Time",
      metric: metrics.averageWaitingTime,
      icon: <Clock3 size={19} />,
    },
    {
      title: "Unserved Passengers",
      metric: metrics.unservedPassengers,
      icon: <Users size={19} />,
    },
    {
      title: "Missed Connections",
      metric: metrics.missedConnections,
      icon: <GitCompareArrows size={19} />,
    },
    {
      title: "ETA Error",
      metric: metrics.etaMae,
      icon: <Activity size={19} />,
    },
  ];

  return (
    <section className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ title, metric, icon }) => (
        <KpiCard
          key={title}
          title={title}
          value={metric.optimized}
          baseline={metric.baseline}
          unit={metric.unit}
          icon={icon}
        />
      ))}
    </section>
  );
}
