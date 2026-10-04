"""Candidate extraction: top-pool + greedy non-maximum suppression in EPSG:5070."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pyproj import Transformer

_T = Transformer.from_crs(4326, 5070, always_xy=True)


def nms(df: pd.DataFrame, score: str = "S_G", pool_frac: float = 0.05, radius_km: float = 150.0,
        max_regions: int = 25) -> pd.DataFrame:
    """df needs lat, lon, eligible, score. Returns one row per region (best cell) with
    region_id and pool statistics."""
    el = df[df["eligible"] & df[score].notna()]
    pool = el.nlargest(max(1, int(np.ceil(pool_frac * len(el)))), score).copy()
    x, y = _T.transform(pool["lon"].to_numpy(), pool["lat"].to_numpy())
    xy = np.c_[x, y] / 1000.0
    alive = np.ones(len(pool), bool)
    picks, members = [], []
    for i in range(len(pool)):            # pool is sorted by score desc
        if not alive[i]:
            continue
        d = np.hypot(*(xy - xy[i]).T)
        near = alive & (d <= radius_km)
        picks.append(i)
        members.append(near.sum())
        alive &= ~near
        if len(picks) >= max_regions:
            break
    out = pool.iloc[picks].copy()
    out["region_id"] = np.arange(1, len(picks) + 1)
    out["pool_cells_in_region"] = members
    return out


def min_separation_km(df: pd.DataFrame) -> float:
    x, y = _T.transform(df["lon"].to_numpy(), df["lat"].to_numpy())
    xy = np.c_[x, y] / 1000.0
    d = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    np.fill_diagonal(d, np.inf)
    return float(d.min())
