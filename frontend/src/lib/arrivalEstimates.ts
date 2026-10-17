import type { EtaRecord, Route, Trip } from "../types/operations";

export interface StopArrival {
  tripId: string;
  routeId: string;
  scheduledArrival: string;
  estimatedArrival: string;
  dayOffset: number;
  source: "live" | "schedule";
}

function parseTime(value: string): number | null {
  const match = /^(\d{1,2}):(\d{2})$/.exec(value);
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

function formatTime(minutes: number): string {
  const normalized = ((minutes % 1440) + 1440) % 1440;
  return `${String(Math.floor(normalized / 60)).padStart(2, "0")}.${String(normalized % 60).padStart(2, "0")}`;
}

function formatClock(value: string): string {
  return value.replace(/^(\d{1,2}):(\d{2})$/, (_match, hours: string, minutes: string) =>
    `${hours.padStart(2, "0")}.${minutes}`,
  );
}

export function getNextStopArrival(
  stopId: string,
  routes: Route[],
  trips: Trip[],
  etas: EtaRecord[],
  now = new Date(),
): StopArrival | null {
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  const live = etas.filter((eta) => eta.stopId === stopId)
    .map((eta) => ({
      tripId: eta.tripId,
      routeId: trips.find((trip) => trip.id === eta.tripId)?.routeId ?? "",
      scheduledArrival: formatClock(eta.scheduledArrival),
      estimatedArrival: formatClock(eta.estimatedArrival),
      dayOffset: 0,
      source: "live" as const,
    }))
    .sort((first, second) => first.estimatedArrival.localeCompare(second.estimatedArrival));
  if (live.length) return live[0];

  const routeById = new Map(routes.map((route) => [route.id, route]));
  const candidates: Array<StopArrival & { minutesAway: number }> = [];
  for (const trip of trips) {
    const route = routeById.get(trip.routeId);
    const stopIndex = route?.stopIds.indexOf(stopId) ?? -1;
    const departure = parseTime(trip.departureTime);
    if (!route || stopIndex < 0 || departure === null || !route.segmentTravelMin) continue;
    const travelTime = route.segmentTravelMin.slice(0, stopIndex).reduce((total, minutes) => total + minutes, 0);
    let arrivalMinute = departure + travelTime;
    let dayOffset = 0;
    while (arrivalMinute < nowMinutes) {
      arrivalMinute += 1440;
      dayOffset += 1;
    }
    candidates.push({
      tripId: trip.id,
      routeId: trip.routeId,
      scheduledArrival: formatClock(trip.departureTime),
      estimatedArrival: formatTime(arrivalMinute),
      dayOffset,
      source: "schedule",
      minutesAway: arrivalMinute - nowMinutes,
    });
  }
  candidates.sort((first, second) => first.minutesAway - second.minutesAway);
  return candidates[0] ?? null;
}
