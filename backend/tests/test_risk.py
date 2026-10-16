"""Tests for the overload / crowding risk model."""
from __future__ import annotations

from app.prediction.risk import assess_risk, capacity_shortfall, crowding_risk


def test_capacity_shortfall() -> None:
    assert capacity_shortfall(42, 30) == 12
    assert capacity_shortfall(20, 30) == 0
    assert capacity_shortfall(30, 30) == 0


def test_crowding_risk() -> None:
    assert crowding_risk(42, 30) == "HIGH"              
    assert crowding_risk(28, 30) == "MEDIUM"                       
    assert crowding_risk(10, 30) == "LOW"
    assert crowding_risk(0, 0) == "LOW"
    assert crowding_risk(5, 0) == "HIGH"


def test_assess_risk() -> None:
    r = assess_risk("A", 480, 42, 30)
    assert r.capacity_shortfall == 12
    assert r.crowding_risk == "HIGH"
    assert r.recommended_action == "EVALUATE_EXTRA_BUS"

    r2 = assess_risk("B", 480, 10, 30)
    assert r2.crowding_risk == "LOW"
    assert r2.recommended_action == "NO_ACTION"
