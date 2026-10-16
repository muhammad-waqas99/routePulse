"""Road-graph travel-time matrix (shortest paths between stops).

Builds a stop-to-stop travel-time matrix from the shuttle route graph (stops
as nodes, segment travel times as edge weights). This approximates road-network
travel times; it is derived from the route geometry, not a surveyed road graph.
"""
from __future__ import annotations

import heapq

from app.schemas.network import Network


def _dijkstra(adj: dict[str, list[tuple[str, float]]], src: str) -> dict[str, float]:
    dist: dict[str, float] = {src: 0.0}
    pq: list[tuple[float, str]] = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def build_travel_matrix(network: Network, directed: bool = False) -> dict[tuple[str, str], float]:
    """Return {(origin_stop, dest_stop): travel_minutes} over the route graph."""
    adj: dict[str, list[tuple[str, float]]] = {}
    for route in network.routes:
        stops = route.stop_ids
        for i in range(len(stops) - 1):
            u, v = stops[i], stops[i + 1]
            w = float(route.segment_travel_min[i])
            adj.setdefault(u, []).append((v, w))
            if not directed:
                adj.setdefault(v, []).append((u, w))

    matrix: dict[tuple[str, str], float] = {}
    for src in adj:
        for dst, d in _dijkstra(adj, src).items():
            matrix[(src, dst)] = round(d, 2)
    return matrix
