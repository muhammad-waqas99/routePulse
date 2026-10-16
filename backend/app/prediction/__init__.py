"""Prediction engine (our team's part).

Sub-modules:
- features.py   feature engineering helpers
- eta.py        travel-time / ETA estimation (EWMA)
- demand.py     passenger demand forecasting (historical-mean baseline)
- risk.py       overload / crowding risk (demand vs capacity)
- predictor.py  unified entry point + output contract
- explainer.py  optional Groq LLM explanation layer (not in the core path)
"""
