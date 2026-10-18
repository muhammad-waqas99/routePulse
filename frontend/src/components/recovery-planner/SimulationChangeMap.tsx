import { Fragment, useEffect, useMemo, useState } from "react";
import { latLngBounds } from "leaflet";
import { CircleMarker, MapContainer, Pane, Polyline, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { OperationsData, Route, Stop } from "../../types/operations";
import type { OptimizationResult, OptimizationTrip } from "../../types/optimization";
import { networkMapConfig } from "../../config/networkMap";
import { getRouteColor, useRoadRouteGeometries } from "../../lib/mapRoutes";
import { routeLabel } from "../../lib/presentation";

interface Props {
  result: OptimizationResult;
  data: OperationsData | null;
  loading: boolean;
  error: string | null;
}

function FitToStops({ stops }: { stops: Stop[] }) {
  const map = useMap();
  const coordinatesKey = stops.map((stop) => `${stop.id}:${stop.latitude},${stop.longitude}`).join("|");

  useEffect(() => {
    if (!stops.length) return;
    const bounds = latLngBounds(stops.map((stop) => [stop.latitude, stop.longitude] as [number, number]));
    map.fitBounds(bounds, { padding: [36, 36], maxZoom: 14 });
  }, [map, coordinatesKey, stops]);

  return null;
}

function countsByRoute(trips: OptimizationTrip[]) {
  const counts = new Map<string, number>();
  for (const trip of trips) counts.set(trip.routeId, (counts.get(trip.routeId) ?? 0) + 1);
  return counts;
}

function RouteLayers({
  routes,
  stops,
  selectedRouteId,
  baselineCounts,
  optimizedCounts,
}: {
  routes: Route[];
  stops: Stop[];
  selectedRouteId: string;
  baselineCounts: Map<string, number>;
  optimizedCounts: Map<string, number>;
}) {
  const geometries = useRoadRouteGeometries(routes, stops);
  const activeRoutes = routes
    .filter((route) => (baselineCounts.get(route.id) ?? 0) > 0 || (optimizedCounts.get(route.id) ?? 0) > 0)
    .sort((left, right) => Number(left.id === selectedRouteId) - Number(right.id === selectedRouteId));

  return (
    <Pane name="comparison-routes" style={{ zIndex: 410 }}>
      {activeRoutes.map((route) => {
        const points = geometries[route.id] ?? [];
        if (points.length < 2) return null;
        const baselineCount = baselineCounts.get(route.id) ?? 0;
        const optimizedCount = optimizedCounts.get(route.id) ?? 0;
        const selected = selectedRouteId === route.id;
        // Keep the original layer visible for every baseline service. On an
        // unchanged route it sits beneath the optimized stroke as a muted
        // reference; on a changed route it remains independently visible.
        const drawBaseline = baselineCount > 0;
        const drawOptimized = optimizedCount > 0;
        const isDimmed = selectedRouteId !== "all" && !selected;
        const color = getRouteColor(route.id);

        return (
          <Fragment key={route.id}>
            {drawBaseline && <Polyline
              positions={points}
              pathOptions={{
                color: "#94a3b8",
                weight: selected ? 9 : 7,
                opacity: isDimmed ? 0.28 : 0.84,
                dashArray: "8 8",
                lineCap: "round",
                lineJoin: "round",
              }}
            >
              <Tooltip>{`${routeLabel(route)} · Baseline`}</Tooltip>
              <Popup><strong>{routeLabel(route)}</strong><br />Baseline · {baselineCount} services</Popup>
            </Polyline>}
            {drawOptimized && <Polyline
              positions={points}
              pathOptions={{
                color,
                weight: selected ? 6 : 4,
                opacity: isDimmed ? 0.3 : selectedRouteId === "all" ? 0.86 : 0.96,
                lineCap: "round",
                lineJoin: "round",
              }}
            >
              <Tooltip>{`${routeLabel(route)} · Optimized`}</Tooltip>
              <Popup>
                <strong>{routeLabel(route)}</strong><br />
                Optimized · {optimizedCount} services
                {baselineCount > 0 && <><br />Baseline · {baselineCount} services</>}
              </Popup>
            </Polyline>}
          </Fragment>
        );
      })}
    </Pane>
  );
}

export default function SimulationChangeMap({ result, data, loading, error }: Props) {
  const [routeSelection, setRouteSelection] = useState("all");
  const baselineCounts = useMemo(() => countsByRoute(result.originalTrips), [result.originalTrips]);
  const optimizedCounts = useMemo(() => countsByRoute(result.proposedTrips), [result.proposedTrips]);
  const activeRoutes = useMemo(() => data?.routes.filter((route) =>
    (baselineCounts.get(route.id) ?? 0) > 0 || (optimizedCounts.get(route.id) ?? 0) > 0,
  ) ?? [], [data?.routes, baselineCounts, optimizedCounts]);
  const selectedRouteId = routeSelection !== "all" && activeRoutes.some((route) => route.id === routeSelection)
    ? routeSelection
    : "all";
  const visibleStops = useMemo(() => {
    if (!data) return [];
    const selectedRoutes = selectedRouteId === "all"
      ? activeRoutes
      : activeRoutes.filter((route) => route.id === selectedRouteId);
    const routeStopIds = new Set(selectedRoutes.flatMap((route) => route.stopIds));
    return data.stops.filter((stop) => routeStopIds.has(stop.id) || (selectedRouteId === "all" && stop.id === "S01"));
  }, [activeRoutes, data, selectedRouteId]);

  if (loading) return <section className="rounded-xl border border-border bg-white p-5 text-sm text-secondary">Loading route comparison…</section>;
  if (error || !data || data.stops.length === 0) return <section className="rounded-xl border border-border bg-white p-5 text-sm text-secondary">Route map unavailable{error ? `: ${error}` : "."}</section>;

  return (
    <section className="min-w-0 space-y-3 rounded-xl border border-border bg-white p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-foreground">Route comparison</h3>
        <span className="rounded-full bg-primary-soft px-3 py-1.5 text-xs font-medium text-primary">{activeRoutes.length} routes · {visibleStops.length} stops</span>
      </div>

      <div
        className="flex min-w-0 max-w-full items-center gap-2"
        aria-label="Select route"
      >
        <button
          type="button"
          onClick={() => setRouteSelection("all")}
          aria-pressed={selectedRouteId === "all"}
          className={`min-h-10 shrink-0 rounded-lg border px-3 py-2 text-sm font-medium ${
            selectedRouteId === "all"
              ? "border-primary bg-primary text-white"
              : "border-border bg-white text-foreground"
          }`}
        >
          All routes
        </button>

        <div className="flex min-w-0 max-w-full flex-1 flex-nowrap items-center gap-2 overflow-x-auto overflow-y-hidden rounded-lg bg-surface-secondary p-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {activeRoutes.map((route) => {
            const selected = selectedRouteId === route.id;
            const color = getRouteColor(route.id);

            return (
              <button
                key={route.id}
                type="button"
                aria-pressed={selected}
                onClick={() => setRouteSelection(route.id)}
                className="min-h-10 shrink-0 whitespace-nowrap rounded-lg border px-3 py-2 text-sm font-medium"
                style={{
                  borderColor: color,
                  backgroundColor: selected ? color : "#fff",
                  color: selected ? "#fff" : color,
                }}
              >
                {routeLabel(route)}
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-2 rounded-lg bg-surface-secondary px-3 py-2 text-xs text-secondary" aria-label="Map legend">
        <span className="inline-flex items-center gap-2"><span className="w-7 border-t-[3px] border-dashed border-slate-400" />Baseline</span>
        <span className="inline-flex items-center gap-2"><span className="w-7 border-t-[3px] border-primary" />Optimized</span>
        <span className="inline-flex items-center gap-2"><span className="size-2.5 rounded-full border-2 border-white bg-slate-700 shadow-sm" />Stop</span>
      </div>

      <div className="h-72 overflow-hidden rounded-lg border border-border sm:h-80 lg:h-96">
        <MapContainer center={networkMapConfig.center} zoom={networkMapConfig.zoom} minZoom={networkMapConfig.minZoom} maxZoom={networkMapConfig.maxZoom} maxBounds={networkMapConfig.maxBounds} maxBoundsViscosity={1} scrollWheelZoom zoomSnap={0.5} className="h-full w-full">
          <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <FitToStops stops={visibleStops} />
          <RouteLayers routes={data.routes} stops={data.stops} selectedRouteId={selectedRouteId} baselineCounts={baselineCounts} optimizedCounts={optimizedCounts} />
          <Pane name="comparison-stops" style={{ zIndex: 500 }}>
            {visibleStops.map((stop) => {
              const servedRoutes = (selectedRouteId === "all"
                ? activeRoutes
                : activeRoutes.filter((route) => route.id === selectedRouteId)
              ).filter((route) => route.stopIds.includes(stop.id));
              const routeColor = servedRoutes.length === 1 ? getRouteColor(servedRoutes[0].id) : "#334155";
              return (
                <CircleMarker key={stop.id} center={[stop.latitude, stop.longitude]} radius={stop.id === "S01" ? 8 : 6} pathOptions={{ color: "#fff", weight: 2, fillColor: routeColor, fillOpacity: 1 }}>
                  <Tooltip direction="top">{stop.name}</Tooltip>
                  <Popup><strong>{stop.name}</strong><br />{servedRoutes.length ? servedRoutes.map(routeLabel).join(", ") : "No active route"}</Popup>
                </CircleMarker>
              );
            })}
          </Pane>
        </MapContainer>
      </div>
    </section>
  );
}
