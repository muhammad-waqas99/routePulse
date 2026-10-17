# Evaluation protocol

Fixed before any plan comparison. Evaluation uses raw event
logs and actual vehicle states — never invented or hardcoded improvements.

## Prediction-engine metrics

- **ETA MAE**: `MAE = (1/N) Σ |predicted - actual|` in minutes. Exclude
  arrivals without a valid prediction and report coverage separately.
- **Demand error**: MAE and WAPE per horizon and stop group.
- **Overload recall**: fraction of actual capacity shortfalls flagged in advance.

## End-to-end metrics (baseline vs optimized)

- Average passenger waiting time (report unserved passengers alongside it).
- Unserved passenger rate.
- Missed connections (count each transfer at most once).
- Fleet utilization.
- Operational cost (`c_km·D + c_h·T_active + c_s·N_shifts`).
- Feasibility: hard-violation count, % plans passing validation, % scenarios
  with a feasible plan.

## Fair comparison

- Freeze network, evaluation horizon, seed, demand rules, and objective weights.
- Run baseline and optimized under identical demand and disruption timelines.
- Report percentage improvement as `(B - O)/B × 100` for lower-is-better metrics;
  report absolute differences when `B = 0`.
