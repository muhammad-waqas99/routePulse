"""Operations overview + seed data integrity tests."""

from __future__ import annotations

from app.services.operations_service import referential_integrity_errors


def test_seed_network_is_referentially_consistent():
    assert referential_integrity_errors() == []


def test_overview_envelope_and_collections(client):
    response = client.get("/api/operations/overview")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Operations overview retrieved successfully"

    data = body["data"]
    for key in (
        "routes",
        "stops",
        "vehicles",
        "trips",
        "demand",
        "etas",
        "alerts",
    ):
        assert key in data
        assert isinstance(data[key], list)
        assert len(data[key]) > 0


def test_overview_entity_fields_match_frontend_contract(client):
    data = client.get("/api/operations/overview").json()["data"]

    route = data["routes"][0]
    assert set(route) >= {"id", "name", "stopIds", "status"}

    stop = data["stops"][0]
    assert set(stop) >= {"id", "name", "latitude", "longitude"}
    assert isinstance(stop["latitude"], (int, float))

    vehicle = data["vehicles"][0]
    assert set(vehicle) >= {"id", "capacity", "status"}

    trip = data["trips"][0]
    assert set(trip) >= {"id", "routeId", "vehicleId", "departureTime", "status"}

    demand = data["demand"][0]
    assert set(demand) >= {"stopId", "time", "passengerCount"}

    eta = data["etas"][0]
    assert set(eta) >= {
        "tripId",
        "stopId",
        "scheduledArrival",
        "estimatedArrival",
    }

    alert = data["alerts"][0]
    assert set(alert) >= {"id", "title", "description", "severity", "status"}


def test_overview_references_are_closed(client):
    data = client.get("/api/operations/overview").json()["data"]

    stop_ids = {s["id"] for s in data["stops"]}
    route_ids = {r["id"] for r in data["routes"]}
    vehicle_ids = {v["id"] for v in data["vehicles"]}
    trip_ids = {t["id"] for t in data["trips"]}

    for route in data["routes"]:
        assert set(route["stopIds"]) <= stop_ids

    for trip in data["trips"]:
        assert trip["routeId"] in route_ids
        assert trip["vehicleId"] in vehicle_ids

    for eta in data["etas"]:
        assert eta["tripId"] in trip_ids
        assert eta["stopId"] in stop_ids


def test_etas_are_predicted_per_trip(client):
    data = client.get("/api/operations/overview").json()["data"]
    # Every published trip must contribute ETA records.
    trip_ids = {trip["id"] for trip in data["trips"]}
    eta_trip_ids = {eta["tripId"] for eta in data["etas"]}
    assert trip_ids == eta_trip_ids
