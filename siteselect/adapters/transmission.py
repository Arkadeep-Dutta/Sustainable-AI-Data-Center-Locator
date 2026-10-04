"""HIFLD Electric Power Transmission Lines -> distance to >=230 / >=345 kV in-service lines and
km of >=230 kV line within 30 km. VOLTAGE <= 0 (unknown, -999999) falls back to VOLT_CLASS.
Distances from cell centroid in EPSG:5070 (STRtree nearest)."""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from ..config import CRS_M, RAW
from ._util import DiscSum, xy_m

CLASS_KV = {"220-287": 230, "345": 345, "500": 500, "735 AND ABOVE": 765, "DC": 500,
            "UNDER 100": 69, "100-161": 115}


def lines() -> gpd.GeoDataFrame:
    g = gpd.read_parquet(RAW / "hifld_transmission.parquet")
    kv = pd.to_numeric(g["VOLTAGE"], errors="coerce")
    kv = kv.where(kv > 0, g["VOLT_CLASS"].map(CLASS_KV))
    g["kv"] = kv
    st = g["STATUS"].fillna("").str.upper()
    # 'NOT AVAILABLE' = status unknown (21% of lines, mostly western utilities) -> retained as existing
    g = g[~st.str.contains("PROPOSED|UNDER CONST|INACTIVE|RETIRED", regex=True)]
    return g[g.geometry.notna()].to_crs(CRS_M)


def build(cells: pd.DataFrame) -> pd.DataFrame:
    g = lines()
    q = shapely.points(xy_m(cells["lon"], cells["lat"]))
    out = pd.DataFrame(index=cells.index)
    for thr, col in [(230, "gi_dist_tx230_km"), (345, "gi_dist_tx345_km")]:
        geoms = g.loc[g["kv"] >= thr, "geometry"].to_numpy()
        tree = shapely.STRtree(geoms)
        idx, dist = tree.query_nearest(q, return_distance=True, all_matches=False)
        d = np.full(len(q), np.nan)
        d[idx[0]] = dist / 1000.0
        out[col] = d
    # length density: sample points every 1 km along >=230 kV lines, each carrying 1 km
    hv = g.loc[g["kv"] >= 230, "geometry"]
    pts = []
    for geom in hv:
        n = max(1, int(geom.length // 1000))
        pts.append(shapely.get_coordinates(shapely.line_interpolate_point(geom, np.linspace(0, geom.length, n))))
    pts = np.concatenate(pts)
    D = DiscSum(2.0)
    out["gi_tx_km_30km"] = D.sample(D.disc(D.grid(pts, np.ones(len(pts))), 30), xy_m(cells["lon"], cells["lat"]))
    for c in ["gi_dist_tx230_km", "gi_dist_tx345_km", "gi_tx_km_30km"]:
        out[f"cov_{c}"] = out[c].notna()
    return out
