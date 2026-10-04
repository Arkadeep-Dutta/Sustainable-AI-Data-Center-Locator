"""HIFLD Electric Power Transmission Lines -> distance to HV (220-287 kV class and above) / EHV (>=345 kV)
in-service AC lines and km of HV line within 30 km. VOLTAGE <= 0 (unknown) falls back to VOLT_CLASS.
HVDC lines are EXCLUDED: point-to-point, a load cannot tap them without a converter station.
Feature names keep the '230' label (the class nominal). Distances from cell centroid in EPSG:5070."""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from ..config import CRS_M, RAW
from ._util import DiscSum, xy_m

CLASS_KV = {"220-287": 230, "345": 345, "500": 500, "735 AND ABOVE": 765,
            "UNDER 100": 69, "100-161": 115}
HV_MIN_KV = 220     # floor of the 220-287 kV class (functionally equivalent to 230 kV for a large load)
EHV_MIN_KV = 345


def lines() -> gpd.GeoDataFrame:
    g = gpd.read_parquet(RAW / "hifld_transmission.parquet")
    kv = pd.to_numeric(g["VOLTAGE"], errors="coerce")
    kv = kv.where(kv > 0, g["VOLT_CLASS"].map(CLASS_KV))
    g["kv"] = kv
    st = g["STATUS"].fillna("").str.upper()
    # 'NOT AVAILABLE' = status unknown (21% of lines, mostly western utilities) -> retained as existing
    g = g[~st.str.contains("PROPOSED|UNDER CONST|INACTIVE|RETIRED", regex=True)]
    is_dc = (g["VOLT_CLASS"].fillna("").str.upper() == "DC") | g["TYPE"].fillna("").str.upper().str.contains(r"\bDC\b")
    g = g[~is_dc]
    return g[g.geometry.notna()].to_crs(CRS_M)


def build(cells: pd.DataFrame) -> pd.DataFrame:
    g = lines()
    q = shapely.points(xy_m(cells["lon"], cells["lat"]))
    out = pd.DataFrame(index=cells.index)
    for thr, col in [(HV_MIN_KV, "gi_dist_tx230_km"), (EHV_MIN_KV, "gi_dist_tx345_km")]:
        geoms = g.loc[g["kv"] >= thr, "geometry"].to_numpy()
        tree = shapely.STRtree(geoms)
        idx, dist = tree.query_nearest(q, return_distance=True, all_matches=False)
        d = np.full(len(q), np.nan)
        d[idx[0]] = dist / 1000.0
        out[col] = d
    # length density: sample points every 1 km along >=230 kV lines, each carrying 1 km
    hv = g.loc[g["kv"] >= HV_MIN_KV, "geometry"]
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
