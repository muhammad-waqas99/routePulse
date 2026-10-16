"""Optimizer: vehicle assignment + demand-driven dispatch.

- ``solve.optimize`` / ``fallback.fallback_plan``: timetable vehicle assignment
  (reassign trips off unavailable vehicles to the spare fleet).
- ``dispatcher.dispatch``: rolling-horizon demand-driven dispatch (greedy +
  local search over the road graph), consuming prediction-engine forecasts.
"""
from app.optimizer.dispatcher import dispatch
from app.optimizer.fallback import fallback_plan
from app.optimizer.solve import optimize

__all__ = ["optimize", "fallback_plan", "dispatch"]
