import { useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import type { Trip, Vehicle } from "../../types/operations";

const fleetColors: Record<Vehicle["status"], string> = {
  available: "var(--success)",
  "in-service": "var(--primary)",
  unavailable: "var(--danger)",
};

const fleetLabels: Record<Vehicle["status"], string> = {
  available: "Available",
  "in-service": "In service",
  unavailable: "Unavailable",
};

type TripPeriod = "all" | "morning" | "afternoon";

function timeToMinutes(value: string) {
  const match = /^(\d{1,2}):(\d{2})$/.exec(value);
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

export default function OperationsOverviewCharts({ vehicles, trips }: { vehicles: Vehicle[]; trips: Trip[] }) {
  const [tripPeriod, setTripPeriod] = useState<TripPeriod>("all");
  const fleetData = useMemo(() => {
    const counts = new Map<Vehicle["status"], number>([["available", 0], ["in-service", 0], ["unavailable", 0]]);
    for (const vehicle of vehicles) counts.set(vehicle.status, (counts.get(vehicle.status) ?? 0) + 1);
    return [...counts].map(([status, value]) => ({ status, name: fleetLabels[status], value, color: fleetColors[status] }));
  }, [vehicles]);

  const hourlyTrips = useMemo(() => {
    const buckets = new Map<number, { hour: number; trips: number }>();
    for (const trip of trips) {
      if (trip.status === "cancelled") continue;
      const minutes = timeToMinutes(trip.departureTime);
      if (minutes === null) continue;
      const hour = Math.floor(minutes / 60);
      const existing = buckets.get(hour) ?? { hour, trips: 0 };
      existing.trips += 1;
      buckets.set(hour, existing);
    }
    const all = [...buckets.values()].sort((a, b) => a.hour - b.hour);
    return all.filter((entry) => tripPeriod === "all" || (tripPeriod === "morning" ? entry.hour < 12 : entry.hour >= 12));
  }, [trips, tripPeriod]);

  const fleetTotal = vehicles.length;

  return (
    <section className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2" aria-label="Operations visualizations">
      <article className="min-w-0 rounded-xl border border-border bg-surface p-4 sm:p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h2 className="font-semibold text-foreground">Fleet status</h2>
          </div>
          <span className="rounded-full bg-primary-soft px-2.5 py-1 text-xs font-medium text-primary">{fleetTotal} buses</span>
        </div>
        {fleetTotal ? (
          <div className="mt-2 grid min-h-[210px] grid-cols-1 items-center gap-2 sm:grid-cols-[minmax(0,1fr)_160px]">
            <div className="relative h-[210px] min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={fleetData} dataKey="value" nameKey="name" innerRadius="65%" outerRadius="88%" paddingAngle={3} stroke="var(--surface)">
                    {fleetData.map((entry) => <Cell key={entry.status} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(value, name) => [`${value ?? 0} buses`, name]} contentStyle={{ borderRadius: 10, borderColor: "var(--border)", background: "var(--surface)" }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-semibold tabular-nums text-foreground">{fleetTotal}</span>
                <span className="text-xs text-muted-foreground">total buses</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-1">
              {fleetData.map((entry) => (
                <div key={entry.status} className="rounded-lg bg-surface-secondary p-2.5 sm:p-3">
                  <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground sm:text-xs"><span className="size-2 rounded-full" style={{ backgroundColor: entry.color }} />{entry.name}</span>
                  <p className="mt-1 text-lg font-semibold tabular-nums text-foreground">{entry.value}</p>
                </div>
              ))}
            </div>
          </div>
        ) : <p className="py-12 text-center text-sm text-muted-foreground">No fleet records returned.</p>}
      </article>

      <article className="min-w-0 rounded-xl border border-border bg-surface p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-semibold text-foreground">Scheduled trips by hour</h2>
          </div>
          <div className="flex rounded-lg bg-surface-secondary p-1" aria-label="Filter trip chart">
            {([{ value: "all", label: "All day" }, { value: "morning", label: "Morning" }, { value: "afternoon", label: "Afternoon" }] as const).map((option) => (
              <button key={option.value} type="button" aria-pressed={tripPeriod === option.value} onClick={() => setTripPeriod(option.value)} className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition ${tripPeriod === option.value ? "bg-surface text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
                {option.label}
              </button>
            ))}
          </div>
        </div>
        {hourlyTrips.length ? (
          <div className="mt-3 h-[235px] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourlyTrips} margin={{ top: 8, right: 8, left: -18, bottom: 2 }} barCategoryGap="32%">
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="hour" tickFormatter={(hour) => `${String(hour).padStart(2, "0")}:00`} tick={{ fill: "var(--muted)", fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip labelFormatter={(hour) => `${String(hour).padStart(2, "0")}:00`} formatter={(value) => [`${value ?? 0} trips`, "Scheduled departures"]} contentStyle={{ borderRadius: 10, borderColor: "var(--border)", background: "var(--surface)" }} />
                <Bar dataKey="trips" name="Scheduled departures" fill="var(--primary)" radius={[5, 5, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : <p className="py-12 text-center text-sm text-muted-foreground">No scheduled trips returned for this period.</p>}
      </article>
    </section>
  );
}
