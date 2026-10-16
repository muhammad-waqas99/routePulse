"""API tests for POST /api/v1/validate.

Uses FastAPI's TestClient against the real application factory, pointing the
validation router at a temporary fixture data directory.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.api import validation as validation_api
from app.main import create_app

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient              


NETWORK = {
    "stops": [
        {"stop_id": "S1", "name": "One", "lat": 0.0, "lon": 0.0},
        {"stop_id": "S2", "name": "Two", "lat": 0.0, "lon": 0.0},
        {"stop_id": "S3", "name": "Three", "lat": 0.0, "lon": 0.0},
    ],
    "routes": [
        {
            "route_id": "R1",
            "stop_ids": ["S1", "S2", "S3"],
            "segment_travel_min": [5.0, 5.0],
            "segment_distance_km": [1.0, 1.0],
            "allowed_vehicle_types": ["shuttle"],
            "min_headway_min": 5,
            "max_headway_min": 120,
        }
    ],
    "vehicles": [
        {
            "vehicle_id": "V1",
            "capacity": 30,
            "vehicle_type": "shuttle",
            "available_from_min": 0,
            "available_until_min": 720,
            "initial_stop_id": "S1",
            "turnaround_min": 4,
            "cost_per_km": 18.0,
        }
    ],
    "trips": [
        {
            "trip_id": "T1",
            "route_id": "R1",
            "vehicle_id": "V1",
            "planned_departure_min": 60,
            "departure_window_start_min": 55,
            "departure_window_end_min": 65,
        }
    ],
}

SCENARIO = {
    "scenario_id": "normal",
    "seed": 42,
    "evaluation_horizon_min": 180,
    "demand_multipliers": {},
    "travel_time_multipliers": {},
    "unavailable_vehicle_ids": [],
    "vehicle_delays_min": {},
}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    network_dir = tmp_path / "network"
    scenario_dir = tmp_path / "scenarios"
    network_dir.mkdir()
    scenario_dir.mkdir()
    (network_dir / "campus.json").write_text(json.dumps(NETWORK), encoding="utf-8")
    (scenario_dir / "normal.json").write_text(json.dumps(SCENARIO), encoding="utf-8")

    monkeypatch.setattr(validation_api, "DATA_DIR", tmp_path)
    return TestClient(create_app())


def _request(**overrides):
    body = {
        "scenario_id": "normal",
        "plan": {
            "plan_type": "baseline",
            "assignments": [
                {"trip_id": "T1", "route_id": "R1", "vehicle_id": "V1", "departure_min": 60}
            ],
        },
        "demand": [],
    }
    body.update(overrides)
    return body


def test_validate_route_is_in_openapi(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert "/api/v1/validate" in schema["paths"]
    assert "post" in schema["paths"]["/api/v1/validate"]


def test_valid_plan_returns_feasible_true(client: TestClient) -> None:
    response = client.post("/api/v1/validate", json=_request())
    assert response.status_code == 200
    body = response.json()
    assert body["feasible"] is True
    assert body["hard_violation_count"] == 0
    assert body["violations"] == []
    assert body["unverified_constraints"] == []


def test_infeasible_plan_returns_200_with_false(client: TestClient) -> None:
    body = _request()
    body["plan"]["assignments"][0]["vehicle_id"] = "VX"                   
    response = client.post("/api/v1/validate", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["feasible"] is False
    assert any(v["code"] == "UNKNOWN_VEHICLE" for v in payload["violations"])


def test_departure_window_violation_reported(client: TestClient) -> None:
    body = _request()
    body["plan"]["assignments"][0]["departure_min"] = 90
    response = client.post("/api/v1/validate", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["feasible"] is False
    violation = next(v for v in payload["violations"] if v["code"] == "DEPARTURE_WINDOW")
    assert violation["departure_min"] == 90
    assert violation["window_end_min"] == 65


def test_unknown_scenario_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/validate", json=_request(scenario_id="does_not_exist"))
    assert response.status_code == 404


def test_malformed_request_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/validate", json={"scenario_id": "normal"})
    assert response.status_code == 422


def test_capacity_unverified_without_demand(client: TestClient) -> None:
    body = _request()
    body.pop("demand")
    response = client.post("/api/v1/validate", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["feasible"] is False
    assert any(u["code"] == "CAPACITY_UNVERIFIED" for u in payload["unverified_constraints"])
