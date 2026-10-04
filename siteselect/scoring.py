"""Normalization, pillar aggregation, confidence, arithmetic/geometric MCDA.

Matrix form (used by robustness too):
  V  (n x F) value matrix, NaN = missing observation
  B  (F x 7) one-hot feature->pillar
  wf (F,)    within-pillar feature weights (sum to 1 per pillar)
  P_p = sum_f wf v / sum_f wf m   if observed pillar weight share >= min_obs, else NaN
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, valuefn
from .config import PILLARS


def feature_table() -> pd.DataFrame:
    f = config.features()
    t = pd.DataFrame({"pillar": {k: v["pillar"] for k, v in f.items()},
                      "weight": {k: float(v["weight"]) for k, v in f.items()}})
    t["w_norm"] = t["weight"] / t.groupby("pillar")["weight"].transform("sum")
    return t


def normalize(df: pd.DataFrame, ref_mask: pd.Series | None = None, mode: str = "physical") -> pd.DataFrame:
    f = config.features()
    cols = {}
    for k, spec in f.items():
        x = df[k] if k in df else pd.Series(np.nan, index=df.index)
        cols[k] = valuefn.apply(x.astype(float), spec["valuefn"], ref_mask, mode)
    return pd.DataFrame(cols, index=df.index)


def onehot(ft: pd.DataFrame) -> np.ndarray:
    return np.stack([(ft["pillar"] == p).to_numpy(float) for p in PILLARS], axis=1)


def pillar_scores(V: np.ndarray, wf: np.ndarray, B: np.ndarray, min_obs: float) -> np.ndarray:
    """V (n,F) with NaN; wf (F,) or (k,F) per-draw. Returns (n,7) or (k,n,7)."""
    M = ~np.isnan(V)
    A = np.where(M, V, 0.0)
    Wb = wf[..., :, None] * B                      # (...,F,7)
    tot = Wb.sum(axis=-2)                          # (...,7)
    num = A @ Wb                                   # (...,n,7)
    den = M.astype(float) @ Wb
    share = den / np.where(tot == 0, 1, tot)[..., None, :]
    with np.errstate(invalid="ignore", divide="ignore"):
        P = num / den
    return np.where(share >= min_obs - 1e-12, P, np.nan)


def aggregate(P: np.ndarray, W: np.ndarray, eps: float) -> tuple[np.ndarray, np.ndarray]:
    """P (...,n,7), W (...,7) -> S_A, S_G (...,n). NaN pillar -> NaN score."""
    W = W[..., None, :]
    S_A = (P * W).sum(axis=-1)
    S_G = np.exp((np.log(np.maximum(P, eps)) * W).sum(axis=-1))
    bad = np.isnan(P).any(axis=-1)
    return np.where(bad, np.nan, S_A), np.where(bad, np.nan, S_G)


def confidence(V: np.ndarray, ft: pd.DataFrame, W: dict[str, float]) -> np.ndarray:
    """Fraction of intended total model weight backed by real observations."""
    intended = ft["w_norm"].to_numpy() * ft["pillar"].map(W).to_numpy()
    return (~np.isnan(V)).astype(float) @ intended


def score(df: pd.DataFrame, gate_pass: pd.Series, mode: str = "physical",
          pillar_w: dict[str, float] | None = None, feat_w: pd.Series | None = None) -> pd.DataFrame:
    """Full scoring. Percentile/winsor reference population = gate-passing cells."""
    wcfg = config.load("weights")
    W = pillar_w or config.pillar_weights()
    ft = feature_table()
    if feat_w is not None:
        ft["weight"] = feat_w.reindex(ft.index).fillna(0)
        ft["w_norm"] = ft["weight"] / ft.groupby("pillar")["weight"].transform("sum")
    Vdf = normalize(df, ref_mask=gate_pass, mode=mode)
    V = Vdf[ft.index].to_numpy()
    B = onehot(ft)
    P = pillar_scores(V, ft["w_norm"].to_numpy(), B, wcfg["min_pillar_weight_observed"])
    Wv = np.array([W[p] for p in PILLARS])
    S_A, S_G = aggregate(P, Wv, wcfg["epsilon"])
    conf = confidence(V, ft, W)
    out = pd.DataFrame(index=df.index)
    for i, p in enumerate(PILLARS):
        out[f"P_{p}"] = P[:, i]
    out["pillars_complete"] = ~np.isnan(P).any(axis=1)
    out["confidence"] = conf
    out["S_A"], out["S_G"] = S_A, S_G
    out["eligible"] = gate_pass & out["pillars_complete"] & (out["confidence"] >= wcfg["confidence_threshold"])
    out["rank_G"] = out["S_G"].where(out["eligible"]).rank(ascending=False, method="min")
    out["rank_A"] = out["S_A"].where(out["eligible"]).rank(ascending=False, method="min")
    return pd.concat([Vdf.add_prefix("v_"), out], axis=1)
