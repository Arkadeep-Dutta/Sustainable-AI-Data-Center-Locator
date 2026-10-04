"""FEMA National Risk Index (census tracts) -> hazard annualized frequencies.

Tract table joined to 2023 Gazetteer tract centroids by GEOID; each cell takes the NEAREST matched
tract centroid (no tract polygons downloaded) — approximation documented in docs/03.
AFREQ = modelled annualized event frequency (hazard occurrence, independent of exposed value),
preferred over EAL scores which scale with building value/population.
"""
from __future__ import annotations

import pandas as pd

from ..config import RAW
from ._util import nearest_values, xy_m
from .acs import tracts

MAP = {"cr_flood_freq": ["IFLD_AFREQ", "CFLD_AFREQ"], "cr_wildfire_freq": ["WFIR_AFREQ"],
       "cr_hurricane_freq": ["HRCN_AFREQ"], "cr_heatwave_freq": ["HWAV_AFREQ"],
       "cr_drought_freq": ["DRGT_AFREQ"], "cr_tornado_freq": ["TRND_AFREQ"]}


def build(cells: pd.DataFrame) -> pd.DataFrame:
    n = pd.read_parquet(RAW / "fema_nri_tracts.parquet")
    n["TRACTFIPS"] = n["TRACTFIPS"].astype(str).str.zfill(11)
    n = n.set_index("TRACTFIPS")
    t = tracts()[["INTPTLAT", "INTPTLONG"]].join(n, how="inner")
    t = t[t["INTPTLONG"].between(-125.5, -66.5) & t["INTPTLAT"].between(24, 50)]
    feats = pd.DataFrame(index=t.index)
    for k, cols in MAP.items():
        # sum of component frequencies; a component missing in NRI means hazard not modelled -> 0
        feats[k] = t[cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(1)
        feats.loc[t[cols].isna().all(1), k] = pd.NA if k != "cr_hurricane_freq" else 0.0
    out, d = nearest_values(cells, xy_m(t["INTPTLONG"], t["INTPTLAT"]), feats.astype(float), max_km=60)
    out["nri_tract_dist_km"] = d
    for k in MAP:
        out[f"cov_{k}"] = out[k].notna()
    return out
