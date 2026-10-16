"""Import ``routepulse_synthetic_data.json`` into the canonical RoutePulse schema.

The expanded synthetic dataset uses camelCase field names and a flat structure.
This script maps it into the snake_case Pydantic schema shared across the system
and writes the canonical files under ``data/``.

Run from the repo root:

    python backend/scripts/import_synthetic_data.py

Source: ``routepulse_synthetic_data.json`` (produced by
``generate_routepulse_data.py``). All values remain synthetic/illustrative.
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import defaultdict
from datetime import datetime

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(_ROOT, "backend"))

from app.schemas.network import Network, Route, Stop, Trip, Vehicle              
from app.schemas.scenario import (              
    BusStatus,
    DemandRecord,
    GPSObservation,
    Scenario,
    TripObservation,
)

DATA_DIR = os.path.join(_ROOT, "data")
SRC = os.path.join(_ROOT, "routepulse_synthetic_data.json")

                                                                   
GPS_SNAPSHOT_MIN = 8 * 60

                                                                          
                                                                          
                                                                          
BERRY_STOPS = [
    ("Krannert Center", "HUB"),
    ("Memorial Library", "ACADEMIC"),
    ("Evans Hall", "ACADEMIC"),
    ("McAllister Hall", "ACADEMIC"),
    ("Hermann Hall", "ACADEMIC"),
    ("Moon Building", "ACADEMIC"),
    ("Cook Building", "ACADEMIC"),
    ("Laughlin Hall", "ACADEMIC"),
    ("Blackstone Hall", "ACADEMIC"),
    ("Green Hall", "ACADEMIC"),
    ("Ford Dining Hall", "DINING"),
    ("Kilpatrick Commons", "DINING"),
    ("Ford Auditorium", "LANDMARK"),
    ("Frost Memorial Chapel", "LANDMARK"),
    ("Barnwell Chapel", "LANDMARK"),
    ("Morgan Hall", "RESIDENTIAL"),
    ("Thomas Berry Hall", "RESIDENTIAL"),
    ("Dana Hall", "RESIDENTIAL"),
    ("Centennial Hall", "RESIDENTIAL"),
    ("Lemley Hall", "RESIDENTIAL"),
    ("North Spires Hall", "RESIDENTIAL"),
    ("South Spires Hall", "RESIDENTIAL"),
    ("Cage Center", "ATHLETICS"),
    ("Richards Gymnasium", "ATHLETICS"),
    ("Valhalla Stadium", "ATHLETICS"),
    ("Clara Bowl", "ATHLETICS"),
    ("Mount Berry Square", "HUB"),
    ("Oak Hill Museum", "LANDMARK"),
    ("Admissions Welcome Center", "ENTRY"),
    ("Main Gate", "ENTRY"),
    ("West Gate", "ENTRY"),
    ("East Gate", "ENTRY"),
    ("Health & Wellness Center", "SERVICE"),
    ("Campus Safety Office", "SERVICE"),
    ("Student Mail Center", "SERVICE"),
    ("Science Annex", "ACADEMIC"),
    ("Fine Arts Building", "ACADEMIC"),
    ("Lecture Hall A", "ACADEMIC"),
    ("Lecture Hall B", "ACADEMIC"),
    ("Transit Hub", "HUB"),
]


def hhmm_to_min(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def iso_to_min(iso: str) -> int:
    dt = datetime.fromisoformat(iso)
    return dt.hour * 60 + dt.minute


def iso_to_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


def split_even(total: float, n: int, ndigits: int) -> list[float]:
    """Split `total` into `n` segments (last absorbs the rounding remainder)."""
    base = round(total / n, ndigits)
    out = [base] * n
    out[-1] = round(total - base * (n - 1), ndigits)
    return out


def main() -> None:
    with open(SRC, encoding="utf-8") as f:
        ds = json.load(f)

                                                        
    berry_rng = random.Random(42)
    stops = []
    for i, s in enumerate(ds["stops"]):
        name, zone = BERRY_STOPS[i]
        row, col = divmod(i, 8)
        lat = round(34.2890 + row * 0.0016 + berry_rng.uniform(-0.0003, 0.0003), 6)
        lon = round(-85.1860 + col * 0.0016 + berry_rng.uniform(-0.0003, 0.0003), 6)
        stops.append(Stop(stop_id=s["stopId"], name=name, lat=lat, lon=lon, zone=zone))

                                                                              
    routes: list[Route] = []
    for r in ds["routes"]:
        n_seg = len(r["stopIds"]) - 1
        seg_dur = split_even(float(r["estimatedDurationMin"]), n_seg, 1)
        seg_dist = split_even(float(r["distanceKm"]), n_seg, 2)
        routes.append(Route(
            route_id=r["routeId"],
            stop_ids=r["stopIds"],
            segment_travel_min=seg_dur,
            segment_distance_km=seg_dist,
            allowed_vehicle_types=["shuttle"],
            min_headway_min=r["minimumHeadwayMin"],
            max_headway_min=r["minimumHeadwayMin"] * 2,
        ))
    route_by_id = {r.route_id: r for r in routes}

                        
    vehicles: list[Vehicle] = []
    for v in ds["vehicles"]:
        route = route_by_id.get(v.get("assignedRouteId") or "")
        initial = route.stop_ids[0] if route and route.stop_ids else "S01"
        vehicles.append(Vehicle(
            vehicle_id=v["vehicleId"],
            capacity=v["capacity"],
            vehicle_type="shuttle",
            available_from_min=420,           
            available_until_min=1320,         
            initial_stop_id=initial,
            turnaround_min=v["turnaroundBufferMin"],
            cost_per_km=round(float(v["operatingCostPerKm"]), 2),
        ))

                                      
    trips: list[Trip] = []
    trip_route: dict[str, str] = {}
    for s in ds["schedules"]:
        dep = iso_to_min(s["departureTime"])
        trips.append(Trip(
            trip_id=s["tripId"],
            route_id=s["routeId"],
            vehicle_id=s["vehicleId"],
            planned_departure_min=dep,
            departure_window_start_min=max(0, dep - 5),
            departure_window_end_min=dep + 5,
        ))
        trip_route[s["tripId"]] = s["routeId"]

    network = Network(stops=stops, routes=routes, vehicles=vehicles, trips=trips)

                                                    
    demand_records: list[DemandRecord] = []
    for d in ds["demand"]:
        day = "WEEKEND" if d.get("weekday") in ("Saturday", "Sunday") else "WEEKDAY"
        demand_records.append(DemandRecord(
            stop_id=d["stopId"],
            day_type=day,
            time_bucket_min=hhmm_to_min(d["timeWindow"]),
            passengers=d["passengers"],
        ))

                                                                                   
    etas_by_trip: dict[str, list[dict]] = defaultdict(list)
    for e in ds["etas"]:
        etas_by_trip[e["tripId"]].append(e)

    trip_observations: list[TripObservation] = []
    for trip_id, es in etas_by_trip.items():
        es.sort(key=lambda x: x["scheduledArrival"])
        route = route_by_id.get(trip_route.get(trip_id, ""))
        if route is None:
            continue
        for i in range(len(es) - 1):
            a, b = es[i], es[i + 1]
            travel_sec = (
                iso_to_dt(b["groundTruthArrival"]) - iso_to_dt(a["groundTruthArrival"])
            ).total_seconds()
            if a["stopId"] not in route.stop_ids:
                continue
            seg = route.stop_ids.index(a["stopId"])
            trip_observations.append(TripObservation(
                route_id=route.route_id,
                segment_index=seg,
                from_stop_id=a["stopId"],
                to_stop_id=b["stopId"],
                travel_time_sec=round(travel_sec, 1),
            ))

                                                                      
    gps_by_vehicle: dict[str, list[dict]] = defaultdict(list)
    for g in ds["gpsTraces"]:
        gps_by_vehicle[g["vehicleId"]].append(g)

    gps_observations: list[GPSObservation] = []
    for vid, samples in gps_by_vehicle.items():
        samples.sort(key=lambda x: abs(iso_to_min(x["timestamp"]) - GPS_SNAPSHOT_MIN))
        s = samples[0]
        route_id = trip_route.get(s["tripId"], "")
        route = route_by_id.get(route_id)
        seg = 0
        if route and s.get("nearestStopId") in route.stop_ids:
            idx = route.stop_ids.index(s["nearestStopId"])
            seg = max(0, idx - 1)
        gps_observations.append(GPSObservation(
            vehicle_id=vid,
            timestamp_min=iso_to_min(s["timestamp"]),
            lat=s["latitude"],
            lon=s["longitude"],
            route_id=route_id,
            segment_index=seg,
        ))

                          
    bus_status: list[BusStatus] = []
    for v in ds["vehicles"]:
        route = route_by_id.get(v.get("assignedRouteId") or "")
        current = route.stop_ids[0] if route and route.stop_ids else "S01"
        bus_status.append(BusStatus(
            bus_id=v["vehicleId"],
            current_stop_id=current,
            capacity=v["capacity"],
            available=bool(v.get("available", True)),
            onboard=0,
        ))

                         
    scenario_name = {
        "SCN01": "normal",
        "SCN02": "traffic_delay",
        "SCN03": "road_closure",
        "SCN04": "demand_surge",
        "SCN05": "vehicle_failure",
    }
    scenarios: list[tuple[str, Scenario]] = []
    for sc in ds["scenarios"]:
        sid = scenario_name.get(sc["scenarioId"], sc["scenarioId"].lower())
        demand_mult: dict[str, float] = {}
        if sc.get("demandMultiplier", 1.0) != 1.0:
            for stop in sc.get("affectedStopIds", []):
                demand_mult[stop] = float(sc["demandMultiplier"])
        travel_mult: dict[str, float] = {}
        if sc.get("travelTimeMultiplier", 1.0) != 1.0:
            for r in sc.get("affectedRouteIds", []):
                travel_mult[r] = float(sc["travelTimeMultiplier"])
        scenarios.append((sid, Scenario(
            scenario_id=sid,
            seed=ds["metadata"].get("randomSeed", 42),
            evaluation_horizon_min=180,
            demand_multipliers=demand_mult,
            travel_time_multipliers=travel_mult,
            unavailable_vehicle_ids=list(sc.get("unavailableVehicleIds", [])),
        )))

                                     
    os.makedirs(os.path.join(DATA_DIR, "network"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "gps"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "scenarios"), exist_ok=True)

    def dump(path: str, payload) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    dump(os.path.join(DATA_DIR, "network", "campus.json"), network.model_dump(mode="json"))
    dump(os.path.join(DATA_DIR, "demand_history.json"),
         [r.model_dump(mode="json") for r in demand_records])
    dump(os.path.join(DATA_DIR, "trip_history.json"),
         [r.model_dump(mode="json") for r in trip_observations])
    dump(os.path.join(DATA_DIR, "gps", "gps_traces.json"),
         [g.model_dump(mode="json") for g in gps_observations])
    dump(os.path.join(DATA_DIR, "bus_status.json"),
         [b.model_dump(mode="json") for b in bus_status])
    for sid, sc in scenarios:
        dump(os.path.join(DATA_DIR, "scenarios", f"{sid}.json"), sc.model_dump(mode="json"))

    print(
        f"Imported -> stops={len(stops)} routes={len(routes)} vehicles={len(vehicles)} "
        f"trips={len(trips)} demand={len(demand_records)} trip_obs={len(trip_observations)} "
        f"gps_snapshot={len(gps_observations)} scenarios={len(scenarios)}"
    )


if __name__ == "__main__":
    main()
