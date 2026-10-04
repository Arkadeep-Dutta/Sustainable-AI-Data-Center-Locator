"""Robustness: Dirichlet pillar-weight MC + within-pillar feature jitter, method sensitivity,
Pareto dominance, missing-data downside. Definitions fixed in SPEC §12."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .config import PILLARS
from .scoring import aggregate, feature_table, onehot, pillar_scores


def weight_mc(V: np.ndarray, n_draws: int = 5000, kappa: float = 100.0, jitter: tuple = (0.8, 1.2),
              seed: int = 42, batch: int = 500) -> np.ndarray:
    """V (n,F) normalized values for the candidate set. Returns ranks (n_draws, n) by S_G (1 = best)."""
    rng = np.random.default_rng(seed)
    wcfg = config.load("weights")
    ft = feature_table()
    B = onehot(ft)
    W0 = np.array([config.pillar_weights()[p] for p in PILLARS])
    wf0 = ft["w_norm"].to_numpy()
    ranks = []
    for s in range(0, n_draws, batch):
        k = min(batch, n_draws - s)
        W = rng.dirichlet(kappa * W0, size=k)                       # (k,7)
        wf = wf0 * rng.uniform(*jitter, size=(k, wf0.size))         # (k,F); renormalized inside pillar_scores
        P = pillar_scores(V, wf, B, wcfg["min_pillar_weight_observed"])   # (k,n,7)
        _, S_G = aggregate(P, W, wcfg["epsilon"])                   # (k,n)
        S_G = np.nan_to_num(S_G, nan=-1.0)
        ranks.append((-S_G).argsort(axis=1).argsort(axis=1) + 1)
    return np.concatenate(ranks)


def summarize(ranks: np.ndarray, ids: list, baseline_SG: np.ndarray) -> pd.DataFrame:
    base_rank = pd.Series(-baseline_SG).rank(method="min").to_numpy()
    df = pd.DataFrame({
        "id": ids, "baseline_rank": base_rank, "baseline_S_G": baseline_SG,
        "median_rank": np.median(ranks, axis=0), "p_rank1": (ranks == 1).mean(axis=0),
        "p_top5": (ranks <= 5).mean(axis=0),
        "rank_p05": np.percentile(ranks, 5, axis=0), "rank_p95": np.percentile(ranks, 95, axis=0),
    })
    # Robustness winner rule (fixed in advance): max P(rank=1) -> better median -> higher baseline S_G
    return df.sort_values(["p_rank1", "median_rank", "baseline_S_G"],
                          ascending=[False, True, False]).reset_index(drop=True)


def pareto_dominated(P: np.ndarray) -> np.ndarray:
    """P (n,7) pillar scores. True where some other row is >= on all and > on one."""
    n = P.shape[0]
    dom = np.zeros(n, bool)
    for i in range(n):
        ge = (P >= P[i]).all(axis=1)
        gt = (P > P[i]).any(axis=1)
        dom[i] = (ge & gt).any()
    return dom


def missing_downside(V: np.ndarray, fill: np.ndarray) -> np.ndarray:
    """Replace missing values with conservative fill (F,) e.g. eligible-population p10 or 0."""
    return np.where(np.isnan(V), fill[None, :], V)
