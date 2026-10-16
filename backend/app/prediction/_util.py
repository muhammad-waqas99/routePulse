"""Small shared math helpers (dependency-free)."""
from __future__ import annotations


def percentile(sorted_values: list[float], p: float) -> float:
    """Return the p-th percentile (p in [0, 100]) using linear interpolation.

    Used for empirical confidence bounds on ETA and demand forecasts.
    """
    if not sorted_values:
        raise ValueError("percentile of empty sequence")
    vals = sorted(sorted_values)
    if p <= 0:
        return vals[0]
    if p >= 100:
        return vals[-1]
    k = (len(vals) - 1) * (p / 100.0)
    lo = int(k)
    hi = lo + 1 if lo + 1 < len(vals) else lo
    frac = k - lo
    return vals[lo] + frac * (vals[hi] - vals[lo])
