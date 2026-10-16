"""Run the optimizer on the dummy network for each scenario and print the plan.

Usage (from the repo root):

    python backend/demo_optimize.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)

from app.optimizer.fallback import fallback_plan              
from app.optimizer.solve import optimize              
from app.schemas.network import Network              
from app.schemas.scenario import Scenario              


def load(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    net = Network.model_validate(load(os.path.join(DATA, "network", "campus.json")))

    for name in ["normal", "vehicle_failure", "traffic_delay"]:
        sc = Scenario.model_validate(load(os.path.join(DATA, "scenarios", f"{name}.json")))
        base = fallback_plan(net, sc)
        opt = optimize(net, sc)

        print(f"[{name}]")
        print(f"  baseline : {len(base.assignments)} assigned, "
              f"{len(base.unassigned_trip_ids)} unassigned")
        print(f"  optimized: {len(opt.assignments)} assigned, "
              f"{len(opt.unassigned_trip_ids)} unassigned, "
              f"{len(opt.extra_trips)} extra dispatch(es), status={opt.solver_status}")

        base_by = {a.trip_id: a.vehicle_id for a in base.assignments}
        opt_by = {a.trip_id: a.vehicle_id for a in opt.assignments}
        changed = [t for t in opt_by if base_by.get(t) != opt_by[t]]
        if changed:
            example = changed[0]
            print(f"  reassigned trips: {len(changed)} "
                  f"(e.g. {example}: {base_by.get(example)} -> {opt_by[example]})")
        print()


if __name__ == "__main__":
    main()
