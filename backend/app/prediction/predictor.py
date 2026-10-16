"""Prediction engine entry point.

Combines demand forecasting, ETA estimation, and overload risk into the single
output contract consumed by the optimizer and API.

The separation of concerns (from `Wild Bugs.md`): the prediction engine
estimates *what will happen*; the optimizer decides *what to do about it*.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from app.prediction.demand import DemandForecaster
from app.prediction.eta import ETAEstimator, StopETA
from app.prediction.features import BUCKET_MINUTES, time_bucket
from app.prediction.risk import assess_risk
from app.schemas.network import Network
from app.schemas.scenario import GPSObservation, Scenario


@dataclass
class StopForecast:
    """Demand + risk forecast for a single stop over the horizon."""

    stop_id: str
    time_bucket_min: int
    horizon_minutes: int
    predicted_passengers: float
    demand_lower: float
    demand_upper: float
    available_capacity: int
    capacity_shortfall: float
    crowding_risk: str
    recommended_action: str
    method: str


@dataclass
class VehicleETA:
    """ETA forecast for a single vehicle along its route."""

    vehicle_id: str
    route_id: str
    current_segment_index: int
    etas: list[StopETA]


@dataclass
class PredictionOutput:
    """The unified prediction output contract."""

    model_version: str
    timestamp_min: int
    horizon_minutes: int
    day_type: str
    scenario_id: Optional[str]
    stop_forecasts: list[StopForecast]
    vehicle_etas: list[VehicleETA]

    def to_dict(self) -> dict:
        return asdict(self)


def serving_capacity_by_stop(
    network: Network,
    unavailable_vehicle_ids: Optional[list[str]] = None,
) -> dict[str, int]:
    """Estimate the capacity expected to serve each stop from the timetable.

    Sums the capacity of each vehicle assigned (via trips) to a route that
    serves the stop, counting each vehicle once per stop. The optimizer may
    later change these assignments; this is the baseline expectation.
    """
    unavailable = set(unavailable_vehicle_ids or [])
    cap: dict[str, int] = {s.stop_id: 0 for s in network.stops}
    seen: set[tuple[str, str]] = set()

    for trip in network.trips:
        if trip.vehicle_id in unavailable:
            continue
        route = network.routes_by_id.get(trip.route_id)
        vehicle = network.vehicles_by_id.get(trip.vehicle_id)
        if route is None or vehicle is None:
            continue
        for stop_id in route.stop_ids:
            key = (trip.vehicle_id, stop_id)
            if key not in seen:
                seen.add(key)
                cap[stop_id] = cap.get(stop_id, 0) + vehicle.capacity
    return cap


class PredictionEngine:
    """Facade over the demand, ETA, and risk models."""

    def __init__(
        self,
        network: Network,
        demand_forecaster: DemandForecaster,
        eta_estimator: ETAEstimator,
        model_version: str = "v1",
    ) -> None:
        self.network = network
        self.demand = demand_forecaster
        self.eta = eta_estimator
        self.model_version = model_version

    def predict(
        self,
        timestamp_min: int,
        gps_observations: list[GPSObservation],
        horizon_minutes: int = 15,
        scenario: Optional[Scenario] = None,
        day_type: str = "WEEKDAY",
        recent_demand_by_stop: Optional[dict[str, float]] = None,
        alpha: float = 0.0,
        available_capacity_by_stop: Optional[dict[str, int]] = None,
    ) -> PredictionOutput:
        """Run one prediction cycle.

        - Demand: summed over the ``horizon_minutes`` horizon in 5-minute buckets.
        - ETA: per vehicle, from its GPS observation.
        - Risk: predicted demand vs. expected serving capacity.
        """
        bucket = time_bucket(timestamp_min)
        n_buckets = max(1, horizon_minutes // BUCKET_MINUTES)
        buckets = [bucket + i * BUCKET_MINUTES for i in range(n_buckets)]

        unavailable = scenario.unavailable_vehicle_ids if scenario else None
        capacity_by_stop = available_capacity_by_stop or serving_capacity_by_stop(
            self.network, unavailable
        )

        stop_forecasts: list[StopForecast] = []
        for stop in self.network.stops:
            total = lower = upper = 0.0
            sample = 0
            method = "no_data"
            recent = (
                recent_demand_by_stop.get(stop.stop_id)
                if recent_demand_by_stop
                else None
            )
            for b in buckets:
                fc = self.demand.predict(
                    stop.stop_id,
                    b,
                    day_type=day_type,
                    horizon_minutes=horizon_minutes,
                    scenario=scenario,
                    recent_demand=recent,
                    alpha=alpha,
                )
                total += fc.predicted_passengers
                lower += fc.demand_lower
                upper += fc.demand_upper
                sample = max(sample, fc.sample_size)
                if fc.method != "no_data":
                    method = fc.method

            cap = capacity_by_stop.get(stop.stop_id, 0)
            risk = assess_risk(stop.stop_id, bucket, total, cap)
            stop_forecasts.append(
                StopForecast(
                    stop_id=stop.stop_id,
                    time_bucket_min=bucket,
                    horizon_minutes=horizon_minutes,
                    predicted_passengers=round(total, 2),
                    demand_lower=round(lower, 2),
                    demand_upper=round(upper, 2),
                    available_capacity=cap,
                    capacity_shortfall=risk.capacity_shortfall,
                    crowding_risk=risk.crowding_risk,
                    recommended_action=risk.recommended_action,
                    method=method,
                )
            )

        vehicle_etas: list[VehicleETA] = []
        for obs in gps_observations:
            route = self.network.routes_by_id.get(obs.route_id)
            if route is None:
                continue
            etas = self.eta.predict_etas(
                route, obs.segment_index, obs.timestamp_min, scenario
            )
            vehicle_etas.append(
                VehicleETA(
                    vehicle_id=obs.vehicle_id,
                    route_id=obs.route_id,
                    current_segment_index=obs.segment_index,
                    etas=etas,
                )
            )

        return PredictionOutput(
            model_version=self.model_version,
            timestamp_min=timestamp_min,
            horizon_minutes=horizon_minutes,
            day_type=day_type,
            scenario_id=scenario.scenario_id if scenario else None,
            stop_forecasts=stop_forecasts,
            vehicle_etas=vehicle_etas,
        )
