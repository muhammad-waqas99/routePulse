"""Integration test for the unified PredictionEngine."""
from __future__ import annotations

from app.prediction.demand import DemandForecaster
from app.prediction.eta import ETAEstimator
from app.prediction.predictor import PredictionEngine
from app.schemas.network import Network, Route, Stop, Trip, Vehicle
from app.schemas.scenario import DemandRecord, GPSObservation


def _network() -> Network:
    stops = [
        Stop(stop_id="S0", name="Hub", lat=0.0, lon=0.0, zone="HUB"),
        Stop(stop_id="S1", name="Academic", lat=1.0, lon=1.0, zone="ACADEMIC"),
        Stop(stop_id="S2", name="Residence", lat=2.0, lon=2.0, zone="RESIDENTIAL"),
    ]
    routes = [
        Route(
            route_id="R",
            stop_ids=["S0", "S1", "S2"],
            segment_travel_min=[5.0, 4.0],
            segment_distance_km=[1.0, 1.0],
        )
    ]
    vehicles = [Vehicle(vehicle_id="V1", capacity=30, initial_stop_id="S0")]
    trips = [
        Trip(
            trip_id="T1",
            route_id="R",
            vehicle_id="V1",
            planned_departure_min=420,
            departure_window_start_min=415,
            departure_window_end_min=430,
        )
    ]
    return Network(stops=stops, routes=routes, vehicles=vehicles, trips=trips)


def test_engine_predict() -> None:
    net = _network()
    demand = DemandForecaster()
    demand.fit(
        [
            DemandRecord(stop_id="S1", day_type="WEEKDAY", time_bucket_min=960, passengers=10),
            DemandRecord(stop_id="S1", day_type="WEEKDAY", time_bucket_min=960, passengers=10),
        ]
    )
    eta = ETAEstimator()
    engine = PredictionEngine(net, demand, eta)

    gps = [
        GPSObservation(
            vehicle_id="V1", timestamp_min=960, lat=0.0, lon=0.0,
            route_id="R", segment_index=0,
        )
    ]
    out = engine.predict(timestamp_min=960, gps_observations=gps, horizon_minutes=15)

    assert len(out.stop_forecasts) == 3
    assert len(out.vehicle_etas) == 1
    assert out.horizon_minutes == 15

    s1 = next(s for s in out.stop_forecasts if s.stop_id == "S1")
                                                                                           
    assert s1.predicted_passengers == 10.0
    assert s1.available_capacity == 30
    assert s1.crowding_risk == "LOW"

    v = out.vehicle_etas[0]
    assert v.vehicle_id == "V1"
    assert [e.stop_id for e in v.etas] == ["S1", "S2"]
