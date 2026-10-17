import type { Route, Trip, Vehicle } from "../../types/operations";
import { humanizeIdentifier, routeLabel } from "../../lib/presentation";

interface RouteStatusTableProps {
  routes: Route[];
  vehicles: Vehicle[];
  trips: Trip[];
}

const statusStyles: Record<Route["status"], string> = {
  active: "bg-green-50 text-green-700",
  delayed: "bg-amber-50 text-amber-700",
  disrupted: "bg-red-50 text-red-700",
  inactive: "bg-slate-100 text-slate-600",
};

function formatStatus(status: Route["status"]) {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export default function RouteStatusTable({ routes, vehicles, trips }: RouteStatusTableProps) {
  if (!routes.length) {
    return (
      <div className="rounded-lg border border-border px-4 py-10 text-center">
        <p className="text-sm font-medium text-foreground">No routes available</p>
        <p className="mt-1 text-sm text-muted-foreground">Route information will appear here when data is available.</p>
      </div>
    );
  }

  return (
    <div>
      <ul className="grid gap-2 md:hidden">
        {routes.map((route) => {
          const assignedVehicle = vehicles.find((vehicle) => vehicle.routeId === route.id);
          const scheduledTrips = trips.filter((trip) => trip.routeId === route.id && trip.status === "scheduled").length;
          return <li key={route.id} className="rounded-lg border border-border p-3">
            <div className="flex items-start justify-between gap-2"><p className="min-w-0 break-words text-sm font-semibold text-foreground">{routeLabel(route)}</p><span className={`shrink-0 rounded-full px-2 py-1 text-xs font-medium ${statusStyles[route.status]}`}>{formatStatus(route.status)}</span></div>
            <div className="mt-2 grid grid-cols-3 gap-2 text-xs"><span className="text-secondary">{route.stopIds.length} stops</span><span className="truncate text-secondary">{assignedVehicle ? humanizeIdentifier(assignedVehicle.id) : "Unassigned"}</span><span className="text-right text-secondary">{scheduledTrips} trips</span></div>
          </li>;
        })}
      </ul>
      <div className="hidden overflow-x-auto md:block">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-3 font-medium">Route</th>
            <th className="px-4 py-3 font-medium">Stops</th>
            <th className="px-4 py-3 font-medium">Assigned Bus</th>
            <th className="px-4 py-3 font-medium">Scheduled Trips</th>
            <th className="px-4 py-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {routes.map((route) => {
            const assignedVehicle = vehicles.find((vehicle) => vehicle.routeId === route.id);
            const scheduledTrips = trips.filter((trip) => trip.routeId === route.id && trip.status === "scheduled").length;

            return (
              <tr key={route.id} className="transition-colors hover:bg-slate-50">
                <td className="max-w-48 break-words px-4 py-4 font-medium text-foreground">{routeLabel(route)}</td>
                <td className="px-4 py-4 text-muted-foreground">{route.stopIds.length}</td>
                <td className="px-4 py-4 text-muted-foreground">{assignedVehicle ? humanizeIdentifier(assignedVehicle.id) : "Unassigned"}</td>
                <td className="px-4 py-4 text-muted-foreground">{scheduledTrips}</td>
                <td className="px-4 py-4">
                  <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles[route.status]}`}>
                    {formatStatus(route.status)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
    </div>
  );
}
