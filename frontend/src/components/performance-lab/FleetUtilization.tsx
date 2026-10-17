import { useState } from "react";
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
import { humanizeIdentifier } from "../../lib/presentation";

type FleetUtilizationProps = {
  vehicles: FleetUtilizationItem[];
};

export default function FleetUtilization({ vehicles }: FleetUtilizationProps) {
  const [visibleCount, setVisibleCount] = useState(10);
  const sortedVehicles = [...vehicles].sort((a, b) => Math.abs(b.optimized - b.baseline) - Math.abs(a.optimized - a.baseline));
  const visibleVehicles = sortedVehicles.slice(0, visibleCount);
  if (!vehicles.length) return null;

  return (
    <section className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
      <h3 className="font-semibold text-foreground">Fleet utilization</h3>
      <div className="mt-4 w-full min-w-0" style={{ height: Math.max(260, visibleVehicles.length * 34) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={visibleVehicles} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }} barCategoryGap="25%">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} tickFormatter={(value: number) => `${value}%`} />
            <YAxis type="category" dataKey="vehicleId" width={84} tick={{ fontSize: 12 }} tickFormatter={(value: string) => humanizeIdentifier(value)} />
            <Tooltip formatter={(value) => [`${value}%`, "Utilization"]} labelFormatter={(label) => humanizeIdentifier(String(label))} />
            <Legend />
            <Bar dataKey="baseline" name="Baseline" fill="var(--text-subtle)" radius={[0, 4, 4, 0]} />
            <Bar dataKey="optimized" name="Optimized" fill="var(--primary)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {sortedVehicles.length > visibleVehicles.length && <button type="button" onClick={() => setVisibleCount((count) => count + 10)} className="mt-3 min-h-10 rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:border-primary hover:text-primary">Show more vehicles</button>}
    </section>
  );
}
