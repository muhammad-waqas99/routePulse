import { useEffect, useMemo, useState } from "react";
import { divIcon, latLngBounds } from "leaflet";
import {
  CircleMarker,
  MapContainer,
  Marker,
  Pane,
  Polyline,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import { Minus, Plus, RotateCcw } from "lucide-react";

import { networkMapConfig } from "../../config/networkMap";
import type { Route, Stop, Vehicle } from "../../types/operations";

interface CampusMapProps {
  stops: Stop[];
  routes: Route[];
  vehicles: Vehicle[];
  selectedStopId: string | null;
  onStopSelect: (stopId: string) => void;
}

interface RouteLinesProps {
  routes: Route[];
  stops: Stop[];
  selectedRouteId: string;
  onRouteSelect: (routeId: string) => void;
}

interface OsrmResponse {
  code: string;
  routes: {
    geometry: {
      coordinates: number[][];
    };
  }[];
}

const routeColors: Record<string, string> = {
  R1: "#2563EB",
  R2: "#16A34A",
  R3: "#D97706",
  R4: "#9333EA",
};


const busIcon = divIcon({
  className: "",
  html: `
    <div style="
      width: 38px;
      height: 38px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #0F172A;
      border: 2px solid white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.25);
    ">
      <svg
        width="23"
        height="23"
        viewBox="0 0 24 24"
        fill="none"
        stroke="white"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M8 6v6m8-6v6M4 12h16" />
        <rect x="4" y="3" width="16" height="15" rx="2" />
        <path d="M6 18v2m12-2v2M8 15h.01M16 15h.01" />
      </svg>
    </div>
  `,
  iconSize: [38, 38],
  iconAnchor: [19, 52],
  popupAnchor: [0, -50],
});

function RouteLines({
  routes,
  stops,
  selectedRouteId,
  onRouteSelect,
}: RouteLinesProps) {
  const [routeGeometries, setRouteGeometries] = useState<
    Record<string, [number, number][]>
  >({});

  useEffect(() => {
    let cancelled = false;

    async function loadRouteGeometries() {
      const results = await Promise.all(
        routes.map(async (route) => {
          const orderedStops = route.stopIds
            .map((stopId) => stops.find((stop) => stop.id === stopId))
            .filter((stop): stop is Stop => Boolean(stop));

          if (orderedStops.length < 2) {
            return [route.id, []] as const;
          }

          const coordinates = orderedStops
            .map((stop) => `${stop.longitude},${stop.latitude}`)
            .join(";");

          const url =
            `https://router.project-osrm.org/route/v1/driving/${coordinates}` +
            "?overview=full&geometries=geojson&steps=false";

          try {
            const response = await fetch(url);

            if (!response.ok) {
              throw new Error(`Routing request failed for ${route.id}`);
            }

            const data = (await response.json()) as OsrmResponse;

            if (data.code !== "Ok" || !data.routes[0]) {
              throw new Error(`No road route found for ${route.id}`);
            }

            const positions = data.routes[0].geometry.coordinates.map(
              ([longitude, latitude]) =>
                [latitude, longitude] as [number, number],
            );

            return [route.id, positions] as const;
          } catch (error) {
            console.error(
              `Could not load road geometry for ${route.id}:`,
              error,
            );

            return [route.id, []] as const;
          }
        }),
      );

      if (!cancelled) {
        setRouteGeometries(Object.fromEntries(results));
      }
    }

    void loadRouteGeometries();

    return () => {
      cancelled = true;
    };
  }, [routes, stops]);

  const visibleRoutes =
    selectedRouteId === "all"
      ? routes
      : routes.filter((route) => route.id === selectedRouteId);

  return (
    <>
      {visibleRoutes.map((route) => {
        const positions = routeGeometries[route.id];

        if (!positions || positions.length < 2) return null;

        return (
          <Polyline
            key={route.id}
            positions={positions}
            pathOptions={{
              color: routeColors[route.id] ?? "#64748B",
              weight: 4,
              opacity: 0.7,
            }}
            eventHandlers={{
              click: () => onRouteSelect(route.id),
            }}
          />
        );
      })}
    </>
  );
}

function FitMapToStops({ stops }: { stops: Stop[] }) {
  const map = useMap();

  useEffect(() => {
    if (stops.length === 0) return;

    const bounds = latLngBounds(
      stops.map(
        (stop) => [stop.latitude, stop.longitude] as [number, number],
      ),
    );

    map.fitBounds(bounds, {
      padding: [30, 30],
      maxZoom: 15,
    });
  }, [map, stops]);

  return null;
}

interface MapControlsProps {
  allStops: Stop[];
  onReset: () => void;
}

function MapControls({ allStops, onReset }: MapControlsProps) {
  const map = useMap();

  function resetMap() {
    onReset();

    if (allStops.length === 0) {
      map.setView(networkMapConfig.center, networkMapConfig.zoom);
      return;
    }

    const bounds = latLngBounds(
      allStops.map(
        (stop) => [stop.latitude, stop.longitude] as [number, number],
      ),
    );

    map.fitBounds(bounds, {
      padding: [30, 30],
      maxZoom: 15,
    });
  }

  return (
    <div className="absolute right-3 top-3 z-10 flex flex-col gap-1">
      <button
        type="button"
        onClick={() => map.zoomIn()}
        aria-label="Zoom in"
        className="rounded-lg border border-border bg-white p-2 text-foreground shadow-sm hover:bg-slate-50"
      >
        <Plus size={18} />
      </button>

      <button
        type="button"
        onClick={() => map.zoomOut()}
        aria-label="Zoom out"
        className="rounded-lg border border-border bg-white p-2 text-foreground shadow-sm hover:bg-slate-50"
      >
        <Minus size={18} />
      </button>

      <button
        type="button"
        onClick={resetMap}
        aria-label="Reset map"
        title="Show all stops"
        className="rounded-lg border border-border bg-white p-2 text-foreground shadow-sm hover:bg-slate-50"
      >
        <RotateCcw size={18} />
      </button>
    </div>
  );
}

export default function CampusMap({
  stops,
  routes,
  vehicles,
  selectedStopId,
  onStopSelect,
}: CampusMapProps) {
  const [selectedRouteId, setSelectedRouteId] = useState("all");



  
  const visibleStops = useMemo(
    () =>
      selectedRouteId === "all"
        ? stops
        : stops.filter((stop) =>
            routes
              .find((route) => route.id === selectedRouteId)
              ?.stopIds.includes(stop.id),
          ),
    [stops, routes, selectedRouteId],
  );

  const visibleVehicles = vehicles.filter((vehicle) => {
    if (vehicle.status !== "in-service" || !vehicle.currentStopId) {
      return false;
    }

    return (
      selectedRouteId === "all" || vehicle.routeId === selectedRouteId
    );
  });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setSelectedRouteId("all")}
          className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
            selectedRouteId === "all"
              ? "border-primary bg-primary text-white"
              : "border-border bg-white text-foreground hover:bg-slate-50"
          }`}
        >
          All
        </button>

        {routes.map((route) => {
          const color = routeColors[route.id] ?? "#64748B";
          const isSelected = selectedRouteId === route.id;

          return (
            <button
              key={route.id}
              type="button"
              title={route.name}
              onClick={() => setSelectedRouteId(route.id)}
              className="rounded-lg border px-3 py-2 text-sm font-medium transition"
              style={{
                borderColor: color,
                backgroundColor: isSelected ? color : "#FFFFFF",
                color: isSelected ? "#FFFFFF" : color,
              }}
            >
              {route.id}
            </button>
          );
        })}

        <span className="ml-auto text-xs text-secondary">
          {visibleStops.length} stops · {visibleVehicles.length} buses
        </span>
      </div>

      
<div className="relative isolate z-0 h-72 w-full overflow-hidden rounded-xl border border-border sm:h-80 lg:h-105">

        <MapContainer
          center={networkMapConfig.center}
          zoom={networkMapConfig.zoom}
          minZoom={networkMapConfig.minZoom}
          maxZoom={networkMapConfig.maxZoom}
          maxBounds={networkMapConfig.maxBounds}
          maxBoundsViscosity={1}
          scrollWheelZoom
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <FitMapToStops stops={visibleStops} />

   
          <Pane name="route-lines" style={{ zIndex: 410 }}>
            <RouteLines
              routes={routes}
              stops={stops}
              selectedRouteId={selectedRouteId}
              onRouteSelect={setSelectedRouteId}
            />
          </Pane>

          <MapControls
            allStops={stops}
            onReset={() => setSelectedRouteId("all")}
          />


          <Pane name="stops" style={{ zIndex: 500 }}>
            {visibleStops.map((stop) => {
              const isUniversityTerminal = stop.id === "S01";
              const isSelected = stop.id === selectedStopId;

              const stopRoute = routes.find(
                (r) => r.stopIds.includes(stop.id) && stop.id !== "S01",
              );

              const routeColor =
                routeColors[stopRoute?.id ?? ""] ?? "#64748B";

              return (
                <div key={stop.id}>
                
                  <CircleMarker
                    center={[stop.latitude, stop.longitude]}
                    radius={isSelected ? 13 : isUniversityTerminal ? 12 : 9}
                    interactive={false}
                    pathOptions={{
                      color: "#FFFFFF",
                      weight: isSelected ? 4 : 3,
                      fillColor: isSelected
                        ? "#0F172A"
                        : isUniversityTerminal
                          ? "#DC2626"
                          : routeColor,
                      fillOpacity: 1,
                    }}
                  />

             
                  <CircleMarker
                    center={[stop.latitude, stop.longitude]}
                    radius={18}
                    eventHandlers={{
                      click: () => onStopSelect(stop.id),
                    }}
                    pathOptions={{
                      stroke: false,
                      fillColor: "#000000",
                      fillOpacity: 0,
                    }}
                  >
                    <Tooltip direction="top" offset={[0, -12]}>
                      {stop.name}
                    </Tooltip>

                    <Popup>
                      <div>
                        <p className="font-semibold">{stop.name}</p>
                        <p>
                          {stop.latitude.toFixed(5)},{" "}
                          {stop.longitude.toFixed(5)}
                        </p>
                        {isUniversityTerminal && (
                          <p>University Terminal — all routes end here</p>
                        )}
                        {stopRoute && <p>Route: {stopRoute.name}</p>}
                      </div>
                    </Popup>
                  </CircleMarker>
                </div>
              );
            })}
          </Pane>

          {visibleVehicles.map((vehicle) => {
            const currentStop = stops.find(
              (stop) => stop.id === vehicle.currentStopId,
            );

            const assignedRoute = routes.find(
              (route) => route.id === vehicle.routeId,
            );

            if (!currentStop) return null;

            return (
              <Marker
                key={vehicle.id}
                position={[currentStop.latitude, currentStop.longitude]}
                icon={busIcon}
                zIndexOffset={1000}
              >
                <Popup>
                  <div>
                    <p className="font-semibold">{vehicle.id}</p>
                    <p>Route: {assignedRoute?.name ?? "Unassigned"}</p>
                    <p>Current stop: {currentStop.name}</p>
                    <p>Destination: IIMB Main Gate</p>
                    <p>Capacity: {vehicle.capacity} passengers</p>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
