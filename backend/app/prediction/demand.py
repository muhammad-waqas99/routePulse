"""Passenger demand forecasting.

Deterministic, explainable baseline:

    D_hat_{s,h} = mean(D_{s,h}^{historical})

Optionally blends a recent observation via exponential smoothing and applies a
scenario demand multiplier. The historical-mean baseline is always available
for comparison across runs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.prediction._util import percentile
from app.schemas.scenario import DemandRecord, Scenario


@dataclass
class DemandForecast:
    """Forecast of passenger demand for one stop and time bucket."""

    stop_id: str
    day_type: str
    time_bucket_min: int
    horizon_minutes: int
    predicted_passengers: float
    demand_lower: float
    demand_upper: float
    sample_size: int
    method: str                                                              


class DemandForecaster:
    """Historical-mean demand baseline with optional recent-demand blending."""

    def __init__(self) -> None:
        self._history: dict[tuple[str, str, int], list[int]] = {}

                                                                          
    def fit(self, records: list[DemandRecord]) -> None:
        """Train on historical demand observations."""
        for r in records:
            key = (r.stop_id, r.day_type, r.time_bucket_min)
            self._history.setdefault(key, []).append(r.passengers)

    def _historical_stats(self, key: tuple[str, str, int]) -> tuple[float, float, float, int]:
        counts = self._history.get(key, [])
        n = len(counts)
        if n == 0:
            return 0.0, 0.0, 0.0, 0
        mean = sum(counts) / n
        lower = percentile(counts, 10)
        upper = percentile(counts, 90)
        return mean, lower, upper, n

                                                                          
    def predict(
        self,
        stop_id: str,
        time_bucket_min: int,
        day_type: str = "WEEKDAY",
        horizon_minutes: int = 15,
        scenario: Optional[Scenario] = None,
        recent_demand: Optional[float] = None,
        alpha: float = 0.0,
    ) -> DemandForecast:
        """Forecast demand for a stop/time bucket.

        ``alpha`` blends ``recent_demand`` with the historical mean (0.0 by
        default = pure historical baseline). ``scenario`` applies its demand
        multiplier for the stop (e.g. an event spike).
        """
        key = (stop_id, day_type, time_bucket_min)
        historical, lower, upper, n = self._historical_stats(key)

        expected = historical
        method = "historical_mean" if n > 0 else "no_data"
        if recent_demand is not None and alpha > 0:
            expected = alpha * recent_demand + (1.0 - alpha) * historical
            if n > 0:
                method = "historical_mean_adjusted"

        mult = 1.0
        if scenario is not None:
            mult = scenario.demand_multipliers.get(stop_id, 1.0)

        return DemandForecast(
            stop_id=stop_id,
            day_type=day_type,
            time_bucket_min=time_bucket_min,
            horizon_minutes=horizon_minutes,
            predicted_passengers=round(expected * mult, 2),
            demand_lower=round(lower * mult, 2),
            demand_upper=round(upper * mult, 2),
            sample_size=n,
            method=method,
        )
