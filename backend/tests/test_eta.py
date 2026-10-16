"""Tests for the ETA / travel-time estimator."""
from __future__ import annotations

import pytest

from app.prediction.eta import ETAEstimator
from app.schemas.scenario import Scenario, TripObservation


def _obs(seg: int, travel_sec: float) -> TripObservation:
    return TripObservation(
        route_id="R_TEST",
        segment_index=seg,
        from_stop_id=["S0", "S1"][seg],
        to_stop_id=["S1", "S2"][seg],
        travel_time_sec=travel_sec,
    )


def test_ewma_update() -> None:
    est = ETAEstimator(alpha=0.4)
    est.observe(_obs(0, 300.0))
    assert est.segment_estimates[("R_TEST", 0)] == pytest.approx(300.0)

    est.observe(_obs(0, 360.0))
    assert est.segment_estimates[("R_TEST", 0)] == pytest.approx(0.4 * 360 + 0.6 * 300)


def test_schedule_fallback(sample_route) -> None:
    est = ETAEstimator(alpha=0.4, dwell_min=0.5)
    etas = est.predict_etas(sample_route, 0, 100.0)

    assert [e.stop_id for e in etas] == ["S1", "S2"]
    assert etas[0].eta_min == pytest.approx(105.0)
    assert etas[1].eta_min == pytest.approx(109.5)
    assert all(e.method == "schedule" for e in etas)
    assert etas[0].lower_min is None and etas[0].upper_min is None


def test_scenario_travel_time_multiplier(sample_route) -> None:
    est = ETAEstimator(alpha=0.4, dwell_min=0.5)
    scenario = Scenario(scenario_id="s", travel_time_multipliers={"R_TEST": 1.3})
    etas = est.predict_etas(sample_route, 0, 100.0, scenario)

                              
    assert etas[0].eta_min == pytest.approx(106.5)
                                              
    assert etas[1].eta_min == pytest.approx(100 + 6.5 + 0.5 + 5.2)


def test_ewma_confidence_window(sample_route) -> None:
    est = ETAEstimator(alpha=0.4, dwell_min=0.5)
    for seg, scheduled_min in enumerate(sample_route.segment_travel_min):
        base = scheduled_min * 60.0
        for obs in [base, base * 1.1, base * 0.9, base * 1.05, base * 0.95]:
            est.observe(_obs(seg, obs))

    etas = est.predict_etas(sample_route, 0, 100.0)
    assert all(e.method == "ewma" for e in etas)
    for e in etas:
        assert e.lower_min <= e.eta_min <= e.upper_min
