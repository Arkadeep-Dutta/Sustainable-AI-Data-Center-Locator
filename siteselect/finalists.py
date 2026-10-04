"""Finalist selection (best eligible res-7 cell per refined region) + full robustness suite (SPEC §12).

python -m siteselect.finalists  -> outputs/diagnostics/finalists_*.csv
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import config, robustness, scoring, valuefn
from .adapters import egrid
from .config import DIAG, PILLARS, PROCESSED


def pick() -> pd.DataFrame:
    s = pd.read_parquet(PROCESSED / "scores_res7_refine.parquet")
    el = s[s["eligible"]]
    best = el.loc[el.groupby("region_id")["S_G"].idxmax()].copy()
    # region depth: number of eligible res-7 cells within 0.02 of the region best (site optionality)
    best["n_near_best_cells"] = [int(((el["region_id"] == r) & (el["S_G"] >= v - 0.02)).sum())
                                 for r, v in zip(best["region_id"], best["S_G"])]
    return best.sort_values("S_G", ascending=False)


def _agg(V, W=None, wf=None):
    ft = scoring.feature_table()
    W = np.array([config.pillar_weights()[p] for p in PILLARS]) if W is None else W
    wf = ft["w_norm"].to_numpy() if wf is None else wf
    P = scoring.pillar_scores(V, wf, scoring.onehot(ft), config.load("weights")["min_pillar_weight_observed"])
    return P, *scoring.aggregate(P, W, config.load("weights")["epsilon"])


def _rank(x):
    return pd.Series(-np.nan_to_num(x, nan=1)).rank(method="min").to_numpy().astype(int)


def run() -> dict:
    fin = pick()
    ids = fin.index.to_list()
    labels = [f"R{r}" for r in fin["region_id"]]
    ft = scoring.feature_table()
    V = fin[[f"v_{k}" for k in ft.index]].to_numpy()
    P, SA, SG = _agg(V)
    tab = pd.DataFrame({"label": labels, "h3": ids, "region_id": fin["region_id"].to_numpy(),
                        "lat": fin["lat"].to_numpy(), "lon": fin["lon"].to_numpy(),
                        "state": fin["state"].to_numpy(), "S_G": SG, "S_A": SA,
                        "rank_G": _rank(SG), "rank_A": _rank(SA), "confidence": fin["confidence"].to_numpy(),
                        "n_near_best_cells": fin["n_near_best_cells"].to_numpy()})
    for i, p in enumerate(PILLARS):
        tab[f"P_{p}"] = P[:, i]
    # method: percentile normalisation
    sp = pd.read_parquet(PROCESSED / "scores_res7_refine_percentile.parquet").loc[ids]
    Vp = sp[[f"v_{k}" for k in ft.index]].to_numpy()
    tab["rank_pctnorm"] = _rank(_agg(Vp)[2])
    # weight-set sensitivity
    orig = np.array([22, 16, 16, 15, 14, 10, 7], float) / 100
    tab["rank_origweights"] = _rank(_agg(V, W=orig)[2])
    tab["rank_equalweights"] = _rank(_agg(V, W=np.full(7, 1 / 7))[2])
    # hydro water inclusion (grid water is a linear value fn -> no reference-population effect)
    f7 = pd.read_parquet(PROCESSED / "features_res7_refine.parquet").loc[ids]
    hyd = egrid.subregion_table(include_hydro=True)["wa_grid_water"]
    Vh = V.copy()
    j = ft.index.get_loc("wa_grid_water")
    spec = config.features()["wa_grid_water"]["valuefn"]
    Vh[:, j] = valuefn.linear(f7["egrid_subrgn"].map(hyd).astype(float), spec["best"], spec["worst"]).to_numpy()
    tab["rank_hydro_water"] = _rank(_agg(Vh)[2])
    # missing-data downside: national eligible p10 of each v, and worst case 0
    s6 = pd.read_parquet(PROCESSED / "scores_res6.parquet")
    p10 = s6.loc[s6["eligible"], [f"v_{k}" for k in ft.index]].quantile(0.10).to_numpy()
    tab["n_missing_features"] = np.isnan(V).sum(1)
    tab["rank_missing_p10"] = _rank(_agg(robustness.missing_downside(V, p10))[2])
    tab["rank_missing_zero"] = _rank(_agg(robustness.missing_downside(V, np.zeros(V.shape[1])))[2])
    # Pareto
    tab["pareto_dominated"] = robustness.pareto_dominated(np.nan_to_num(P))
    # water-cooled scenario gate
    tab["fails_G5_if_water_cooled"] = (f7["wa_bws"] > 0.8).to_numpy()
    # Dirichlet MC
    mc = {}
    for kappa in (50, 100, 200):
        r = robustness.weight_mc(V, n_draws=5000, kappa=kappa)
        sm = robustness.summarize(r, labels, SG)
        sm.round(4).to_csv(DIAG / f"finalists_mc_k{kappa}.csv", index=False)
        mc[kappa] = sm
        if kappa == 100:
            hist = pd.DataFrame({lab: np.bincount(r[:, i], minlength=len(labels) + 1)[1:] / len(r)
                                 for i, lab in enumerate(labels)}, index=range(1, len(labels) + 1))
            hist.round(4).to_csv(DIAG / "finalists_rank_hist_k100.csv")
    m = mc[100].set_index("id")
    for c in ["p_rank1", "p_top5", "median_rank", "rank_p05", "rank_p95"]:
        tab[c + "_k100"] = tab["label"].map(m[c])
    for k in (50, 200):
        tab[f"p_rank1_k{k}"] = tab["label"].map(mc[k].set_index("id")["p_rank1"])
    tab = tab.sort_values("rank_G")
    tab.round(4).to_csv(DIAG / "finalists_robustness.csv", index=False)
    winner = mc[100].iloc[0]["id"]
    res = {"robustness_winner_k100": winner, "baseline_winner": tab.iloc[0]["label"]}
    (DIAG / "finalists_summary.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    print(run())
