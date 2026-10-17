from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
NETWORK = DATA / "network"
SEED = 42
DEMAND_COUNT = 900
TRIP_HISTORY_COUNT = 900
ROUTE_TIME_FACTOR = 1.6
RADIUS_KM = 10.0


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    term = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.atan2(math.sqrt(term), math.sqrt(1 - term))


def compass_sector(center: tuple[float, float], point: tuple[float, float]) -> str:
    lat1, lat2 = map(math.radians, (center[0], point[0]))
    dlon = math.radians(point[1] - center[1])
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    return ("N", "NE", "E", "SE", "S", "SW", "W", "NW")[int((bearing + 22.5) % 360 // 45)]


def main() -> None:
    rng = random.Random(SEED)
    osm = read_json(NETWORK / "osm_bus_stop_candidates.json")
    road_source = read_json(NETWORK / "osrm_routes_source.json")
    old_network = read_json(NETWORK / "campus.json")
    osm_by_id = {str(item["id"]): item for item in osm["elements"]}
    center = (33.7760948, -84.3988077)
    campus_snap = road_source["campus_snap"]
    campus = (float(campus_snap["latitude"]), float(campus_snap["longitude"]))
    route_sources = road_source["routes"]
    if set(route_sources) != {f"R{i:02d}" for i in range(1, 11)}:
        raise ValueError("OSRM source must contain R01 through R10")

    stop_id_by_osm: dict[str, str] = {}
    stops_by_id: dict[str, dict] = {
        "S01": {
            "stop_id": "S01",
            "name": "Georgia Tech Campus Terminal",
            "lat": campus[0],
            "lon": campus[1],
            "zone": "HUB",
        }
    }
    route_stop_ids: dict[str, list[str]] = {}
    max_snap = float(campus_snap["snap_distance_m"])

    for route_id in sorted(route_sources):
        source = route_sources[route_id]
        osm_ids = [str(value) for value in source["osm_stop_ids"]]
        if len(source["waypoints"]) != len(osm_ids) + 1:
            raise ValueError(f"Waypoint count mismatch for {route_id}")
        ids = []
        for index, osm_id in enumerate(osm_ids):
            if osm_id not in osm_by_id:
                raise ValueError(f"OSM stop {osm_id} is not in the saved source extract")
            point = osm_by_id[osm_id]
            waypoint = source["waypoints"][index]
            max_snap = max(max_snap, float(waypoint["snap_distance_m"]))
            if float(waypoint["snap_distance_m"]) > 75:
                raise ValueError(f"OSRM snapped OSM stop {osm_id} more than 75 m")
            if osm_id not in stop_id_by_osm:
                stop_id = f"S{len(stop_id_by_osm) + 2:02d}"
                stop_id_by_osm[osm_id] = stop_id
                location = waypoint["location"]
                original = (float(point["lat"]), float(point["lon"]))
                road = str(waypoint.get("road_name") or "").strip()
                tags = point.get("tags", {})
                name = str(tags.get("name") or osm.get("display_name_overrides", {}).get(osm_id) or "").strip()
                if not name:
                    name = f"{road} bus stop" if road else str(tags.get("ref") or tags.get("local_ref") or f"{compass_sector(center, original)} Atlanta bus stop")
                stops_by_id[stop_id] = {
                    "stop_id": stop_id,
                    "name": name,
                    "lat": float(location[1]),
                    "lon": float(location[0]),
                    "zone": compass_sector(center, original),
                }
            ids.append(stop_id_by_osm[osm_id])
        route_stop_ids[route_id] = ids + ["S01"]
        if len(source["legs"]) != len(route_stop_ids[route_id]) - 1:
            raise ValueError(f"OSRM leg count mismatch for {route_id}")

    if len(stops_by_id) != 40:
        raise ValueError(f"Expected 40 distinct stops, found {len(stops_by_id)}")
    if any(not -90 <= item["lat"] <= 90 or not -180 <= item["lon"] <= 180 for item in stops_by_id.values()):
        raise ValueError("A stop has invalid latitude or longitude")
    if max(distance_km(center, (item["lat"], item["lon"])) for item in stops_by_id.values()) > RADIUS_KM:
        raise ValueError("At least one stop is outside the 10 km operating radius")

    routes = []
    for route_id in sorted(route_sources):
        source = route_sources[route_id]
        routes.append({
            "route_id": route_id,
            "stop_ids": route_stop_ids[route_id],
            "segment_travel_min": [round(max(float(leg["duration_s"]) / 60 * ROUTE_TIME_FACTOR, 0.8), 1) for leg in source["legs"]],
            "segment_distance_km": [round(float(leg["distance_m"]) / 1000, 3) for leg in source["legs"]],
            "allowed_vehicle_types": ["shuttle"],
            "min_headway_min": 25,
            "max_headway_min": 40,
        })

    fleet_template = {item["vehicle_id"]: item for item in old_network["vehicles"]}
    vehicle_ids = sorted(fleet_template)
    if len(vehicle_ids) != 25:
        raise ValueError(f"Expected 25 existing vehicle IDs, found {len(vehicle_ids)}")
    teams: dict[str, list[str]] = {}
    cursor = 0
    for index, route_id in enumerate(sorted(route_sources)):
        team_size = 3 if index < 5 else 2
        teams[route_id] = vehicle_ids[cursor:cursor + team_size]
        cursor += team_size
    if cursor != len(vehicle_ids):
        raise ValueError("Vehicle teams do not cover the existing fleet")

    vehicles = []
    for route_id, ids in teams.items():
        for vehicle_id in ids:
            template = fleet_template[vehicle_id]
            vehicles.append({
                **template,
                "initial_stop_id": route_stop_ids[route_id][0],
                "available_from_min": 420,
                "available_until_min": 1200,
            })
    vehicles.sort(key=lambda item: item["vehicle_id"])

    trips = []
    trip_number = 1
    for route_index, route_id in enumerate(sorted(route_sources)):
        team = teams[route_id]
        for departure_index in range(20):
            departure = 420 + departure_index * 34 + route_index * 2
            trips.append({
                "trip_id": f"T{trip_number:04d}",
                "route_id": route_id,
                "vehicle_id": team[departure_index % len(team)],
                "planned_departure_min": departure,
                "departure_window_start_min": departure - 5,
                "departure_window_end_min": departure + 5,
            })
            trip_number += 1

    network = {
        "stops": list(stops_by_id.values()),
        "routes": routes,
        "vehicles": vehicles,
        "trips": trips,
    }
    demand_origins = [stop_id for stop_id in stops_by_id if stop_id != "S01"]
    demand_weights = []
    for stop_id in demand_origins:
        name = stops_by_id[stop_id]["name"].lower()
        weight = 1.0
        if any(term in name for term in ("university", "college", "campus", "hospital", "station", "center", "centre", "bus loop", "transit")):
            weight = 2.8
        elif any(term in name for term in ("ave", "street", "road", "dr", "blvd", "way")):
            weight = 1.5
        demand_weights.append(weight)

    demand = []
    demand_history = []
    for index in range(DEMAND_COUNT):
        origin = rng.choices(demand_origins, weights=demand_weights, k=1)[0]
        minute = rng.randint(420, 1140)
        peak = 1.6 if minute < 570 or 900 <= minute < 1080 else 1.0
        passengers = max(1, round(rng.randint(1, 6) * peak))
        demand.append({
            "demand_id": f"D{index + 1:05d}",
            "origin_stop_id": origin,
            "destination_stop_id": "S01",
            "arrival_time_min": minute,
            "passenger_count": passengers,
            "max_wait_min": 25,
            "transfer_allowed": False,
        })
        demand_history.append({
            "stop_id": origin,
            "day_type": "WEEKDAY" if rng.random() < 0.8 else "WEEKEND",
            "time_bucket_min": minute // 30 * 30,
            "passengers": passengers,
        })

    trip_history = []
    for index in range(TRIP_HISTORY_COUNT):
        route = routes[index % len(routes)]
        segment = (index // len(routes)) % len(route["segment_travel_min"])
        mean_seconds = route["segment_travel_min"][segment] * 60
        trip_history.append({
            "route_id": route["route_id"],
            "segment_index": segment,
            "from_stop_id": route["stop_ids"][segment],
            "to_stop_id": route["stop_ids"][segment + 1],
            "travel_time_sec": round(mean_seconds * rng.uniform(0.88, 1.2), 1),
        })

    gps = []
    for index, route_id in enumerate(sorted(route_sources)):
        route_source = route_sources[route_id]
        waypoint_index = min(index % (len(route_source["waypoints"]) - 1), len(route_source["legs"]) - 1)
        location = route_source["waypoints"][waypoint_index]["location"]
        gps.append({
            "vehicle_id": teams[route_id][0],
            "timestamp_min": 480 + index * 3,
            "lat": float(location[1]),
            "lon": float(location[0]),
            "route_id": route_id,
            "segment_index": waypoint_index,
        })

    bus_status = [{
        "bus_id": item["vehicle_id"],
        "current_stop_id": item["initial_stop_id"],
        "capacity": item["capacity"],
        "available": True,
        "onboard": 0,
    } for item in vehicles]

    scenarios = {
        "normal": {
            "scenario_id": "normal", "seed": SEED, "evaluation_horizon_min": 180,
            "demand_multipliers": {}, "travel_time_multipliers": {},
            "unavailable_vehicle_ids": [], "vehicle_delays_min": {},
        },
        "traffic_delay": {
            "scenario_id": "traffic_delay", "seed": SEED, "evaluation_horizon_min": 180,
            "demand_multipliers": {}, "travel_time_multipliers": {"R01": 1.35, "R02": 1.35, "R05": 1.35},
            "unavailable_vehicle_ids": [], "vehicle_delays_min": {},
        },
        "road_closure": {
            "scenario_id": "road_closure", "seed": SEED, "evaluation_horizon_min": 180,
            "demand_multipliers": {}, "travel_time_multipliers": {"R03": 1.5, "R09": 1.5},
            "unavailable_vehicle_ids": [], "vehicle_delays_min": {},
        },
        "demand_surge": {
            "scenario_id": "demand_surge", "seed": SEED, "evaluation_horizon_min": 180,
            "demand_multipliers": {"S14": 1.8, "S34": 1.8}, "travel_time_multipliers": {},
            "unavailable_vehicle_ids": [], "vehicle_delays_min": {},
        },
        "vehicle_failure": {
            "scenario_id": "vehicle_failure", "seed": SEED, "evaluation_horizon_min": 180,
            "demand_multipliers": {}, "travel_time_multipliers": {},
            "unavailable_vehicle_ids": ["BUS02"], "vehicle_delays_min": {},
        },
    }

    geometry = {route_id: route_sources[route_id]["geometry"] for route_id in sorted(route_sources)}
    snapped_stops = {stop_id: [item["lon"], item["lat"]] for stop_id, item in stops_by_id.items()}
    road_distances = {route_id: round(route_sources[route_id]["distance_m"] / 1000, 3) for route_id in sorted(route_sources)}
    metadata = {
        "institution": "Georgia Institute of Technology",
        "city": "Atlanta",
        "state": "Georgia",
        "country": "United States",
        "campus_latitude": center[0],
        "campus_longitude": center[1],
        "campus_center_source": "OpenStreetMap/Nominatim Georgia Tech campus relation 3341535",
        "campus_terminal_latitude": campus[0],
        "campus_terminal_longitude": campus[1],
        "operating_radius_km": RADIUS_KM,
        "random_seed": SEED,
        "counts": {"stops": len(stops_by_id), "routes": len(routes), "vehicles": len(vehicles), "trips": len(trips), "demand_groups": len(demand), "scenarios": len(scenarios)},
        "road_geometry_source": road_source["source"],
        "road_geometry_retrieved_utc": road_source["retrieved_utc"],
        "stop_source": osm["source"],
        "stop_source_retrieved_utc": osm["retrieved_utc"],
        "stop_source_license": osm["license"],
        "unnamed_stop_label_source": osm.get("display_name_override_source"),
        "operational_status_note": "Demand, travel history, GPS snapshots, timetables, and vehicle status are deterministic synthetic scenario fixtures based on this real OSM geography; they are not live service data.",
        "max_stop_snap_distance_m": round(max_snap, 1),
    }

    for route in routes:
        source = route_sources[route["route_id"]]
        if len(route["stop_ids"]) != 5 or len(source["geometry"]) < 2:
            raise ValueError(f"Route shape is incomplete for {route['route_id']}")
        if max(route["segment_travel_min"]) <= 0 or max(route["segment_distance_km"]) <= 0:
            raise ValueError(f"Route has a non-positive segment for {route['route_id']}")

    stop_ids = set(stops_by_id)
    route_ids = {item["route_id"] for item in routes}
    vehicle_id_set = {item["vehicle_id"] for item in vehicles}
    if len({item["trip_id"] for item in trips}) != len(trips) or len(vehicle_id_set) != len(vehicles) or len(stop_ids) != len(stops_by_id):
        raise ValueError("Duplicate network IDs found")
    if any(set(item["stop_ids"]) - stop_ids for item in routes):
        raise ValueError("A route references a missing stop")
    if any(item["route_id"] not in route_ids or item["vehicle_id"] not in vehicle_id_set for item in trips):
        raise ValueError("A trip references a missing route or vehicle")
    if any(item["origin_stop_id"] not in stop_ids or item["destination_stop_id"] not in stop_ids for item in demand):
        raise ValueError("A demand record references a missing stop")
    if any(set(item["unavailable_vehicle_ids"]) - vehicle_id_set or set(item["demand_multipliers"]) - stop_ids or set(item["travel_time_multipliers"]) - route_ids for item in scenarios.values()):
        raise ValueError("A scenario references a missing network entity")
    if any(item["initial_stop_id"] not in stop_ids for item in vehicles):
        raise ValueError("A vehicle references a missing initial stop")
    if any(item["stop_id"] not in stop_ids for item in demand_history):
        raise ValueError("Demand history references a missing stop")
    if any(item["route_id"] not in route_ids or item["from_stop_id"] not in stop_ids or item["to_stop_id"] not in stop_ids for item in trip_history):
        raise ValueError("Trip history references a missing network entity")
    if any(item["vehicle_id"] not in vehicle_id_set or item["route_id"] not in route_ids for item in gps):
        raise ValueError("A GPS fixture references a missing vehicle or route")
    for route in routes:
        source = route_sources[route["route_id"]]
        first = source["geometry"][0]
        last = source["geometry"][-1]
        if any(not -180 <= lon <= 180 or not -90 <= lat <= 90 for lon, lat in source["geometry"]):
            raise ValueError(f"Road geometry contains invalid coordinates for {route['route_id']}")
        first_stop = stops_by_id[route["stop_ids"][0]]
        last_stop = stops_by_id[route["stop_ids"][-1]]
        if distance_km((first_stop["lat"], first_stop["lon"]), (first[1], first[0])) > 0.1:
            raise ValueError(f"Road geometry does not begin at the first stop for {route['route_id']}")
        if distance_km((last_stop["lat"], last_stop["lon"]), (last[1], last[0])) > 0.1:
            raise ValueError(f"Road geometry does not end at the campus for {route['route_id']}")
    if len(network["stops"]) != 40 or len(routes) != 10 or len(vehicles) != 25 or len(trips) != 200 or len(demand) != 900 or len(scenarios) != 5:
        raise ValueError("Required RoutePulse entity counts changed")

    write_json(NETWORK / "campus.json", network)
    write_json(DATA / "demand.json", demand)
    write_json(DATA / "demand_history.json", demand_history)
    write_json(DATA / "trip_history.json", trip_history)
    write_json(DATA / "gps" / "gps_traces.json", gps)
    write_json(DATA / "bus_status.json", bus_status)
    for scenario_id, scenario in scenarios.items():
        write_json(DATA / "scenarios" / f"{scenario_id}.json", scenario)
    write_json(NETWORK / "snapped_stops.json", snapped_stops)
    write_json(NETWORK / "route_road_distances_km.json", road_distances)
    write_json(NETWORK / "route_geometry.geojson.json", geometry)
    write_json(ROOT / "frontend" / "src" / "data" / "routeGeometry.json", geometry)
    write_json(NETWORK / "geography_metadata.json", metadata)

    print(f"Rebuilt for {metadata['institution']} · {metadata['city']}, {metadata['country']}")
    print(f"Center: {center[0]}, {center[1]} · radius: {RADIUS_KM:g} km · max OSM-to-road snap: {max_snap:.1f} m")
    print(f"Stops {len(stops_by_id)} · routes {len(routes)} · vehicles {len(vehicles)} · trips {len(trips)} · OD groups {len(demand)} · scenarios {len(scenarios)}")
    print("Route road distances (km): " + ", ".join(f"{key}={value:.2f}" for key, value in road_distances.items()))


if __name__ == "__main__":
    main()
