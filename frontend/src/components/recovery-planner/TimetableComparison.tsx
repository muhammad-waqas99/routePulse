
import type { OptimizationResult } from "../../types/optimization";

interface Props {
  result: OptimizationResult;
}

export default function TimetableComparison({ result }: Props) {
  const changedIds = new Set(
    result.proposedTrips
      .filter((trip) => {
        const original = result.originalTrips.find(
          (item) => item.tripId === trip.tripId,
        );

        return (
          original &&
          (original.departureTime !== trip.departureTime ||
            original.vehicleId !== trip.vehicleId ||
            original.routeId !== trip.routeId)
        );
      })
      .map((trip) => trip.tripId),
  );

  const plans = [
    {
      title: "Original Plan",
      trips: result.originalTrips,
      proposed: false,
    },
    {
      title: "Proposed Plan",
      trips: result.proposedTrips,
      proposed: true,
    },
  ];

  return (
    <section className="min-w-0 space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-foreground">
          Timetable Comparison
        </h3>
        <p className="mt-1 text-sm text-secondary">
          Compare the original schedule with the proposed plan.
        </p>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">
        {plans.map((plan) => (
          <div
            key={plan.title}
            className="min-w-0 overflow-hidden rounded-xl border border-border bg-white"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border p-4">
              <h4 className="font-semibold text-foreground">
                {plan.title}
              </h4>

              <span className="text-xs text-secondary">
                {plan.trips.length} of {result.totalTrips} trips shown
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[440px] text-left text-sm">
                <thead className="bg-slate-50 text-xs text-secondary">
                  <tr>
                    {["Trip", "Route", "Vehicle", "Departure"].map(
                      (heading) => (
                        <th
                          key={heading}
                          className="px-3 py-3 font-medium sm:px-4"
                        >
                          {heading}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>

                <tbody className="divide-y divide-border">
                  {plan.trips.map((trip) => {
                    const changed =
                      plan.proposed && changedIds.has(trip.tripId);

                    return (
                      <tr
                        key={trip.tripId}
                        className={changed ? "bg-blue-50/70" : ""}
                      >
                        <td className="whitespace-nowrap px-3 py-3 font-medium text-foreground sm:px-4">
                          {trip.tripId}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3 text-secondary sm:px-4">
                          {trip.routeId}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3 text-secondary sm:px-4">
                          {trip.vehicleId}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3 sm:px-4">
                          <span
                            className={
                              changed
                                ? "font-semibold text-primary"
                                : "text-foreground"
                            }
                          >
                            {trip.departureTime}
                          </span>

                          {changed && (
                            <span className="ml-2 text-xs text-primary">
                              Changed
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}

                  {plan.trips.length === 0 && (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-6 text-center text-sm text-secondary"
                      >
                        No trips returned for this plan.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-secondary">
        Showing {result.originalTrips.length} original trips and{" "}
        {result.proposedTrips.length} proposed trips returned by the API.
      </p>
    </section>
  );
}
