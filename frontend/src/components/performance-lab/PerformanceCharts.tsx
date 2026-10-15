import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PerformanceMetrics } from "../../types/performanceLab";

type PerformanceChartsProps = {
  metrics: PerformanceMetrics;
};

export default function PerformanceCharts({
  metrics,
}: PerformanceChartsProps) {
  const comparisonData = [
    {
      metric: "Waiting Time",
      baseline: metrics.averageWaitingTime.baseline,
      optimized: metrics.averageWaitingTime.optimized,
    },
    {
      metric: "Unserved",
      baseline: metrics.unservedPassengers.baseline,
      optimized: metrics.unservedPassengers.optimized,
    },
    {
      metric: "Missed Connections",
      baseline: metrics.missedConnections.baseline,
      optimized: metrics.missedConnections.optimized,
    },
    {
      metric: "ETA Error",
      baseline: metrics.etaMae.baseline,
      optimized: metrics.etaMae.optimized,
    },
    {
      metric: "Capacity Violations",
      baseline: metrics.capacityViolations.baseline,
      optimized: metrics.capacityViolations.optimized,
    },
  ];


  return (
    <section className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-foreground">
          Performance Visualizations
        </h3>
        <p className="mt-1 text-sm text-secondary">
          Compare baseline and optimized results across key metrics.
        </p>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">
        <article className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
          <h4 className="font-semibold text-foreground">
            Metric Comparison
          </h4>
          <p className="mt-1 text-sm text-secondary">
            Lower values are generally better for these metrics.
          </p>

          <div className="mt-5 h-80 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={comparisonData}
                margin={{ top: 8, right: 8, left: -18, bottom: 8 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis
                  dataKey="metric"
                  tick={{ fontSize: 11 }}
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                  height={65}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  allowDecimals={false}
                />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="baseline"
                  name="Baseline"
                  fill="#94A3B8"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="optimized"
                  name="Optimized"
                  fill="#2563EB"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
          <h4 className="font-semibold text-foreground">
            Unserved Passenger Comparison
          </h4>
          <p className="mt-1 text-sm text-secondary">
            Compare passengers left unserved in both plans.
          </p>

          <div className="mt-5 h-80 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  {
                    category: "Unserved Passengers",
                    baseline: metrics.unservedPassengers.baseline,
                    optimized: metrics.unservedPassengers.optimized,
                  },
                ]}
                margin={{ top: 12, right: 12, left: 0, bottom: 8 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="baseline"
                  name="Baseline"
                  fill="#94A3B8"
                  radius={[5, 5, 0, 0]}
                />
                <Bar
                  dataKey="optimized"
                  name="Optimized"
                  fill="#2563EB"
                  radius={[5, 5, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
      </div>
    </section>
  );
}
