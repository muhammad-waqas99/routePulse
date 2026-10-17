import { useEffect, useMemo, useState } from "react";
import savedRoadRoutes from "../data/routeGeometry.json";
import type { Route, Stop } from "../types/operations";

export type LatLng = [number, number];

const savedGeometry = savedRoadRoutes as Record<string, number[][]>;
const geometryCache = new Map<string, Promise<LatLng[]>>();

function getMapItinerary(route: Route, stopsById: Map<string, Stop>): Stop[] {
  const orderedStops = route.stopIds
    .map((stopId) => stopsById.get(stopId))
    .filter((stop): stop is Stop => Boolean(stop));
  const college = stopsById.get("S01");
  if (!college || orderedStops.length === 0) return orderedStops;
  if (orderedStops[orderedStops.length - 1]?.id === college.id) return orderedStops;

  const routeStops = orderedStops.filter((stop) => stop.id !== college.id);
  return [college, ...routeStops, college];
}

function toLatLng(stops: Stop[]): LatLng[] {
  return stops.map((stop) => [stop.latitude, stop.longitude]);
}

function savedRouteGeometry(route: Route): LatLng[] {
  return (savedGeometry[route.id] ?? []).map(([longitude, latitude]) => [latitude, longitude]);
}

function combineGeometry(...segments: LatLng[][]): LatLng[] {
  return segments.reduce<LatLng[]>((combined, segment) => {
    if (segment.length === 0) return combined;
    combined.push(...(combined.length ? segment.slice(1) : segment));
    return combined;
  }, []);
}

interface RoadEdge {
  to: string;
  points: LatLng[];
  distance: number;
}

function distanceMeters(a: LatLng, b: LatLng): number {
  const latitudeScale = 111_320;
  const longitudeScale = latitudeScale * Math.cos(((a[0] + b[0]) / 2) * Math.PI / 180);
  return Math.hypot((a[0] - b[0]) * latitudeScale, (a[1] - b[1]) * longitudeScale);
}

function nearestPointIndex(points: LatLng[], stop: Stop, fromIndex: number): number {
  let bestIndex = fromIndex;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (let index = fromIndex; index < points.length; index += 1) {
    const distance = distanceMeters(points[index], [stop.latitude, stop.longitude]);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  }
  return bestDistance <= 80 ? bestIndex : -1;
}

function buildRoadGraph(routes: Route[], stopsById: Map<string, Stop>): Map<string, RoadEdge[]> {
  const graph = new Map<string, RoadEdge[]>();
  const addEdge = (from: string, to: string, points: LatLng[]) => {
    const distance = points.slice(1).reduce((total, point, index) => total + distanceMeters(points[index], point), 0);
    graph.set(from, [...(graph.get(from) ?? []), { to, points, distance }]);
    graph.set(to, [...(graph.get(to) ?? []), { to: from, points: [...points].reverse(), distance }]);
  };

  for (const route of routes) {
    const routeStops = route.stopIds.map((id) => stopsById.get(id)).filter((stop): stop is Stop => Boolean(stop));
    const points = savedRouteGeometry(route);
    if (routeStops.length < 2 || points.length < 2) continue;

    let previousIndex = 0;
    const stopIndexes: number[] = [];
    for (const stop of routeStops) {
      const index = nearestPointIndex(points, stop, previousIndex);
      if (index < previousIndex) break;
      stopIndexes.push(index);
      previousIndex = index;
    }
    if (stopIndexes.length !== routeStops.length) continue;

    for (let index = 0; index < routeStops.length - 1; index += 1) {
      const segment = points.slice(stopIndexes[index], stopIndexes[index + 1] + 1);
      if (segment.length > 1) addEdge(routeStops[index].id, routeStops[index + 1].id, segment);
    }
  }
  return graph;
}

function getRoadConnection(from: string, to: string, routes: Route[], stopsById: Map<string, Stop>): LatLng[] {
  if (from === to) {
    const stop = stopsById.get(from);
    return stop ? [[stop.latitude, stop.longitude]] : [];
  }

  const graph = buildRoadGraph(routes, stopsById);
  const distances = new Map<string, number>([[from, 0]]);
  const previous = new Map<string, { node: string; points: LatLng[] }>();
  const pending = new Set(graph.keys());
  pending.add(from);

  while (pending.size) {
    let current: string | undefined;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (const node of pending) {
      const distance = distances.get(node) ?? Number.POSITIVE_INFINITY;
      if (distance < bestDistance) {
        current = node;
        bestDistance = distance;
      }
    }
    if (!current || !Number.isFinite(bestDistance)) break;
    pending.delete(current);
    if (current === to) break;

    for (const edge of graph.get(current) ?? []) {
      const candidate = bestDistance + edge.distance;
      if (candidate < (distances.get(edge.to) ?? Number.POSITIVE_INFINITY)) {
        distances.set(edge.to, candidate);
        previous.set(edge.to, { node: current, points: edge.points });
        pending.add(edge.to);
      }
    }
  }

  if (!previous.has(to)) return [];
  const segments: LatLng[][] = [];
  let current = to;
  while (current !== from) {
    const step = previous.get(current);
    if (!step) return [];
    segments.unshift(step.points);
    current = step.node;
  }
  return combineGeometry(...segments);
}

async function requestRoadGeometry(stops: Stop[]): Promise<LatLng[]> {
  if (stops.length < 2) return [];
  try {
  const coordinateChunks: Stop[][] = [];
  for (let start = 0; start < stops.length - 1; start += 94) {
    coordinateChunks.push(stops.slice(start, Math.min(start + 95, stops.length)));
  }
  const complete: LatLng[] = [];
  for (const chunk of coordinateChunks) {
    const coordinates = chunk.map((stop) => `${stop.longitude},${stop.latitude}`).join(";");
    const response = await fetch(`https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson&steps=false`);
    if (!response.ok) return [];
    const payload = await response.json() as { code?: string; routes?: Array<{ geometry?: { coordinates?: number[][] } }> };
    const segment = payload.code === "Ok" ? payload.routes?.[0]?.geometry?.coordinates : undefined;
    if (!segment?.length) return [];
    const points = segment.map(([longitude, latitude]) => [latitude, longitude] as LatLng);
    complete.push(...(complete.length ? points.slice(1) : points));
  }
  return complete;
  } catch {
    return [];
  }
}

export function getRouteGeometry(route: Route, stopsById: Map<string, Stop>, routes: Route[] = [route]): Promise<LatLng[]> {
  const itinerary = getMapItinerary(route, stopsById);
  const key = `${route.id}:${itinerary.map((stop) => `${stop.id}:${stop.latitude.toFixed(6)},${stop.longitude.toFixed(6)}`).join("|")}`;
  const cached = geometryCache.get(key);
  if (cached) return cached;

  const routeStops = route.stopIds
    .map((stopId) => stopsById.get(stopId))
    .filter((stop): stop is Stop => Boolean(stop));
  const saved = savedRouteGeometry(route);
  const savedMatchesStops = saved.length > 1 && routeStops.length > 1 &&
    Math.abs(saved[0][0] - routeStops[0].latitude) < 0.00003 &&
    Math.abs(saved[0][1] - routeStops[0].longitude) < 0.00003 &&
    Math.abs(saved[saved.length - 1][0] - routeStops[routeStops.length - 1].latitude) < 0.00003 &&
    Math.abs(saved[saved.length - 1][1] - routeStops[routeStops.length - 1].longitude) < 0.00003;

  const request = (async () => {
    if (itinerary.length < 2) return toLatLng(itinerary);

    if (savedMatchesStops) {
      if (routeStops[routeStops.length - 1]?.id === "S01") return saved;
      const college = itinerary[0];
      const startsAtCollege = routeStops[0].id === college.id;
      const endsAtCollege = routeStops[routeStops.length - 1].id === college.id;
      const outbound = startsAtCollege ? [] : getRoadConnection(college.id, routeStops[0].id, routes, stopsById);
      const inbound = endsAtCollege ? [] : getRoadConnection(routeStops[routeStops.length - 1].id, college.id, routes, stopsById);
      if ((!startsAtCollege && outbound.length < 2) || (!endsAtCollege && inbound.length < 2)) {
        return toLatLng(itinerary);
      }
      const loop = combineGeometry(outbound, saved, inbound);
      return loop.length > 1 ? loop : toLatLng(itinerary);
    }

    const routed = await requestRoadGeometry(itinerary);
    return routed.length > 1 ? routed : toLatLng(itinerary);
  })();
  geometryCache.set(key, request);
  return request;
}

export function useRoadRouteGeometries(routes: Route[], stops: Stop[]): Record<string, LatLng[]> {
  const [resolvedGeometries, setResolvedGeometries] = useState<Record<string, { version: string; points: LatLng[] }>>({});
  const routeKey = routes.map((route) => `${route.id}:${route.stopIds.join(",")}`).join(";");
  const stopKey = stops.map((stop) => `${stop.id}:${stop.latitude},${stop.longitude}`).join(";");
  const version = `${routeKey}|${stopKey}`;
  const fallbackGeometries = useMemo(() => {
    const stopsById = new Map(stops.map((stop) => [stop.id, stop]));
    return Object.fromEntries(routes.map((route) => [route.id, toLatLng(getMapItinerary(route, stopsById))]));
  }, [routes, stops]);

  useEffect(() => {
    let active = true;
    const stopsById = new Map(stops.map((stop) => [stop.id, stop]));

    let cursor = 0;
    async function worker() {
      while (active) {
        const index = cursor++;
        if (index >= routes.length) return;
        const route = routes[index];
        const points = await getRouteGeometry(route, stopsById, routes);
        if (active) setResolvedGeometries((current) => ({ ...current, [route.id]: { version, points } }));
      }
    }
    void Promise.all(Array.from({ length: Math.min(4, routes.length) }, () => worker()));
    return () => { active = false; };
  }, [routes, stops, routeKey, stopKey, version]);

  return Object.fromEntries(routes.map((route) => [
    route.id,
    resolvedGeometries[route.id]?.version === version
      ? resolvedGeometries[route.id].points
      : fallbackGeometries[route.id] ?? [],
  ]));
}

export function getRouteColor(routeId: string): string {
  let hash = 0;
  for (const character of routeId) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  const hue = (hash * 137.508) % 360;
  return `hsl(${hue.toFixed(1)} 72% 40%)`;
}

