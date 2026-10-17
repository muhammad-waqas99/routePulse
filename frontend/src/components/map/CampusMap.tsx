import { Fragment, useEffect, useMemo, useState } from "react";
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
import { getRouteColor, useRoadRouteGeometries } from "../../lib/mapRoutes";
import { getNextStopArrival } from "../../lib/arrivalEstimates";
import { humanizeIdentifier, routeLabel } from "../../lib/presentation";
import type { EtaRecord, Route, Stop, Trip, Vehicle } from "../../types/operations";

interface CampusMapProps {
  stops: Stop[];
  routes: Route[];
  vehicles: Vehicle[];
  trips: Trip[];
  etas: EtaRecord[];
  selectedStopId: string | null;
  onStopSelect: (stopId: string) => void;
}

interface RouteLinesProps {
  routes: Route[];
  stops: Stop[];
  selectedRouteId: string;
  onRouteSelect: (routeId: string) => void;
  focused: boolean;
}


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
  focused,
}: RouteLinesProps) {
  const visibleRoutes =
    selectedRouteId === "all"
      ? routes
      : routes.filter((route) => route.id === selectedRouteId);
  const geometries = useRoadRouteGeometries(routes, stops);

  return (
    <>
      {visibleRoutes.map((route) => {
        const positions = geometries[route.id] ?? [];

        if (positions.length < 2) return null;

        const color = getRouteColor(route.id);
        const displayPositions = positions;
        const opacity = focused && selectedRouteId !== route.id ? 0.12 : selectedRouteId === "all" ? 0.72 : 0.95;
        return <Fragment key={route.id}><Polyline positions={displayPositions} pathOptions={{ color: "#FFFFFF", weight: selectedRouteId === route.id ? 9 : 7, opacity: opacity * 0.85 }} eventHandlers={{ click: () => onRouteSelect(route.id) }} /><Polyline positions={displayPositions} pathOptions={{ color, weight: selectedRouteId === route.id ? 5 : 3.5, opacity }} eventHandlers={{ click: () => onRouteSelect(route.id) }} /></Fragment>;
      })}
    </>
  );
}

function FitMapToStops({ stops }: { stops: Stop[] }) {
  const map = useMap();

  useEffect(() => {
    if (stops.length === 0) return;

    const bounds = latLngBounds(stops.map((stop) => [stop.latitude, stop.longitude] as [number, number]));
    map.fitBounds(bounds, { padding: [36, 36], maxZoom: 14 });
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

    const bounds = latLngBounds(allStops.map((stop) => [stop.latitude, stop.longitude] as [number, number]));
    map.fitBounds(bounds, { padding: [36, 36], maxZoom: 14 });
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
  trips,
  etas,
  selectedStopId,
  onStopSelect,
}: CampusMapProps) {
  const [selectedRouteId, setSelectedRouteId] = useState("all");



  
  const visibleStops = useMemo(
    () =>
      selectedRouteId === "all"
        ? stops
        : stops.filter((stop) => stop.id === "S01" ||
            routes
              .find((route) => route.id === selectedRouteId)
              ?.stopIds.includes(stop.id),
          ),
    [stops, routes, selectedRouteId],
  );

  const visibleVehicles = vehicles.filter((vehicle) => {
    if ((vehicle.status !== "in-service" && vehicle.status !== "available") || !vehicle.currentStopId) {
      return false;
    }

    return (
      selectedRouteId === "all" || vehicle.routeId === selectedRouteId
    );
  });
  const arrivalsByStop = useMemo(
    () => new Map(stops.map((stop) => [stop.id, getNextStopArrival(stop.id, routes, trips, etas)])),
    [stops, routes, trips, etas],
  );

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start gap-2">
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

        <div className="flex max-h-28 min-w-0 flex-1 flex-wrap gap-2 overflow-y-auto rounded-lg bg-slate-50 p-2">
        {routes.map((route) => {
          const color = getRouteColor(route.id);
          const isSelected = selectedRouteId === route.id;

          return (
            <button
              key={route.id}
              type="button"
              title={routeLabel(route)}
              onClick={() => setSelectedRouteId(route.id)}
              className="rounded-lg border px-3 py-2 text-sm font-medium transition"
              style={{
                borderColor: color,
                backgroundColor: isSelected ? color : "#FFFFFF",
                color: isSelected ? "#FFFFFF" : color,
              }}
            >
              {routeLabel(route)}
            </button>
          );
        })}
        </div>

        <span className="ml-auto text-xs text-secondary">
          {routes.length} routes · {visibleStops.length} stops · {visibleVehicles.length} buses
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
          zoomSnap={0.5}
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
              focused={selectedRouteId !== "all"}
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

              const routeColor = getRouteColor(stopRoute?.id ?? stop.id);
              const nextArrival = arrivalsByStop.get(stop.id);

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
                        {isUniversityTerminal && (
                          <p>University Terminal — all routes end here</p>
                        )}
                        {stopRoute && <p>Route: {routeLabel(stopRoute)}</p>}
                        {nextArrival && <p>Next {nextArrival.estimatedArrival}{nextArrival.dayOffset ? ` (+${nextArrival.dayOffset} day)` : ""} · {nextArrival.source === "live" ? "Live" : "Scheduled"} · {routeLabel(routes.find((route) => route.id === nextArrival.routeId) ?? { id: nextArrival.routeId, name: nextArrival.routeId, stopIds: [], status: "active" })}</p>}
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
                    <p className="font-semibold">{humanizeIdentifier(vehicle.id)}</p>
                    <p>Planned route: {assignedRoute?.name ?? "No route"}</p>
                    <p>Current stop: {currentStop.name}</p>
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
