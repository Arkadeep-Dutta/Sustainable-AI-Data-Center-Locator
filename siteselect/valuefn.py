"""Value functions: raw feature -> v in [0, 1] (1 = best). NaN stays NaN."""
from __future__ import annotations

import numpy as np
import pandas as pd


def linear(x: pd.Series, best: float, worst: float) -> pd.Series:
    """Piecewise-linear physical value function; direction implied by best vs worst."""
    v = (x - worst) / (best - worst)
    return v.clip(0.0, 1.0)


def percentile(x: pd.Series, direction: int, ref_mask: pd.Series | None = None, log: bool = False) -> pd.Series:
    """Empirical CDF against the reference population (default: all non-NaN)."""
    x = np.log1p(x.clip(lower=0)) if log else x
    ref = x[ref_mask] if ref_mask is not None else x
    ref = np.sort(ref.dropna().to_numpy())
    if ref.size == 0:
        return pd.Series(np.nan, index=x.index)
    # mid-rank CDF handles ties (plateaus) symmetrically
    lo = np.searchsorted(ref, x.to_numpy(), side="left")
    hi = np.searchsorted(ref, x.to_numpy(), side="right")
    v = pd.Series((lo + hi) / 2.0 / ref.size, index=x.index)
    v[x.isna()] = np.nan
    return v if direction > 0 else 1.0 - v


def winsor(x: pd.Series, direction: int, lo_pct: float = 2, hi_pct: float = 98,
           ref_mask: pd.Series | None = None, log: bool = False) -> pd.Series:
    x = np.log1p(x.clip(lower=0)) if log else x
    ref = (x[ref_mask] if ref_mask is not None else x).dropna()
    if ref.empty:
        return pd.Series(np.nan, index=x.index)
    lo, hi = np.percentile(ref, [lo_pct, hi_pct])
    if hi <= lo:
        return pd.Series(np.where(x.isna(), np.nan, 0.5), index=x.index)
    v = ((x - lo) / (hi - lo)).clip(0, 1)
    return v if direction > 0 else 1.0 - v


def apply(x: pd.Series, spec: dict, ref_mask: pd.Series | None = None, mode: str = "physical") -> pd.Series:
    """mode='physical' uses spec; mode='percentile' forces percentile rank for every feature
    (method-sensitivity alternative)."""
    t = spec["type"]
    if mode == "percentile":
        if t == "linear":
            d = 1 if spec["best"] > spec["worst"] else -1
            return percentile(x, d, ref_mask)
        return percentile(x, spec["direction"], ref_mask, spec.get("log", False))
    if t == "linear":
        return linear(x, spec["best"], spec["worst"])
    if t == "percentile":
        return percentile(x, spec["direction"], ref_mask, spec.get("log", False))
    if t == "winsor":
        return winsor(x, spec["direction"], spec.get("lo_pct", 2), spec.get("hi_pct", 98),
                      ref_mask, spec.get("log", False))
    raise ValueError(f"unknown valuefn {t}")
