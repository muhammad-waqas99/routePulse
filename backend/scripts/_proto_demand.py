"""Throwaway prototype: demand generation volume vs validator capacity checks."""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.optimizer import fallback_plan, optimize              
from app.schemas.network import Network              
from app.schemas.scenario import DemandRecord, PassengerDemand, Scenario              
from app.validation.constraints import validate_plan              

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

net = Network.model_validate(json.loads((DATA / "network" / "campus.json").read_text(encoding="utf-8-sig")))
hist = [DemandRecord.model_validate(r) for r in json.loads((DATA / "demand_history.json").read_text(encoding="utf-8-sig"))]


def gen(scenario, start, horizon, capture, max_group, seed):
    rng = random.Random(seed)
    downs: dict[str, list[str]] = {}
    for r in net.routes:
        for i, o in enumerate(r.stop_ids):
            downs.setdefault(o, []).extend(r.stop_ids[i + 1:])
    out = []
    n = 0
    for rec in sorted(hist, key=lambda r: (r.stop_id, r.time_bucket_min)):
        if rec.day_type != "WEEKDAY":
            continue
        if not (start <= rec.time_bucket_min < start + horizon):
            continue
        if rec.stop_id not in downs:
            continue
        mult = scenario.demand_multipliers.get(rec.stop_id, 1.0)
        target = rec.passengers * capture * mult
        size = min(max_group, max(1, round(target * rng.uniform(0.8, 1.2))))
        dest = rng.choice(downs[rec.stop_id])
        arr = rec.time_bucket_min + rng.randint(0, 19)
        out.append(PassengerDemand(
            demand_id=f"D{n:04d}", origin_stop_id=rec.stop_id, destination_stop_id=dest,
            arrival_time_min=arr, passenger_count=size, max_wait_min=25, transfer_allowed=True,
        ))
        n += 1
    return out


for capture, maxg in [(0.10, 6), (0.15, 6), (0.15, 8), (0.20, 6), (0.30, 6)]:
    print("=== capture", capture, "max_group", maxg)
    for sid in ["normal", "demand_surge", "traffic_delay", "road_closure", "vehicle_failure"]:
        sc = Scenario.model_validate(json.loads((DATA / "scenarios" / f"{sid}.json").read_text(encoding="utf-8-sig")))
        dem = gen(sc, 415, 180, capture, maxg, 42)
        tot = sum(d.passenger_count for d in dem)
        base = fallback_plan(net, sc)
        opt = optimize(net, sc)
        rb = validate_plan(net, base, sc, demand=dem)
        ro = validate_plan(net, opt, sc, demand=dem)
        cb = sum(1 for v in rb["violations"] if v["code"] == "CAPACITY_EXCEEDED")
        co = sum(1 for v in ro["violations"] if v["code"] == "CAPACITY_EXCEEDED")
        print(f"  {sid}: groups={len(dem)} pax={tot} base_cap={cb} base_total={rb['hard_violation_count']} "
              f"opt_cap={co} opt_total={ro['hard_violation_count']}")
