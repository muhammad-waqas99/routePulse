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

import type { FleetUtilization as FleetUtilizationItem } from "../../types/performanceLab";

type FleetUtilizationProps = {
  vehicles: FleetUtilizationItem[];
};

export default function FleetUtilization({
  vehicles,
}: FleetUtilizationProps) {
  return (
    <section className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div>
        <h3 className="font-semibold text-foreground">
          Fleet Utilization
        </h3>
        <p className="mt-1 text-sm text-secondary">
          Compare how much each vehicle is utilized in both plans.
        </p>
      </div>

      {vehicles.length === 0 ? (
        <p className="py-10 text-center text-sm text-secondary">
          Fleet utilization data is not available for this run.
        </p>
      ) : (
        <div className="mt-5 h-80 w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={vehicles}
              layout="vertical"
              margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
              barCategoryGap="25%"
            >
              <CartesianGrid
                strokeDasharray="3 3"
                horizontal={false}
              />

              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                tickFormatter={(value: number) => `${value}%`}
              />

              <YAxis
                type="category"
                dataKey="vehicleId"
                width={70}
                tick={{ fontSize: 12 }}
              />

              <Tooltip
                formatter={(value) => [`${value}%`, "Utilization"]}
              />

              <Legend />

              <Bar
                dataKey="baseline"
                name="Baseline"
                fill="#94A3B8"
                radius={[0, 4, 4, 0]}
              />

              <Bar
                dataKey="optimized"
                name="Optimized"
                fill="#2563EB"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
