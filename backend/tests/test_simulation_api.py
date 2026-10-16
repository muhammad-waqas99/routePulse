"""API tests for the simulation-facing endpoints.

Uses FastAPI's TestClient against the real application factory, pointing the
data helpers at a temporary fixture directory.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.api import deps
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

    monkeypatch.setattr(deps, "DATA_DIR", tmp_path)
    return TestClient(create_app())


def test_all_routes_registered(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    for route, method in [
        ("/api/v1/network", "get"),
        ("/api/v1/scenarios", "get"),
        ("/api/v1/scenarios/{scenario_id}/run", "post"),
        ("/api/v1/optimize", "post"),
        ("/api/v1/evaluate", "post"),
        ("/api/v1/runs/{run_id}", "get"),
        ("/api/v1/validate", "post"),
    ]:
        assert route in paths
        assert method in paths[route]


def test_get_network(client: TestClient) -> None:
    response = client.get("/api/v1/network")
    assert response.status_code == 200
    body = response.json()
    assert len(body["stops"]) == 3
    assert len(body["routes"]) == 1


def test_list_scenarios(client: TestClient) -> None:
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    assert [s["scenario_id"] for s in response.json()] == ["normal"]


def test_run_scenario_baseline_and_optimized(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scenarios/normal/run",
        json={"include_optimized": True, "seed": 42, "demand": []},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "normal"
    assert body["baseline"]["metrics"]["total_demand"] == 0
    assert body["optimized"] is not None
    assert body["comparison"] is not None
    assert body["run_id"]


def test_run_scenario_with_real_demand(client: TestClient) -> None:
    demand = [
        {
            "demand_id": "D1",
            "origin_stop_id": "S1",
            "destination_stop_id": "S3",
            "arrival_time_min": 58,
            "passenger_count": 5,
        }
    ]
    response = client.post(
        "/api/v1/scenarios/normal/run",
        json={"include_optimized": False, "seed": 42, "demand": demand},
    )
    assert response.status_code == 200
    baseline = response.json()["baseline"]
    assert baseline["feasible"] is True
    assert baseline["metrics"]["served_passengers"] == 5
    assert baseline["passenger_outcomes"]["unserved"] == 0


def test_run_unknown_scenario_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/scenarios/missing/run", json={"demand": []})
    assert response.status_code == 404


def test_get_stored_run(client: TestClient) -> None:
    run = client.post(
        "/api/v1/scenarios/normal/run", json={"demand": []}
    ).json()
    run_id = run["run_id"]
    response = client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["run_id"] == run_id


def test_get_unknown_run_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/runs/nope").status_code == 404


def test_optimize_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/optimize", json={"scenario_id": "normal"})
    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["plan_type"] == "optimized"
    assert len(body["plan"]["assignments"]) == 1
    assert "feasible" in body


def test_optimize_unknown_scenario_returns_404(client: TestClient) -> None:
    assert client.post("/api/v1/optimize", json={"scenario_id": "x"}).status_code == 404


def test_evaluate_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/evaluate", json={"scenario_id": "normal", "demand": []}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["baseline"] is not None
    assert body["comparison"]["baseline"]["run_id"] == body["baseline"]["run_id"]
    assert "candidate_validation" in body["comparison"]
