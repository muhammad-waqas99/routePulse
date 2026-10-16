"""Tests for the minimal time-stepped simulator."""
from __future__ import annotations

from app.optimizer.dispatcher import dispatch
from app.optimizer.route_planner import build_travel_matrix
from app.optimizer.state import StopForecast
from app.schemas.network import Network, Route, Stop, Vehicle
from app.simulation.engine import Simulator


def _network() -> Network:
    stops = [Stop(stop_id=f"S{i}", name=f"S{i}", lat=0.0, lon=0.0) for i in range(1, 4)]
    routes = [
        Route(
            route_id="R1",
            stop_ids=["S1", "S2", "S3"],
            segment_travel_min=[5.0, 5.0],
            segment_distance_km=[1.0, 1.0],
        )
    ]
    vehicles = [Vehicle(vehicle_id="B1", capacity=30, initial_stop_id="S1")]
    return Network(stops=stops, routes=routes, vehicles=vehicles, trips=[])


def _dispatch_fn():
    def fn(state, time_min):
        forecasts = {
            "S1": StopForecast("S1", demand=0, shortfall=0, risk=0.0),
            "S2": StopForecast("S2", demand=10, shortfall=10, risk=2.0),
            "S3": StopForecast("S3", demand=0, shortfall=0, risk=0.0),
        }
        return dispatch(state, forecasts)
    return fn


def test_simulator_boards_passengers() -> None:
    net = _network()
    matrix = build_travel_matrix(net)
    sim = Simulator(net, matrix)
    sim.inject({"S2": [0.0, 0.0, 0.0, 0.0, 0.0]})                              

    result = sim.run(horizon_min=10, step_min=5, dispatch_fn=_dispatch_fn())

    assert result.boarded == 5
    assert result.unserved == 0
    assert result.avg_wait_min >= 0
    assert len(result.actions) >= 1
