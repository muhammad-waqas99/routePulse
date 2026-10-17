import {
  BusFront,
  CalendarDays,
  Users,
  BellRing,
  MapPin,
  Clock,
  Route as RouteIcon,
} from "lucide-react";
import { useState } from "react";

import type { OperationsData } from "../types/operations";

import StatCard from "../components/dashboard/StatCard";
import AlertItem from "../components/dashboard/AlertItem";
import RouteStatusTable from "../components/dashboard/RouteStatusTable";
import DemandCapacityChart from "../components/dashboard/DemandCapacityChart";
import OperationsOverviewCharts from "../components/dashboard/OperationsOverviewCharts";
import CampusMap from "../components/map/CampusMap";
import { getNextStopArrival } from "../lib/arrivalEstimates";
import { presentAlert, routeLabel } from "../lib/presentation";

interface OperationsPageProps {
  data: OperationsData | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export default function OperationsPage({
  data: operationsData,
  loading,
  error,
  onRetry,
}: OperationsPageProps) {

  const [selectedStopId, setSelectedStopId] = useState<string | null>(
    null,
  );

  if (loading) {
    return (
      <div
        className="flex min-h-64 items-center justify-center"
        role="status"
      >
        <p className="text-sm text-secondary">
          Loading operations data...
        </p>
      </div>
    );
  }

  if (error || !operationsData) {
    return (
      <div className="rounded-xl border border-danger-border bg-surface p-4 sm:p-6">
        <div className="flex items-start gap-3" role="alert">
          <div className="rounded-lg bg-danger-soft px-2.5 py-1 text-xs font-semibold text-danger">Critical alert</div>
          <div>
            <h2 className="font-semibold text-foreground">Initial operations data could not load</h2>
            <p className="mt-2 break-words text-sm text-secondary">{error ?? "The operations API returned no data."}</p>
          </div>
        </div>
        <button type="button" onClick={onRetry} className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white">
          Retry loading data
        </button>
      </div>
    );
  }

  const {
    vehicles,
    trips,
    demand,
    alerts,
    routes,
    stops,
    etas,
  } = operationsData;

  const availableBuses = vehicles.filter(
    (vehicle) => vehicle.status === "available",
  ).length;

  const scheduledTrips = trips.filter(
    (trip) => trip.status === "scheduled",
  ).length;

  const passengerDemand = demand.reduce(
    (total, record) => total + record.passengerCount,
    0,
  );

  const activeSystemAlerts = alerts.filter((alert) => alert.status === "active");
  const activeAlerts = activeSystemAlerts.length;

  const statCards = [
    {
      title: "Available Buses",
      value: String(availableBuses),
      description: "Ready for service",
      icon: BusFront,
    },
    {
      title: "Scheduled Trips",
      value: String(scheduledTrips),
      description: "On the timetable",
      icon: CalendarDays,
    },
    {
      title: "Passenger Demand",
      value: String(passengerDemand),
      description: "Passengers across the network",
      icon: Users,
    },
    {
      title: "Active Alerts",
      value: String(activeAlerts),
      description: "Issues needing attention",
      icon: BellRing,
    },
  ];

  const selectedStop = stops.find(
    (stop) => stop.id === selectedStopId,
  );

  const routesAtStop = selectedStop
    ? routes.filter((route) =>
        route.stopIds.includes(selectedStop.id),
      )
    : [];

  const passengersWaiting = selectedStop
    ? demand
        .filter((record) => record.stopId === selectedStop.id)
        .reduce(
          (total, record) => total + record.passengerCount,
          0,
        )
    : 0;

  const nextArrival = selectedStop
    ? getNextStopArrival(selectedStop.id, routes, trips, etas)
    : undefined;

  return (
    <div className="space-y-6">
      <section aria-label="Transport metrics">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => (
            <StatCard
              key={card.title}
              title={card.title}
              value={card.value}
              description={card.description}
              icon={card.icon}
            />
          ))}
        </div>
      </section>

      <OperationsOverviewCharts vehicles={vehicles} trips={trips} />

      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            Campus Network
          </h2>
        </div>

        <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-[minmax(0,4fr)_minmax(220px,1fr)]">
          <div className="min-w-0 rounded-xl border border-border bg-white p-3 sm:p-5">
            <div className="mb-4">
              <h3 className="font-semibold text-foreground">
                Campus Transport Map
              </h3>
              <p className="mt-1 text-sm text-secondary">
                Select a stop to view its details.
              </p>
            </div>

            <CampusMap
              stops={stops}
              routes={routes}
              vehicles={vehicles}
              trips={trips}
              etas={etas}
              selectedStopId={selectedStopId}
              onStopSelect={setSelectedStopId}
            />
          </div>

          <aside
            aria-label="Selected stop details"
            className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5"
          >
            <div className="mb-5 flex items-center gap-2">
              <div className="rounded-lg bg-blue-50 p-2 text-primary">
                <MapPin size={19} />
              </div>

              <div>
                <h3 className="font-semibold text-foreground">
                  Stop Details
                </h3>
                <p className="text-xs text-secondary">
                  Selected campus stop
                </p>
              </div>
            </div>

            {selectedStop ? (
              <div className="space-y-5">
                <div>
                  <h4 className="mt-1 text-lg font-semibold text-foreground">
                    {selectedStop.name}
                  </h4>
                </div>

                <div className="border-t border-border pt-4">
                  <div className="flex items-center gap-2 text-sm text-secondary">
                    <RouteIcon size={16} />
                    <span>Routes served</span>
                  </div>

                  <div className="mt-2 flex flex-wrap gap-2">
                    {routesAtStop.length > 0 ? (
                      routesAtStop.map((route) => (
                        <span
                          key={route.id}
                          className="rounded-md bg-blue-50 px-2.5 py-1 text-sm font-medium text-primary"
                        >
                          {routeLabel(route)}
                        </span>
                      ))
                    ) : (
                      <p className="text-sm text-secondary">
                        No routes assigned
                      </p>
                    )}
                  </div>
                </div>

                <div className="border-t border-border pt-4">
                  <div className="flex items-center gap-2 text-sm text-secondary">
                    <Users size={16} />
                    <span>Passengers waiting</span>
                  </div>

                  <p className="mt-2 text-2xl font-semibold text-foreground">
                    {passengersWaiting}
                  </p>
                </div>

                <div className="border-t border-border pt-4">
                  <div className="flex items-center gap-2 text-sm text-secondary">
                    <Clock size={16} />
                    <span>Next arrival</span>
                  </div>

                  <p className="mt-2 text-lg font-semibold text-foreground">
                    {nextArrival
                      ? nextArrival.estimatedArrival
                      : "No arrival data"}
                  </p>

                  {nextArrival && (
                    <p className="mt-1 text-xs text-secondary">
                      {nextArrival.source === "live" ? "Live" : "Scheduled"} · {routeLabel(routes.find((route) => route.id === nextArrival.routeId) ?? { id: nextArrival.routeId, name: nextArrival.routeId, stopIds: [], status: "active" })}{nextArrival.dayOffset ? ` · +${nextArrival.dayOffset} day` : ""}
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedStopId(null)}
                  className="w-full rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground transition hover:bg-slate-50"
                >
                  Clear selection
                </button>
              </div>
            ) : (
              <div className="flex min-h-64 flex-col items-center justify-center text-center">
                <div className="rounded-full bg-slate-100 p-3 text-secondary">
                  <MapPin size={22} />
                </div>

                <h4 className="mt-4 font-medium text-foreground">
                  No stop selected
                </h4>
                <p className="mt-2 max-w-48 text-sm text-secondary">
                  Click any stop marker on the map to view its routes,
                  passenger demand, and arrival information.
                </p>
              </div>
            )}
          </aside>
        </div>
      </section>

      <section className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
          <h2 className="mb-4 font-semibold text-foreground">
            Route Status
          </h2>

          <RouteStatusTable
            routes={routes}
            vehicles={vehicles}
            trips={trips}
          />
        </div>

        <div className="min-w-0 rounded-xl border border-border bg-white p-4 sm:p-5">
          <h2 className="mb-4 font-semibold text-foreground">
            Demand vs. Capacity
          </h2>

          <DemandCapacityChart
            demand={demand}
            stops={stops}
            vehicles={vehicles}
            routes={routes}
            trips={trips}
          />
        </div>
      </section>

      <section className="rounded-xl border border-border bg-white p-4 sm:p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="font-semibold text-foreground">Active operational alerts</h2>
            <p className="mt-1 text-xs text-secondary">Issues needing attention</p>
          </div>
          <span className="rounded-full bg-primary-soft px-2.5 py-1 text-xs font-medium text-primary">{activeAlerts} active</span>
        </div>

        <div className="space-y-3">
          {activeSystemAlerts.map((alert) => <AlertItem key={alert.id} alert={presentAlert(alert, routes, vehicles, stops)} />)}

          {activeAlerts === 0 && (
            <p className="text-sm text-secondary">
              No active operational issues were returned.
            </p>
          )}
        </div>
      </section>

    </div>
  );
}
