import { useMemo, useState, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, BusFront, TrendingUp, Users } from "lucide-react";
import type { DemandRecord, Route, Stop, Trip, Vehicle } from "../../types/operations";

interface DemandCapacityChartProps {
  demand: DemandRecord[];
  stops: Stop[];
  vehicles: Vehicle[];
  routes: Route[];
  trips: Trip[];
}

interface IntervalData {
  time: string;
  timeLabel: string;
  demand: number | null;
  capacity: number;
  shortage: number | null;
  utilization: number | null;
  primaryStopName: string | null;
  additionalStopCount: number;
  hasDemandData: boolean;
}

type Period = "all" | "morning" | "midday" | "evening";
const INTERVAL_MINUTES = 15;
const periodOptions: Array<{ value: Period; label: string }> = [
  { value: "all", label: "All day" },
  { value: "morning", label: "Morning" },
  { value: "midday", label: "Midday" },
  { value: "evening", label: "Evening" },
];

function formatTime(minutes: number) {
  const normalized = ((minutes % 1440) + 1440) % 1440;
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
}

function parseTime(time: string) {
  const match = /^(\d{1,2}):(\d{2})$/.exec(time);
  if (!match) return null;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  return hours <= 23 && minutes <= 59 ? hours * 60 + minutes : null;
}

function intervalStart(minutes: number) {
  return Math.floor(minutes / INTERVAL_MINUTES) * INTERVAL_MINUTES;
}

function includedInPeriod(time: string, period: Period) {
  if (period === "all") return true;
  const hour = (parseTime(time) ?? 0) / 60;
  if (period === "morning") return hour >= 7 && hour < 11;
  if (period === "midday") return hour >= 11 && hour < 15;
  return hour >= 15;
}

export default function DemandCapacityChart({ demand, stops, vehicles, routes, trips }: DemandCapacityChartProps) {
  const [period, setPeriod] = useState<Period>("all");
  const allChartData = useMemo<IntervalData[]>(() => {
    const stopById = new Map(stops.map((stop) => [stop.id, stop]));
    const routeById = new Map(routes.map((route) => [route.id, route]));
    const vehicleById = new Map(vehicles.map((vehicle) => [vehicle.id, vehicle]));
    const demandByInterval = new Map<number, { total: number; stopIds: Set<string>; byStop: Map<string, number> }>();
    const times: number[] = [];

    for (const record of demand) {
      const minutes = parseTime(record.time);
      if (minutes === null) continue;
      times.push(minutes);
      const start = intervalStart(minutes);
      const existing = demandByInterval.get(start) ?? { total: 0, stopIds: new Set<string>(), byStop: new Map<string, number>() };
      existing.total += record.passengerCount;
      existing.stopIds.add(record.stopId);
      existing.byStop.set(record.stopId, (existing.byStop.get(record.stopId) ?? 0) + record.passengerCount);
      demandByInterval.set(start, existing);
    }

    const parsedTrips = trips.flatMap((trip) => {
      const departure = parseTime(trip.departureTime);
      const route = routeById.get(trip.routeId);
      if (departure === null || !route || trip.status === "cancelled") return [];
      const duration = route.segmentTravelMin?.reduce((sum, minutes) => sum + minutes, 0) ?? 0;
      if (!duration) return [];
      times.push(departure);
      return [{ trip, route, departure, arrival: departure + duration }];
    });

    if (!times.length) return [];
    const first = intervalStart(Math.min(...times));
    const last = Math.max(...times, ...parsedTrips.map((item) => item.arrival));
    const intervals: IntervalData[] = [];

    for (let start = first; start <= last; start += INTERVAL_MINUTES) {
      const intervalDemand = demandByInterval.get(start);
      const stopIds = intervalDemand?.stopIds ?? new Set<string>();
      const relevantRoutes = new Set(routes.filter((route) => route.stopIds.some((id) => stopIds.has(id))).map((route) => route.id));
      const activeVehicleIds = new Set<string>();

      for (const item of parsedTrips) {
        if (item.departure <= start && start < item.arrival && relevantRoutes.has(item.route.id)) {
          const vehicle = vehicleById.get(item.trip.vehicleId);
          if (vehicle && vehicle.status !== "unavailable") activeVehicleIds.add(vehicle.id);
        }
      }

      const capacity = [...activeVehicleIds].reduce((sum, id) => sum + (vehicleById.get(id)?.capacity ?? 0), 0);
      const passengerDemand = intervalDemand?.total ?? null;
      const primaryStopId = intervalDemand
        ? [...intervalDemand.byStop.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]
        : undefined;
      intervals.push({
        time: formatTime(start),
        timeLabel: `${formatTime(start)}–${formatTime(start + INTERVAL_MINUTES)}`,
        demand: passengerDemand,
        capacity,
        shortage: passengerDemand === null ? null : Math.max(0, passengerDemand - capacity),
        utilization: passengerDemand === null || capacity === 0 ? null : (passengerDemand / capacity) * 100,
        primaryStopName: primaryStopId ? stopById.get(primaryStopId)?.name ?? null : null,
        additionalStopCount: Math.max(0, (intervalDemand?.byStop.size ?? 0) - (primaryStopId ? 1 : 0)),
        hasDemandData: intervalDemand !== undefined,
      });
    }
    return intervals;
  }, [demand, stops, vehicles, routes, trips]);

  const chartData = useMemo(() => allChartData.filter((item) => includedInPeriod(item.time, period)), [allChartData, period]);
  const summary = useMemo(() => {
    const recorded = chartData.filter((item) => item.hasDemandData);
    const totalDemand = recorded.reduce((sum, item) => sum + (item.demand ?? 0), 0);
    const nearCapacity = recorded.filter((item) => item.capacity > 0 && item.demand !== null && item.demand <= item.capacity && item.demand / item.capacity >= 0.8).length;
    const overCapacity = recorded.filter((item) => item.demand !== null && item.demand > item.capacity).length;
    const peak = recorded.reduce<IntervalData | null>((current, item) => (item.shortage ?? 0) > (current?.shortage ?? 0) ? item : current, null);
    return { totalDemand, nearCapacity, overCapacity, peakShortage: peak?.shortage ?? 0, peakWindow: peak?.timeLabel ?? null };
  }, [chartData]);

  if (!stops.length || !allChartData.some((item) => item.hasDemandData)) {
    return <div className="rounded-xl border border-warning-border bg-warning-soft p-4 text-sm text-warning">Demand or timetable data is missing, so capacity charts cannot be calculated.</div>;
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-foreground">Passenger demand vs scheduled capacity</h3>
          <p className="mt-1 text-sm text-secondary">15-minute intervals</p>
        </div>
        <div className="flex flex-wrap gap-1 rounded-lg bg-surface-secondary p-1" aria-label="Filter demand chart by time of day">
          {periodOptions.map((option) => (
            <button key={option.value} type="button" aria-pressed={period === option.value} onClick={() => setPeriod(option.value)} className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition ${period === option.value ? "bg-surface text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <SummaryCard label="Recorded demand" value={summary.totalDemand.toLocaleString()} description="Passengers in selected time range" icon={<Users size={17} />} />
        <SummaryCard label="Near capacity" value={String(summary.nearCapacity)} description="Intervals at 80% or more" icon={<TrendingUp size={17} />} />
        <SummaryCard label="Over capacity" value={String(summary.overCapacity)} description="Demand exceeds scheduled seats" icon={<AlertTriangle size={17} />} danger={summary.overCapacity > 0} />
        <SummaryCard label="Peak shortage" value={summary.peakWindow ? `${summary.peakShortage} passengers` : "None"} description={summary.peakWindow ?? "No shortage in this range"} icon={<BusFront size={17} />} danger={summary.peakShortage > 0} />
      </div>

      <div className="h-[310px] w-full min-w-0 rounded-xl border border-border bg-surface p-3 sm:h-[350px] sm:p-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 14, right: 12, left: -16, bottom: 4 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: "var(--muted)", fontSize: 10 }} tickLine={false} axisLine={false} interval={Math.max(0, Math.ceil(chartData.length / 8) - 1)} />
            <YAxis allowDecimals={false} tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false} axisLine={false} />
            <Tooltip content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const item = payload[0]?.payload as IntervalData | undefined;
              if (!item) return null;
              return (
                <div className="min-w-52 rounded-lg border border-border bg-surface p-3 text-sm shadow-dropdown">
                  <p className="font-semibold text-foreground">{item.primaryStopName ?? item.timeLabel}{item.additionalStopCount > 0 ? ` + ${item.additionalStopCount}` : ""}</p>
                  <p className="mt-0.5 text-xs text-secondary">{item.timeLabel}</p>
                  {item.hasDemandData ? (
                    <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-secondary">
                      <span>Demand</span><strong className="text-right text-foreground">{item.demand}</strong>
                      <span>Capacity</span><strong className="text-right text-foreground">{item.capacity}</strong>
                      <span>Load</span><strong className="text-right text-foreground">{item.utilization === null ? "—" : `${item.utilization.toFixed(0)}%`}</strong>
                    </div>
                  ) : <p className="mt-2 text-secondary">No demand record for this interval.</p>}
                </div>
              );
            }} />
            <Legend verticalAlign="top" align="right" wrapperStyle={{ fontSize: 11, paddingBottom: 8 }} />
            <Area type="monotone" dataKey="demand" name="Passenger demand" stroke="var(--primary)" fill="var(--primary-soft)" strokeWidth={2.5} connectNulls={false} activeDot={{ r: 5 }} />
            <Area type="monotone" dataKey="capacity" name="Scheduled seat capacity" stroke="var(--info)" fill="var(--info-soft)" strokeWidth={2} connectNulls activeDot={{ r: 4 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function SummaryCard({ label, value, description, icon, danger = false }: { label: string; value: string; description: string; icon: ReactNode; danger?: boolean }) {
  return (
    <article className={`min-w-0 rounded-xl border p-3 sm:p-4 ${danger ? "border-danger-border bg-danger-soft/60" : "border-border bg-surface"}`}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-muted-foreground sm:text-sm">{label}</p>
        <span className={danger ? "text-danger" : "text-primary"}>{icon}</span>
      </div>
      <p className={`mt-2 truncate text-xl font-semibold tabular-nums sm:text-2xl ${danger ? "text-danger" : "text-foreground"}`}>{value}</p>
      <p className="mt-1 truncate text-[11px] text-muted-foreground sm:text-xs">{description}</p>
    </article>
  );
}
