"""Tests for the demand forecaster."""
from __future__ import annotations

import pytest

from app.prediction.demand import DemandForecaster
from app.schemas.scenario import DemandRecord, Scenario


def _records() -> list[DemandRecord]:
    return [
        DemandRecord(stop_id="A", day_type="WEEKDAY", time_bucket_min=480, passengers=c)
        for c in [10, 12, 8, 14, 6]
    ]


def test_historical_mean() -> None:
    f = DemandForecaster()
    f.fit(_records())
    fc = f.predict("A", 480)
    assert fc.predicted_passengers == pytest.approx(10.0)
    assert fc.method == "historical_mean"
    assert fc.sample_size == 5
    assert fc.demand_lower == pytest.approx(6.8)
    assert fc.demand_upper == pytest.approx(13.2)


def test_no_data() -> None:
    f = DemandForecaster()
    fc = f.predict("Z", 480)
    assert fc.predicted_passengers == 0.0
    assert fc.method == "no_data"
    assert fc.sample_size == 0


def test_scenario_multiplier() -> None:
    f = DemandForecaster()
    f.fit(_records())
    s = Scenario(scenario_id="spike", demand_multipliers={"A": 2.0})
    fc = f.predict("A", 480, scenario=s)
    assert fc.predicted_passengers == pytest.approx(20.0)
    assert fc.demand_lower == pytest.approx(13.6)
    assert fc.demand_upper == pytest.approx(26.4)


def test_recent_blend() -> None:
    f = DemandForecaster()
    f.fit(_records())
    fc = f.predict("A", 480, recent_demand=20.0, alpha=0.4)
                              
    assert fc.predicted_passengers == pytest.approx(14.0)
    assert fc.method == "historical_mean_adjusted"
