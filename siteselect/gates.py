"""Hard constraints applied before MCDA."""
from __future__ import annotations

import pandas as pd

from . import config


def apply(df: pd.DataFrame, res: int, level: str = "national", scenario: dict | None = None) -> pd.DataFrame:
    """Return DataFrame of boolean excl_<gate> columns + 'gate_pass'.
    Missing gate feature -> not excluded by that gate (handled by confidence rules instead)."""
    gates = config.load("gates")[level]
    scenario = scenario or config.load("scenario")
    out = pd.DataFrame(index=df.index)
    for name, g in gates.items():
        flag = g.get("only_if_scenario")
        if flag and not scenario.get("cooling", {}).get(flag, False):
            continue
        if g["feature"] not in df:
            continue
        thr = g["threshold"]
        thr = thr[res] if isinstance(thr, dict) else thr
        x = df[g["feature"]]
        out[f"excl_{name}"] = (x < thr) if g["rule"] == "lt" else (x > thr)
        out[f"excl_{name}"] = out[f"excl_{name}"].fillna(False)
    out["gate_pass"] = ~out.any(axis=1) if len(out.columns) else True
    return out


def removal_table(excl: pd.DataFrame, area: pd.Series | None = None) -> pd.DataFrame:
    """% of cells (or area) removed by each gate individually and cumulatively."""
    w = area if area is not None else pd.Series(1.0, index=excl.index)
    tot = w.sum()
    rows, cum = [], pd.Series(False, index=excl.index)
    for c in [c for c in excl.columns if c.startswith("excl_")]:
        cum = cum | excl[c]
        rows.append({"gate": c[5:], "pct_individual": 100 * w[excl[c]].sum() / tot,
                     "pct_cumulative": 100 * w[cum].sum() / tot})
    return pd.DataFrame(rows)
