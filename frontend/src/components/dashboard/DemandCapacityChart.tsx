import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, TrendingUp, Users, BusFront } from "lucide-react";

import type {
  DemandRecord,
  Route,
  Stop,
  Vehicle,
} from "../../types/operations";

interface DemandCapacityChartProps {
  demand: DemandRecord[];
  stops: Stop[];
  vehicles: Vehicle[];
  routes: Route[];
}

interface IntervalData {
  time: string;
  timeLabel: string;
  demand: number | null;
  capacity: number;
  shortage: number | null;
  utilization: number | null;
  stopNames: string[];
  hasDemandData: boolean;
}

const START_MINUTES = 7 * 60;
const END_MINUTES = 10 * 60;
const INTERVAL_MINUTES = 15;

function formatTime(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

function parseTime(time: string) {
  const [hours, minutes] = time.split(":").map(Number);

  if (
    !Number.isFinite(hours) ||
    !Number.isFinite(minutes) ||
    hours < 0 ||
    hours > 23 ||
    minutes < 0 ||
    minutes > 59
  ) {
    return null;
  }

  return hours * 60 + minutes;
}

function getIntervalStart(minutes: number) {
  return Math.floor(minutes / INTERVAL_MINUTES) * INTERVAL_MINUTES;
}

export default function DemandCapacityChart({
  demand,
  stops,
  vehicles,
  routes,
}: DemandCapacityChartProps) {
  const chartData = useMemo<IntervalData[]>(() => {
    const stopById = new Map(stops.map((stop) => [stop.id, stop]));
    const routeById = new Map(routes.map((route) => [route.id, route]));

    const demandByInterval = new Map<
      number,
      { total: number; stopIds: Set<string> }
    >();

    for (const record of demand) {
      const minutes = parseTime(record.time);

      if (minutes === null) continue;

      const intervalStart = getIntervalStart(minutes);
      const existing = demandByInterval.get(intervalStart) ?? {
        total: 0,
        stopIds: new Set<string>(),
      };

      existing.total += record.passengerCount;
      existing.stopIds.add(record.stopId);
      demandByInterval.set(intervalStart, existing);
    }

    const intervals: IntervalData[] = [];

    for (
      let start = START_MINUTES;
      start < END_MINUTES;
      start += INTERVAL_MINUTES
    ) {
      const end = start + INTERVAL_MINUTES;
      const intervalDemand = demandByInterval.get(start);
      const stopIds = intervalDemand?.stopIds ?? new Set<string>();


      const relevantRouteIds = new Set<string>();

      for (const route of routes) {
        if (route.stopIds.some((stopId) => stopIds.has(stopId))) {
          relevantRouteIds.add(route.id);
        }
      }

      
      const capacity = vehicles
        .filter(
          (vehicle) =>
            vehicle.status === "in-service" &&
            vehicle.routeId &&
            relevantRouteIds.has(vehicle.routeId) &&
            routeById.has(vehicle.routeId),
        )
        .reduce((total, vehicle) => total + vehicle.capacity, 0);

      const passengerDemand = intervalDemand?.total ?? null;
      const shortage =
        passengerDemand === null
          ? null
          : Math.max(0, passengerDemand - capacity);

      const stopNames = [...stopIds]
        .map((id) => stopById.get(id)?.name)
        .filter((name): name is string => Boolean(name));

      intervals.push({
        time: formatTime(start),
        timeLabel: `${formatTime(start)}–${formatTime(end)}`,
        demand: passengerDemand,
        capacity,
        shortage,
        utilization:
          passengerDemand === null || capacity === 0
            ? null
            : (passengerDemand / capacity) * 100,
        stopNames,
        hasDemandData: intervalDemand !== undefined,
      });
    }

    return intervals;
  }, [demand, stops, vehicles, routes]);

  const summary = useMemo(() => {
    const recordedIntervals = chartData.filter(
      (item) => item.hasDemandData,
    );

    const totalDemand = recordedIntervals.reduce(
      (total, item) => total + (item.demand ?? 0),
      0,
    );

    const nearCapacity = recordedIntervals.filter(
      (item) =>
        item.capacity > 0 &&
        item.demand !== null &&
        item.demand <= item.capacity &&
        item.demand / item.capacity >= 0.8,
    ).length;

    const overCapacity = recordedIntervals.filter(
      (item) =>
        item.demand !== null && item.demand > item.capacity,
    ).length;

    let peakShortage = 0;
    let peakWindow: string | null = null;

    for (let index = 0; index < chartData.length - 1; index++) {
      const first = chartData[index];
      const second = chartData[index + 1];


      if (
        first.demand === null ||
        second.demand === null ||
        !first.hasDemandData ||
        !second.hasDemandData
      ) {
        continue;
      }

      const combinedDemand = first.demand + second.demand;
      const combinedCapacity = first.capacity + second.capacity;
      const shortage = Math.max(0, combinedDemand - combinedCapacity);

      if (shortage > peakShortage) {
        peakShortage = shortage;
        peakWindow = `${first.time}–${formatTime(
          (parseTime(second.time) ?? 0) + INTERVAL_MINUTES,
        )}`;
      }
    }

    return {
      totalDemand,
      nearCapacity,
      overCapacity,
      peakShortage,
      peakWindow,
    };
  }, [chartData]);

  if (stops.length === 0 || chartData.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
        Demand and capacity data is not available yet.
      </div>
    );
  }

  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          Demand vs Capacity
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Expected passenger demand compared with available vehicle capacity.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Recorded Demand"
          value={summary.totalDemand.toLocaleString()}
          description="Passengers across recorded intervals"
          icon={<Users size={18} />}
        />
        <SummaryCard
          label="Near Capacity"
          value={String(summary.nearCapacity)}
          description="Intervals at 80–100% capacity"
          icon={<TrendingUp size={18} />}
        />
        <SummaryCard
          label="Over Capacity"
          value={String(summary.overCapacity)}
          description="Intervals where demand exceeds capacity"
          icon={<AlertTriangle size={18} />}
          danger={summary.overCapacity > 0}
        />
        <SummaryCard
          label="Peak Shortage"
          value={
            summary.peakWindow
              ? `${summary.peakShortage} passengers`
              : "Not identified"
          }
          description={
            summary.peakWindow
              ? summary.peakWindow
              : "Need consecutive intervals with demand data"
          }
          icon={<BusFront size={18} />}
          danger={summary.peakShortage > 0}
        />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
        <div className="mb-5">
          <h3 className="font-semibold text-slate-900">
            Passenger demand versus capacity by 15-minute interval
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            Hover over a bar to inspect demand, capacity and affected stops.
          </p>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 8, right: 8, left: -16, bottom: 4 }}
              barCategoryGap="25%"
            >
              <CartesianGrid
                stroke="#E2E8F0"
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="time"
                tick={{ fill: "#64748B", fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: "#E2E8F0" }}
                interval={0}
                angle={-45}
                textAnchor="end"
                height={52}
              />

              <YAxis
                allowDecimals={false}
                tick={{ fill: "#64748B", fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />

              <Tooltip
                cursor={{ fill: "#F1F5F9" }}
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;

                  const item = payload[0]?.payload as
                    | IntervalData
                    | undefined;

                  if (!item) return null;

                  return (
                    <div className="max-w-xs rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
                      <p className="font-semibold text-slate-900">
                        {item.timeLabel}
                      </p>

                      {!item.hasDemandData ? (
                        <p className="mt-2 text-sm text-slate-500">
                          No demand records for this interval.
                        </p>
                      ) : (
                        <div className="mt-2 space-y-1 text-sm">
                          <p>Demand: {item.demand} passengers</p>
                          <p>Available capacity: {item.capacity}</p>
                          <p>
                            Shortage: {item.shortage} passengers
                          </p>
                          <p>
                            Capacity utilization:{" "}
                            {item.utilization === null
                              ? "Unavailable"
                              : `${item.utilization.toFixed(0)}%`}
                          </p>

                          {item.stopNames.length > 0 && (
                            <p className="mt-2 border-t border-slate-100 pt-2 text-slate-500">
                              Stops: {item.stopNames.join(", ")}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                }}
              />

              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ fontSize: 12, paddingBottom: 12 }}
              />

              <Bar
                dataKey="demand"
                name="Passenger Demand"
                radius={[4, 4, 0, 0]}
                maxBarSize={24}
              >
                {chartData.map((item) => (
                  <Cell
                    key={item.time}
                    fill={
                      item.demand === null
                        ? "#CBD5E1"
                        : item.demand > item.capacity
                          ? "#DC2626"
                          : item.capacity > 0 &&
                              item.demand / item.capacity >= 0.8
                            ? "#D97706"
                            : "#2563EB"
                    }
                  />
                ))}
              </Bar>

              <Bar
                dataKey="capacity"
                name="Available Capacity (estimate)"
                fill="#94A3B8"
                radius={[4, 4, 0, 0]}
                maxBarSize={24}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-600">
          <span className="flex items-center gap-2">
            <span className="size-2.5 rounded-sm bg-blue-600" />
            Capacity sufficient
          </span>
          <span className="flex items-center gap-2">
            <span className="size-2.5 rounded-sm bg-amber-600" />
            Near capacity
          </span>
          <span className="flex items-center gap-2">
            <span className="size-2.5 rounded-sm bg-red-600" />
            Demand exceeds capacity
          </span>
        </div>

        <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <h4 className="text-sm font-semibold text-slate-900">
            Capacity Shortage Insight
          </h4>
          {summary.peakWindow && summary.peakShortage > 0 ? (
            <p className="mt-1 text-sm text-slate-600">
              The greatest combined shortage occurs between{" "}
              <strong>{summary.peakWindow}</strong>, with an estimated
              shortage of <strong>{summary.peakShortage} passengers</strong>
              .
            </p>
          ) : (
            <p className="mt-1 text-sm text-slate-600">
              A peak shortage cannot be identified until consecutive
              15-minute intervals have recorded demand and capacity data.
            </p>
          )}
        </div>

        <p className="mt-4 text-xs leading-5 text-slate-500">
          Demand is grouped into 15-minute intervals. Missing demand
          records are shown as unavailable, not zero. Capacity is estimated
          from in-service vehicles assigned to routes serving stops with
          recorded demand; it is not a time-specific live vehicle forecast.
        </p>
      </div>
    </section>
  );
}

function SummaryCard({
  label,
  value,
  description,
  icon,
  danger = false,
}: {
  label: string;
  value: string;
  description: string;
  icon: React.ReactNode;
  danger?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-slate-500">{label}</p>
        <span className={danger ? "text-red-600" : "text-slate-500"}>
          {icon}
        </span>
      </div>
      <p
        className={`mt-3 text-2xl font-semibold ${
          danger ? "text-red-600" : "text-slate-900"
        }`}
      >
        {value}
      </p>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        {description}
      </p>
    </div>
  );
}
