# Architecture

This document summarizes the backend and dashboard architecture.

## Layers

1. **Network** — stops, routes, vehicles, trips (`data/network/campus.json`).
2. **Data / simulation state** — demand history, trip history, GPS, bus status.
3. **Prediction engine** — demand, ETA, and overload-risk forecasts.
4. **Optimizer** — greedy vehicle assignment scored against operational metrics.
5. **Simulation / evaluation** — plan validation and baseline comparison.

## Prediction engine data flow

```
raw inputs ──► features ──► demand forecaster ──┐
   │                            │                ├──► risk assessment ──► optimizer
   └────────────────────────► ETA estimator ────┘
```

The prediction engine estimates *what will happen*; the optimizer decides
*what to do about it*.

## Modules

- **`eta.py`** — EWMA over segment travel times; schedule fallback scaled by
  the scenario's travel-time multiplier; empirical 10th/90th percentile windows.
- **`demand.py`** — historical-mean baseline; optional EWMA recent-blend and
  scenario demand multiplier; percentile confidence bounds.
- **`risk.py`** — demand-to-capacity shortfall and crowding-risk classification.
- **`predictor.py`** — single entry point returning the unified output contract.
- **`explainer.py`** — optional Groq (GPT OSS 20B) natural-language explanation.
