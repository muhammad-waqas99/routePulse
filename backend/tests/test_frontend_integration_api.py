"""Contracts consumed by the supplied React frontend."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import deps
from app.evaluation import store as evaluation_store
from app.main import create_app


NETWORK = {
    "stops": [
        {"stop_id": "S1", "name": "One", "lat": 1.0, "lon": 2.0},
        {"stop_id": "S2", "name": "Two", "lat": 1.1, "lon": 2.1},
    ],
    "routes": [{
        "route_id": "R1", "stop_ids": ["S1", "S2"],
        "segment_travel_min": [5], "segment_distance_km": [1.5],
        "allowed_vehicle_types": ["shuttle"], "min_headway_min": 5,
        "max_headway_min": 30,
    }],
    "vehicles": [{
        "vehicle_id": "V1", "capacity": 10, "vehicle_type": "shuttle",
        "available_from_min": 0, "available_until_min": 720,
        "initial_stop_id": "S1", "turnaround_min": 4,
    }],
    "trips": [{
        "trip_id": "T1", "route_id": "R1", "vehicle_id": "V1",
        "planned_departure_min": 60, "departure_window_start_min": 55,
        "departure_window_end_min": 65,
    }],
}
SCENARIO = {
    "scenario_id": "normal", "evaluation_horizon_min": 60,
    "demand_multipliers": {}, "travel_time_multipliers": {},
    "unavailable_vehicle_ids": [], "vehicle_delays_min": {},
}


def test_operations_overview_returns_configured_snapshot(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "network").mkdir()
    (tmp_path / "scenarios").mkdir()
    (tmp_path / "network" / "campus.json").write_text(json.dumps(NETWORK), encoding="utf-8")
    (tmp_path / "bus_status.json").write_text(json.dumps([{
        "bus_id": "V1", "current_stop_id": "S2", "capacity": 10,
        "available": True, "onboard": 0,
    }]), encoding="utf-8")
    monkeypatch.setattr(deps, "DATA_DIR", tmp_path)
    response = TestClient(create_app()).get("/api/v1/operations/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["dataSource"] == "synthetic snapshot"
    assert body["stops"][0]["latitude"] == 1.0
    assert body["vehicles"][0]["currentStopId"] == "S2"
    assert body["etas"] == []
    assert len(body["alerts"]) == 1
    assert body["alerts"][0]["title"] == "Passenger load checks unavailable"


def test_evaluation_history_endpoints_return_real_evaluation(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "network").mkdir()
    (tmp_path / "scenarios").mkdir()
    (tmp_path / "network" / "campus.json").write_text(json.dumps(NETWORK), encoding="utf-8")
    (tmp_path / "scenarios" / "normal.json").write_text(json.dumps(SCENARIO), encoding="utf-8")
    (tmp_path / "demand.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(deps, "DATA_DIR", tmp_path)
    evaluation_store.clear()
    client = TestClient(create_app())

    created = client.post("/api/v1/evaluate", json={"scenario_id": "normal"})
    assert created.status_code == 200
    evaluation_id = created.json()["evaluation_id"]
    assert evaluation_id
    assert created.json()["candidate"] is not None

    listed = client.get("/api/v1/evaluations")
    assert listed.status_code == 200
    assert [item["evaluation_id"] for item in listed.json()] == [evaluation_id]
    assert "events" not in listed.json()[0]["baseline"]

    repeated = client.post("/api/v1/evaluate", json={"scenario_id": "normal"})
    assert repeated.status_code == 200
    assert repeated.json()["evaluation_id"] != evaluation_id
    assert len(client.get("/api/v1/evaluations").json()) == 2

    fetched = client.get(f"/api/v1/evaluations/{evaluation_id}")
    assert fetched.status_code == 200
    assert fetched.json()["scenario_id"] == "normal"
    assert client.get("/api/v1/evaluations/unknown").status_code == 404
