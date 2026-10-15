import type {
  Route,
  Vehicle,
  Trip,
} from "../../types/operations";

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

export default function RouteStatusTable({
  routes,
  vehicles,
  trips,
}: RouteStatusTableProps) {
  if (routes.length === 0) {
    return (
      <div className="rounded-lg border border-border px-4 py-10 text-center">
        <p className="text-sm font-medium text-foreground">
          No routes available
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Route information will appear here when data is available.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-160 text-left text-sm">
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
            const assignedVehicle = vehicles.find(
              (vehicle) => vehicle.routeId === route.id,
            );

            const scheduledTrips = trips.filter(
              (trip) =>
                trip.routeId === route.id &&
                trip.status === "scheduled",
            ).length;

            return (
              <tr
                key={route.id}
                className="transition-colors hover:bg-slate-50"
              >
                <td className="px-4 py-4 font-medium text-foreground">
                  {route.name}
                  <p className="mt-1 text-xs font-normal text-muted-foreground">
                    {route.id}
                  </p>
                </td>

                <td className="px-4 py-4 text-muted-foreground">
                  {route.stopIds.length}
                </td>

                <td className="px-4 py-4 text-muted-foreground">
                  {assignedVehicle?.id ?? "Unassigned"}
                </td>

                <td className="px-4 py-4 text-muted-foreground">
                  {scheduledTrips}
                </td>

                <td className="px-4 py-4">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles[route.status]}`}
                  >
                    {formatStatus(route.status)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
