"""Travel-time / ETA estimation.

Uses an exponentially weighted moving average (EWMA) over observed segment
travel times:

    t_hat_i^(k) = alpha * t_i^obs + (1 - alpha) * t_hat_i^(k-1)

and sums remaining segment estimates to predict arrival times:

    ETA(next stop) = t_now + sum(remaining segment estimates) + dwell

When observations are sparse it falls back to scheduled segment times scaled by
the scenario's travel-time multiplier. Arrival windows come from empirical
10th/90th percentile residuals; no arbitrary window is reported for the
schedule-fallback method.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.prediction._util import percentile
from app.schemas.network import Route
from app.schemas.scenario import Scenario, TripObservation


@dataclass
class StopETA:
    """Predicted arrival at a single downstream stop."""

    stop_id: str
    eta_min: float
    lower_min: Optional[float] = None
    upper_min: Optional[float] = None
    method: str = "schedule"                       


class ETAEstimator:
    """EWMA-based segment travel-time estimator with schedule fallback."""

    def __init__(self, alpha: float = 0.4, dwell_min: float = 0.5):
        self.alpha = alpha
        self.dwell_min = dwell_min
                                                                   
        self._estimate: dict[tuple[str, int], float] = {}
                                                                          
        self._observations: dict[tuple[str, int], list[float]] = {}

                                                                          
                                      
                                                                          
    def observe(self, obs: TripObservation) -> None:
        """Ingest one observed segment travel time and update the EWMA."""
        key = (obs.route_id, obs.segment_index)
        self._observations.setdefault(key, []).append(obs.travel_time_sec)
        prev = self._estimate.get(key)
        if prev is None:
            self._estimate[key] = obs.travel_time_sec
        else:
            self._estimate[key] = (
                self.alpha * obs.travel_time_sec + (1.0 - self.alpha) * prev
            )

    @property
    def segment_estimates(self) -> dict[tuple[str, int], float]:
        """Read-only view of smoothed segment estimates (seconds)."""
        return dict(self._estimate)

                                                                          
                
                                                                          
    def _segment_time(
        self, route: Route, segment_index: int, scenario: Optional[Scenario]
    ) -> tuple[float, Optional[float], Optional[float], str]:
        """Return (mean_min, lower_min, upper_min, method) for one segment."""
        key = (route.route_id, segment_index)
        scheduled_min = route.segment_travel_min[segment_index]
        mult = 1.0
        if scenario is not None:
            mult = scenario.travel_time_multipliers.get(route.route_id, 1.0)

        obs = self._observations.get(key, [])
        if len(obs) >= 2:
            smoothed = self._estimate[key]
            est_min = smoothed / 60.0
            residuals = [o - smoothed for o in obs]           
            lower_min = est_min + percentile(residuals, 10) / 60.0
            upper_min = est_min + percentile(residuals, 90) / 60.0
            return est_min, lower_min, upper_min, "ewma"

                                                                           
        return scheduled_min * mult, None, None, "schedule"

    def predict_etas(
        self,
        route: Route,
        current_segment_index: int,
        time_now_min: float,
        scenario: Optional[Scenario] = None,
    ) -> list[StopETA]:
        """Predict ETA for every downstream stop from the current segment.

        ``current_segment_index`` is the segment the vehicle is currently on
        (0-indexed); the next stop is ``route.stop_ids[current_segment_index + 1]``.
        """
        etas: list[StopETA] = []
        n_stops = len(route.stop_ids)

        mean_elapsed = 0.0
        lower_elapsed = 0.0
        upper_elapsed = 0.0
        all_calibrated = True

        for seg in range(current_segment_index, n_stops - 1):
            mean, lo, hi, method = self._segment_time(route, seg, scenario)
            mean_elapsed += mean
            if lo is None or hi is None:
                all_calibrated = False
            lower_elapsed += lo if lo is not None else mean
            upper_elapsed += hi if hi is not None else mean

            stop_id = route.stop_ids[seg + 1]
            eta = time_now_min + mean_elapsed
            if all_calibrated:
                lo_eta = time_now_min + lower_elapsed
                hi_eta = time_now_min + upper_elapsed
            else:
                lo_eta = hi_eta = None

            etas.append(
                StopETA(
                    stop_id=stop_id,
                    eta_min=round(eta, 2),
                    lower_min=round(lo_eta, 2) if lo_eta is not None else None,
                    upper_min=round(hi_eta, 2) if hi_eta is not None else None,
                    method="ewma" if all_calibrated else "schedule",
                )
            )

                                                                  
            if seg < n_stops - 2:
                mean_elapsed += self.dwell_min
                lower_elapsed += self.dwell_min
                upper_elapsed += self.dwell_min

        return etas
