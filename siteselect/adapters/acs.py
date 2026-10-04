"""Census ACS 5-yr 2019-2023 (table-based summary file) at TRACT level + 2023 Gazetteer centroids
-> radius aggregates (FFT disc sums on an EPSG:5070 raster).

Workforce: ages 18-64 (B01001 male 007-019, female 031-043).
Skilled share: C24010 'computer, engineering & science' (007), 'construction & extraction' (032),
'installation, maintenance & repair' (033), 'production' (035); female = male line + 36.
Unemployment: B23025 005 / 003 (civilian labour force).
Income: B19013 median HH income, population-weighted mean of tract medians (approximation).
"""
from __future__ import annotations

import zipfile

import numpy as np
import pandas as pd

from ..config import INTERIM, RAW
from ._util import DiscSum, xy_m


def _read(table: str, cols: list[str]) -> pd.DataFrame:
    df = pd.read_csv(RAW / f"acsdt5y2023-{table}.dat", sep="|", usecols=["GEO_ID"] + cols, dtype={"GEO_ID": str})
    df = df[df["GEO_ID"].str.startswith("1400000US")]
    df["GEOID"] = df["GEO_ID"].str[9:]
    return df.drop(columns="GEO_ID").set_index("GEOID")


def tracts() -> pd.DataFrame:
    p = INTERIM / "acs_tracts.parquet"
    if p.exists():
        return pd.read_parquet(p)
    with zipfile.ZipFile(RAW / "2023_Gaz_tracts_national.zip") as z:
        g = pd.read_csv(z.open("2023_Gaz_tracts_national.txt"), sep="\t", dtype={"GEOID": str})
    g.columns = [c.strip() for c in g.columns]
    g = g.set_index("GEOID")[["INTPTLAT", "INTPTLONG", "ALAND_SQMI"]]
    m = [f"B01001_E{i:03d}" for i in range(7, 20)]
    f = [f"B01001_E{i:03d}" for i in range(31, 44)]
    a = _read("b01001", ["B01001_E001"] + m + f)
    t = pd.DataFrame({"pop": a["B01001_E001"], "wa_pop": a[m + f].sum(1)})
    occ = [7, 32, 33, 35]
    c = _read("c24010", ["C24010_E001"] + [f"C24010_E{i:03d}" for i in occ + [o + 36 for o in occ]])
    t["employed"] = c["C24010_E001"]
    t["skilled"] = c.drop(columns="C24010_E001").sum(1)
    e = _read("b23025", ["B23025_E003", "B23025_E005"])
    t["clf"], t["unemp"] = e["B23025_E003"], e["B23025_E005"]
    inc = _read("b19013", ["B19013_E001"])["B19013_E001"]
    t["med_inc"] = inc.where(inc > 0)
    t = t.join(g, how="inner")
    t = t.apply(pd.to_numeric, errors="coerce")
    t.to_parquet(p)
    return t


def build(cells: pd.DataFrame, heat_radius_km: float = 50.0) -> pd.DataFrame:
    t = tracts()
    t = t[t["INTPTLONG"].between(-125.5, -66.5) & t["INTPTLAT"].between(24, 50)]
    sxy = xy_m(t["INTPTLONG"], t["INTPTLAT"])
    qxy = xy_m(cells["lon"], cells["lat"])
    out = pd.DataFrame(index=cells.index)
    D = DiscSum(2.0)
    def r(col, R, w=None):
        v = t[col].fillna(0).to_numpy(float) * (1 if w is None else w)
        return D.sample(D.disc(D.grid(sxy, v), R), qxy)
    out["ce_workforce_80km"] = r("wa_pop", 80)
    emp, sk = r("employed", 80), r("skilled", 80)
    out["ce_skilled_share_80km"] = np.where(emp > 100, sk / np.maximum(emp, 1), np.nan)
    clf, un = r("clf", 50), r("unemp", 50)
    out["ce_unemployment_50km"] = np.where(clf > 100, un / np.maximum(clf, 1), np.nan)
    has_inc = t["med_inc"].notna().to_numpy()
    pw = t["pop"].fillna(0).to_numpy(float) * has_inc
    num = D.sample(D.disc(D.grid(sxy, np.nan_to_num(t["med_inc"].to_numpy(float)) * pw), 50), qxy)
    den = D.sample(D.disc(D.grid(sxy, pw), 50), qxy)
    out["ce_income_50km"] = np.where(den > 100, num / np.maximum(den, 1), np.nan)
    pop_h = r("pop", heat_radius_km)
    out["pop_50km"] = pop_h
    # local burden: 1 km raster, 5 km radius
    D1 = DiscSum(1.0)
    p5 = D1.sample(D1.disc(D1.grid(sxy, t["pop"].fillna(0).to_numpy(float)), 5), qxy)
    out["ce_popdens_5km"] = p5 / (np.pi * 25.0)
    for c in ["ce_workforce_80km", "ce_skilled_share_80km", "ce_unemployment_50km", "ce_income_50km", "ce_popdens_5km"]:
        out[f"cov_{c}"] = out[c].notna()
    return out
