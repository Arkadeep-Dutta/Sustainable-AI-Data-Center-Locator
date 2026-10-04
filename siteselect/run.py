"""Pipeline stages.

python -m siteselect.run --stage score     --res 6   # gates + MCDA -> scores_res6.parquet
python -m siteselect.run --stage gate2     --res 6   # methodology diagnostics -> outputs/diagnostics/gate2_*.csv
python -m siteselect.run --stage sanity    --res 6
python -m siteselect.run --stage candidates --res 6
"""
from __future__ import annotations

import argparse

import h3
import numpy as np
import pandas as pd

from . import candidates as cand
from . import config, gates, scoring
from .config import DIAG, OUTPUTS, PILLARS, PROCESSED

MARKETS = {"Loudoun Co VA": (39.08, -77.65), "Quincy WA": (47.23, -119.85),
           "The Dalles OR": (45.60, -121.18), "Altoona (central) IA": (41.65, -93.47),
           "Abilene TX": (32.45, -99.73), "Cheyenne WY": (41.14, -104.82), "Phoenix AZ": (33.45, -112.07)}


def load_features(res: int, tag: str = "") -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / f"features_res{res}{tag}.parquet")


def score(res: int, mode: str = "physical", tag: str = "", level: str = "national") -> pd.DataFrame:
    df = load_features(res, tag)
    g = gates.apply(df, res, level=level)
    s = scoring.score(df, g["gate_pass"], mode=mode)
    out = pd.concat([df[["lat", "lon", "state"]], g, s], axis=1)
    out.to_parquet(PROCESSED / f"scores_res{res}{tag}{'' if mode == 'physical' else '_' + mode}.parquet")
    return out


def gate2(res: int) -> None:
    df = load_features(res)
    g = gates.apply(df, res)
    gates.removal_table(g, df["area_km2"]).round(2).to_csv(DIAG / f"gate2_gates_res{res}.csv", index=False)
    rows = []
    wcfg = config.load("weights")
    for thr in [0.6, 0.75, 0.9]:
        wcfg["confidence_threshold"] = thr
        s = scoring.score(df, g["gate_pass"])
        rows.append({"conf_threshold": thr, "eligible_cells": int(s["eligible"].sum()),
                     "pct_area": round(100 * df.loc[s["eligible"], "area_km2"].sum() / df["area_km2"].sum(), 2),
                     "top_cell": s["S_G"].where(s["eligible"]).idxmax()})
    wcfg["confidence_threshold"] = 0.75
    pd.DataFrame(rows).to_csv(DIAG / f"gate2_confidence_res{res}.csv", index=False)
    feats = [f for f in config.features() if f in df]
    c = df.loc[g["gate_pass"], feats].corr(method="spearman")
    pairs = c.where(np.triu(np.ones(c.shape, bool), 1)).stack()
    pairs[pairs.abs() > 0.6].sort_values(key=abs, ascending=False).round(3).to_csv(
        DIAG / f"gate2_corr_flags_res{res}.csv", header=["spearman"])
    c.round(3).to_csv(DIAG / f"correlation_res{res}.csv")
    df.loc[g["gate_pass"], feats].describe(percentiles=[.05, .5, .95]).T.round(3).to_csv(
        DIAG / f"feature_distributions_res{res}.csv")


def sanity(res: int, tag: str = "") -> pd.DataFrame:
    s = pd.read_parquet(PROCESSED / f"scores_res{res}{tag}.parquet")
    f = load_features(res, tag)
    keys = ["ec_co2_rate", "wa_bws", "gi_dist_tx230_km", "ce_workforce_80km", "lm_suitable_km2",
            "hr_hdd", "egrid_subrgn"]
    rows = []
    for name, (la, lo) in MARKETS.items():
        c = h3.latlng_to_cell(la, lo, res)
        if c not in s.index:
            rows.append({"market": name, "h3": c, "note": "cell not in grid"})
            continue
        r = {"market": name, "h3": c, **{k: f.at[c, k] for k in keys if k in f},
             **{k: s.at[c, k] for k in ["gate_pass", "eligible", "confidence", "S_G", "rank_G"] + [f"P_{p}" for p in PILLARS]}}
        r["pct_rank"] = round(100 * (1 - (r["rank_G"] or np.nan) / s["eligible"].sum()), 1) if r["eligible"] else None
        rows.append(r)
    out = pd.DataFrame(rows)
    out.round(3).to_csv(DIAG / f"sanity_markets_res{res}{tag}.csv", index=False)
    # regional plateau diagnostic: share of S_G variance explained by eGRID subregion
    e = s[s["eligible"]].join(f["egrid_subrgn"])
    tot = e["S_G"].var()
    within = e.groupby("egrid_subrgn")["S_G"].var().mul(e.groupby("egrid_subrgn").size()).sum() / len(e)
    with open(DIAG / f"plateau_res{res}{tag}.txt", "w") as fh:
        fh.write(f"R2 of S_G explained by eGRID subregion: {1 - within / tot:.3f}\n")
    return out


def candidates(res: int, pool_frac: float = 0.05, radius_km: float = 150, n: int = 25) -> pd.DataFrame:
    s = pd.read_parquet(PROCESSED / f"scores_res{res}.parquet")
    c = cand.nms(s.reset_index(), pool_frac=pool_frac, radius_km=radius_km, max_regions=n)
    c.to_parquet(PROCESSED / f"candidates_res{res}.parquet")
    return c


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--res", type=int, default=6)
    a = ap.parse_args()
    if a.stage == "score":
        o = score(a.res); print(f"eligible {int(o['eligible'].sum())}/{len(o)}")
        score(a.res, mode="percentile")
    elif a.stage == "gate2":
        gate2(a.res)
    elif a.stage == "sanity":
        sanity(a.res)
    elif a.stage == "candidates":
        print(len(candidates(a.res)))
