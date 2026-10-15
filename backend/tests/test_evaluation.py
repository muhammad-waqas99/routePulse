"""Evaluation endpoints and frontend-contract tests."""

from __future__ import annotations

METRIC_KEYS = {
    "averageWaitingTime",
    "unservedPassengers",
    "missedConnections",
    "etaMae",
    "unservedRate",
    "capacityViolations",
    "vehicleDistance",
}


def test_startup_seeds_evaluation_runs(client):
    body = client.get("/api/evaluation").json()
    assert body["success"] is True

    runs = body["data"]["runs"]
    assert len(runs) >= 3
    assert {run["scenarioId"] for run in runs} >= {
        "normal_operations",
        "demand_spike",
        "vehicle_unavailable",
    }


def test_completed_run_has_full_metrics(client):
    runs = client.get("/api/evaluation").json()["data"]["runs"]
    completed = [run for run in runs if run["status"] == "completed"]
    assert completed

    run = completed[0]
    assert run["metrics"] is not None
    assert set(run["metrics"]) == METRIC_KEYS
    for metric in run["metrics"].values():
        assert set(metric) == {"baseline", "optimized", "unit", "lowerIsBetter"}
        assert isinstance(metric["baseline"], (int, float))

    assert run["passengerOutcome"] is not None
    assert run["fleetUtilization"]
    assert run["keyFinding"]


def test_evaluation_detail_matches_list(client):
    runs = client.get("/api/evaluation").json()["data"]["runs"]
    run_id = runs[0]["runId"]

    body = client.get(f"/api/evaluation/{run_id}").json()
    assert body["success"] is True
    assert body["data"]["runId"] == run_id


def test_optimize_then_fetch_run(client):
    optimize = client.post(
        "/api/optimize", json={"scenarioId": "demand_spike"}
    ).json()
    run_id = optimize["runId"]

    detail = client.get(f"/api/evaluation/{run_id}").json()["data"]
    assert detail["scenarioId"] == "demand_spike"
    assert detail["status"] == "completed"
    assert detail["metrics"]["unservedPassengers"]["optimized"] == (
        optimize["optimizedMetrics"]["unservedPassengers"]
    )


def test_unknown_run_returns_404(client):
    response = client.get("/api/evaluation/999999")
    assert response.status_code == 404
    assert response.json()["success"] is False


def test_optimize_response_matches_recovery_planner_contract(client):
    body = client.post(
        "/api/optimize", json={"scenarioId": "normal_operations"}
    ).json()

    assert set(body["metrics"]) == {
        "averageWaitingTimeMin",
        "unservedPassengers",
        "missedConnections",
        "vehicleDistanceKm",
    }

    trip = body["proposedTrips"][0]
    assert set(trip) >= {"tripId", "routeId", "vehicleId", "departureTime"}

    for constraint in body["constraints"]:
        assert set(constraint) >= {"id", "label", "passed"}
