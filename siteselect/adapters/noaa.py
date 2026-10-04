"""NOAA 1991-2020 Climate Normals (annual/seasonal, by station) -> HDD65, CDD65 via IDW (k=8, p=2,
EPSG:5070). Derived PUE / on-site WUE use scenario.yaml ASSUMPTIONS on these OBSERVED normals."""
from __future__ import annotations

import tarfile

import numpy as np
import pandas as pd

from .. import config
from ..config import INTERIM, RAW
from ._util import idw, xy_m

CONUS_BBOX = (-125.5, 24.0, -66.5, 49.8)


def stations() -> pd.DataFrame:
    p = INTERIM / "noaa_normals_stations.parquet"
    if p.exists():
        return pd.read_parquet(p)
    rows = []
    with tarfile.open(RAW / "noaa_normals_annualseasonal_1991_2020.tar.gz") as t:
        for m in t:
            if not m.isfile() or not m.name.endswith(".csv"):
                continue
            df = pd.read_csv(t.extractfile(m), usecols=lambda c: c in
                             ("STATION", "LATITUDE", "LONGITUDE", "ANN-HTDD-NORMAL", "ANN-CLDD-NORMAL"))
            if {"ANN-HTDD-NORMAL", "ANN-CLDD-NORMAL"} <= set(df.columns):
                rows.append(df.iloc[0])
    s = pd.DataFrame(rows).rename(columns={"ANN-HTDD-NORMAL": "hdd", "ANN-CLDD-NORMAL": "cdd"})
    s = s.dropna(subset=["hdd", "cdd"])
    s = s[(s["hdd"] >= 0) & (s["cdd"] >= 0)]
    s.to_parquet(p)
    return s


def build(cells: pd.DataFrame) -> pd.DataFrame:
    s = stations()
    lo, la, hi, ha = CONUS_BBOX
    s = s[s["LONGITUDE"].between(lo - 3, hi + 3) & s["LATITUDE"].between(la - 3, ha + 3)]
    xy = xy_m(s["LONGITUDE"], s["LATITUDE"])
    out = pd.DataFrame(index=cells.index)
    out["hdd65"] = idw(cells, xy, s["hdd"].to_numpy(float))
    out["cdd65"] = idw(cells, xy, s["cdd"].to_numpy(float))
    c = config.load("scenario")["cooling"]
    out["ec_pue"] = c["pue_base"] + c["pue_per_cdd"] * out["cdd65"]
    out["wa_onsite_wue"] = c["wue_base_l_per_kwh"] + c["wue_per_cdd"] * out["cdd65"]
    out["hr_hdd"] = out["hdd65"]
    for k in ["ec_pue", "wa_onsite_wue", "hr_hdd"]:
        out[f"cov_{k}"] = out[k].notna()
    return out
