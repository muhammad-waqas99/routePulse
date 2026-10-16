"""End-to-end run: passengers arrive -> prediction forecasts -> dispatch -> simulate.

Usage (from the repo root):

    python backend/demo_end_to_end.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)

from app.optimizer.dispatcher import DispatchPlan, dispatch              
from app.optimizer.route_planner import build_travel_matrix              
from app.optimizer.state import StopForecast              
from app.prediction.demand import DemandForecaster              
from app.prediction.eta import ETAEstimator              
from app.prediction.predictor import PredictionEngine              
from app.schemas.network import Network              
from app.schemas.scenario import DemandRecord, Scenario, TripObservation              
from app.simulation.engine import Simulator              

RISK_SCORE = {"LOW": 0.0, "MEDIUM": 1.0, "HIGH": 2.0}


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def arrivals_from_history(records: list[DemandRecord], start_min: int, horizon_min: int):
    arrivals: dict[str, list[float]] = {}
    for r in records:
        if r.day_type != "WEEKDAY":
            continue
        if start_min <= r.time_bucket_min < start_min + horizon_min:
                                                                               
            arrivals.setdefault(r.stop_id, []).extend(
                [float(r.time_bucket_min - start_min)] * r.passengers
            )
    return arrivals


def make_dispatch_fn(engine: PredictionEngine, scenario: Scenario, day_type: str, start_offset: int):
    def dispatch_fn(state, relative_min: int):
        output = engine.predict(
            timestamp_min=start_offset + relative_min,
            gps_observations=[],
            horizon_minutes=15,
            scenario=scenario,
            day_type=day_type,
        )
        forecasts = {
            f.stop_id: StopForecast(
                stop_id=f.stop_id,
                demand=f.predicted_passengers,
                shortfall=f.capacity_shortfall,
                risk=RISK_SCORE.get(f.crowding_risk, 0.0),
            )
            for f in output.stop_forecasts
        }
        return dispatch(state, forecasts)
    return dispatch_fn


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    net = Network.model_validate(load_json(os.path.join(DATA, "network", "campus.json")))
    demand_records = [
        DemandRecord.model_validate(r)
        for r in load_json(os.path.join(DATA, "demand_history.json"))
    ]
    trip_records = [
        TripObservation.model_validate(r)
        for r in load_json(os.path.join(DATA, "trip_history.json"))
    ]
    scenario = Scenario.model_validate(
        load_json(os.path.join(DATA, "scenarios", "demand_surge.json"))
    )

    demand = DemandForecaster()
    demand.fit(demand_records)
    eta = ETAEstimator(alpha=0.4)
    for t in trip_records:
        eta.observe(t)
    engine = PredictionEngine(net, demand, eta)

    travel_matrix = build_travel_matrix(net)
    sim = Simulator(net, travel_matrix)

    START = 8 * 60         
    HORIZON = 45
    arrivals = arrivals_from_history(demand_records, START, HORIZON)
    total_arrivals = sum(len(v) for v in arrivals.values())
    sim.inject(arrivals)

    result = sim.run(HORIZON, 5, make_dispatch_fn(engine, scenario, "WEEKDAY", START))

                                                                  
    def no_dispatch(state, relative_min):
        return DispatchPlan(simulation_time=relative_min, actions=[], objective_score=0.0)

    base_sim = Simulator(net, travel_matrix)
    base_sim.inject(arrivals)
    base_result = base_sim.run(HORIZON, 5, no_dispatch)

    print(f"Scenario: {scenario.scenario_id} | start 08:00 | horizon {HORIZON} min")
    print(f"Passengers arrived: {total_arrivals}")
    print(f"Boarded: {result.boarded} | Unserved: {result.unserved} | Avg wait: {result.avg_wait_min} min")
    print(f"Dispatch actions: {len(result.actions)}")
    for t, bus, stop, reason in result.actions[:12]:
        name = net.stops_by_id[stop].name if stop in net.stops_by_id else stop
        print(f"  t={t:>3}  {bus} -> {stop} ({name})  [{reason}]")

    print(f"\nBaseline (no dispatch): boarded {base_result.boarded} | unserved {base_result.unserved}")
    print(f"Optimized (dispatch):   boarded {result.boarded} | unserved {result.unserved} "
          f"| avg wait {result.avg_wait_min} min")


if __name__ == "__main__":
    main()
