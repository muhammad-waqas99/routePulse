"""Tests for the travel-time matrix."""
from __future__ import annotations

from app.optimizer.route_planner import build_travel_matrix
from app.schemas.network import Network, Route, Stop


def _network() -> Network:
    stops = [Stop(stop_id=f"S{i}", name=f"S{i}", lat=0.0, lon=0.0) for i in range(1, 5)]
    routes = [
        Route(
            route_id="R1",
            stop_ids=["S1", "S2", "S3", "S4"],
            segment_travel_min=[5.0, 4.0, 6.0],
            segment_distance_km=[1.0, 1.0, 1.0],
        )
    ]
    return Network(stops=stops, routes=routes, vehicles=[], trips=[])


def test_shortest_path() -> None:
    m = build_travel_matrix(_network())
    assert m[("S1", "S2")] == 5.0
    assert m[("S1", "S4")] == 15.0                 
    assert m[("S4", "S1")] == 15.0              


def test_self_reachable() -> None:
    m = build_travel_matrix(_network())
    assert m[("S2", "S2")] == 0.0
