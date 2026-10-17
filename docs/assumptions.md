# Assumptions

Explicit assumptions behind the current implementation. Change these here if
they become wrong, and update the affected code.

- **Geographic data.** Georgia Tech campus and transit-stop locations are based
  on OpenStreetMap. Road geometry and distances come from OSRM driving routes.
  OpenStreetMap data is available under ODbL 1.0 and must retain attribution.
- **Simulated data.** Demand, schedules, travel-time history, GPS snapshots, and
  bus status are deterministic scenario fixtures (seed 42), not live service
  data or measured campus operations.
- **Time unit.** Simulation time is integer minutes from midnight. Demand and
  ETA forecasts use 5-minute buckets.
- **Service window.** Vehicles are modelled from 07:00 (420) to 20:00 (1200).
- **Demand baseline.** `D_hat = mean(historical)` per (stop, day type, bucket).
  EWMA recent-blend is optional (default `alpha=0.0`).
- **ETA smoothing.** `alpha = 0.4` for segment EWMA; tuned later on validation
  data, never the held-out test set.
- **ETA dwell.** A fixed 0.5-minute dwell per intermediate stop (a placeholder
  for a real boarding-time model).
- **Confidence intervals.** Empirical 10th/90th percentile residuals. No
  arbitrary fixed windows are reported for the schedule fallback.
- **Capacity.** The optimizer estimates peak trip loads from configured demand.
  The independent validator checks passenger loads by route segment when
  demand is available.
- **LLM usage.** Groq (GPT OSS 20B) is only for explanations; it is optional,
  lazy, cached, and never computes the numbers.
