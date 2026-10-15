"""Scenario listing and validation tests."""

from __future__ import annotations


def test_scenarios_include_expected_set(client):
    response = client.get("/api/scenarios")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True

    ids = {scenario["id"] for scenario in body["data"]}
    assert {
        "normal_operations",
        "demand_spike",
        "vehicle_unavailable",
    } <= ids


def test_scenario_fields_match_frontend_contract(client):
    scenarios = client.get("/api/scenarios").json()["data"]
    for scenario in scenarios:
        assert set(scenario) >= {
            "id",
            "name",
            "category",
            "description",
            "type",
            "demandMultiplierPercent",
            "availableVehicles",
            "affectedPeriod",
            "evaluationHorizonMin",
        }


def test_optimize_with_unknown_scenario_returns_404(client):
    response = client.post("/api/optimize", json={"scenarioId": "does_not_exist"})
    assert response.status_code == 404

    body = response.json()
    assert body["success"] is False
    assert "does_not_exist" in body["message"]


def test_optimize_missing_scenario_id_is_422(client):
    response = client.post("/api/optimize", json={})
    assert response.status_code == 422

    body = response.json()
    assert body["success"] is False
    assert body["error"] == "validation_error"
