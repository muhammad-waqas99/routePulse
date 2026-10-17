import type { Route, Stop, TransportAlert, Vehicle } from "../types/operations";

export function humanizeIdentifier(value: string): string {
  const patterns: Array<[RegExp, string]> = [
    [/^(route|r)[_-]?0*(\d+)$/i, "Route"],
    [/^(vehicle|bus|v)[_-]?0*(\d+)$/i, "Vehicle"],
    [/^(stop|s)[_-]?0*(\d+)$/i, "Stop"],
    [/^(trip|t)[_-]?0*(\d+)$/i, "Trip"],
  ];
  for (const [pattern, label] of patterns) {
    const match = pattern.exec(value.trim());
    if (match) return `${label} ${Number(match[2])}`;
  }
  return value.toLowerCase().replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function routeLabel(route: Route): string {
  return route.name && route.name !== route.id ? route.name : humanizeIdentifier(route.id);
}

export function scenarioLabel(value: string): string {
  const labels: Record<string, string> = {
    normal: "Normal operations",
    demand_surge: "Demand surge",
    road_closure: "Road closure",
    traffic_delay: "Traffic delay",
    vehicle_failure: "Vehicle failure",
  };
  return labels[value] ?? humanizeIdentifier(value);
}

export function presentAlert(
  alert: TransportAlert,
  routes: Route[] = [],
  vehicles: Vehicle[] = [],
  stops: Stop[] = [],
): TransportAlert {
  const references = new Map<string, string>();
  for (const route of routes) references.set(route.id, routeLabel(route));
  for (const vehicle of vehicles) references.set(vehicle.id, humanizeIdentifier(vehicle.id));
  for (const stop of stops) references.set(stop.id, stop.name || humanizeIdentifier(stop.id));

  const replaceReferences = (text: string) => {
    let result = text;
    for (const [id, label] of [...references.entries()].sort((a, b) => b[0].length - a[0].length)) {
      const escaped = id.replace(/[^\w-]/g, "\\$&");
      result = result.replace(new RegExp(`\\b${escaped}\\b`, "gi"), label);
    }
    return result.replace(/\btrip[_-]?(\d+)\b/gi, (_match, number: string) => `Trip ${Number(number)}`);
  };

  const route = routes.find((item) => item.id === alert.routeId);
  const vehicle = vehicles.find((item) => item.id === alert.vehicleId);
  const context = [route ? routeLabel(route) : "", vehicle ? humanizeIdentifier(vehicle.id) : ""].filter(Boolean);
  let description = replaceReferences(alert.description);
  for (const label of context) {
    if (!description.toLowerCase().includes(label.toLowerCase())) description += ` · ${label}`;
  }

  return {
    ...alert,
    title: replaceReferences(alert.title),
    description,
  };
}
