"""Optimizer + pipeline tests."""

from __future__ import annotations

import pytest

from app.optimizer.solve import InfeasibleError, build_optimized_plan
from app.services.operations_service import get_network_model
from app.services.scenario_service import get_scenario


def test_normal_optimization_succeeds_and_validates(client):
    response = client.post(
        "/api/optimize", json={"scenarioId": "normal_operations"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["status"] in {"optimal", "feasible"}
    assert body["hardViolationCount"] == 0
    assert body["validation"]["valid"] is True
    assert len(body["proposedTrips"]) > 0
    assert body["totalTrips"] == len(body["proposedTrips"])


def test_optimization_returns_full_evidence_bundle(client):
    body = client.post("/api/optimize", json={"scenarioId": "normal_operations"}).json()

    assert set(body) >= {
        "status",
        "originalTrips",
        "proposedTrips",
        "totalTrips",
        "constraints",
        "hardViolationCount",
        "metrics",
        "runId",
        "scenarioId",
        "scenarioName",
        "baselinePlan",
        "optimizedPlan",
        "validation",
        "simulation",
        "baselineMetrics",
        "optimizedMetrics",
        "differences",
        "warnings",
    }
    assert set(body["simulation"]) == {"baseline", "optimized"}
    assert body["scenarioId"] == "normal_operations"


def test_demand_spike_reduces_unserved_passengers(client):
    body = client.post("/api/optimize", json={"scenarioId": "demand_spike"}).json()

    baseline_unserved = body["baselineMetrics"]["unservedPassengers"]
    optimized_unserved = body["optimizedMetrics"]["unservedPassengers"]

    # The optimizer must not do worse than the fixed published timetable.
    assert optimized_unserved <= baseline_unserved
    # And on this scenario it should strictly improve.
    assert optimized_unserved < baseline_unserved


def test_metric_values_are_computed_not_constant(client):
    normal = client.post(
        "/api/optimize", json={"scenarioId": "normal_operations"}
    ).json()
    spike = client.post(
        "/api/optimize", json={"scenarioId": "demand_spike"}
    ).json()

    # Different scenarios must produce genuinely different computed output.
    assert (
        normal["optimizedMetrics"]["vehicleDistanceKm"]
        != spike["optimizedMetrics"]["vehicleDistanceKm"]
    )
    assert (
        normal["baselineMetrics"]["unservedPassengers"]
        != spike["baselineMetrics"]["unservedPassengers"]
    )


def test_infeasible_when_no_vehicles_available():
    network = get_network_model()
    scenario = get_scenario("normal_operations").model_copy(
        update={
            "unavailableVehicleIds": [
                "BUS01",
                "BUS02",
                "BUS03",
                "BUS04",
                "BUS05",
                "BUS06",
            ]
        }
    )

    with pytest.raises(InfeasibleError):
        build_optimized_plan(network, scenario)


def test_api_returns_structured_infeasible_response(client, monkeypatch):
    def _raise(*_args, **_kwargs):
        raise InfeasibleError("Synthetic infeasible case for testing.")

    monkeypatch.setattr(
        "app.services.pipeline_service.build_optimized_plan", _raise
    )

    response = client.post(
        "/api/optimize", json={"scenarioId": "normal_operations"}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "infeasible"
    assert body["hardViolationCount"] > 0
    assert body["validation"]["valid"] is False
    assert body["warnings"]
    assert body["message"]


def test_vehicle_unavailable_scenario_runs(client):
    body = client.post(
        "/api/optimize", json={"scenarioId": "vehicle_unavailable"}
    ).json()
    assert body["status"] in {"optimal", "feasible"}
    assert body["validation"]["valid"] is True
    # BUS02 is grounded in this scenario.
    assert "BUS02" not in body["optimizedPlan"]["vehiclesUsed"]
