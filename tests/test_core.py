import numpy as np
import pandas as pd
import pytest

from siteselect import candidates, gates, robustness, scoring, valuefn
from siteselect.config import PILLARS


def test_linear_direction_and_clip():
    x = pd.Series([50, 100, 400, 700, 900, np.nan])
    v = valuefn.linear(x, best=100, worst=700)          # lower is better (carbon)
    assert v.iloc[0] == 1 and v.iloc[1] == 1 and v.iloc[3] == 0 and v.iloc[4] == 0
    assert v.iloc[2] == pytest.approx(0.5)
    assert np.isnan(v.iloc[5])
    v2 = valuefn.linear(pd.Series([2, 8.5, 15]), best=15, worst=2)   # higher is better (land)
    assert list(v2.round(3)) == [0, 0.5, 1]


def test_percentile_reference_population_and_direction():
    x = pd.Series([1.0, 2, 3, 4, 100])
    ref = pd.Series([True, True, True, True, False])
    v = valuefn.percentile(x, -1, ref)                  # lower hazard better
    assert v.iloc[0] > v.iloc[3] and v.iloc[4] == 0     # 100 is beyond ref -> worst


def test_gates_exclude_and_ignore_missing():
    df = pd.DataFrame({"lm_suitable_km2": [1.0, 5.0, np.nan], "lm_unbuildable_frac": [0, 0.9, 0],
                       "gi_dist_tx230_km": [10, 10, 80], "wa_bws": [0.9, 0.9, 0.9]})
    g = gates.apply(df, res=6)
    assert list(g["gate_pass"]) == [False, False, False]
    assert g.loc[2, "excl_G1_land"] == False and g.loc[2, "excl_G4_transmission"] == True  # noqa: E712
    assert "excl_G5_water" not in g      # dry-cooling base case: G5 inactive


def _V_two_pillars_missing():
    ft = scoring.feature_table()
    V = np.full((2, len(ft)), 0.5)
    hr = (ft["pillar"] == "HR").to_numpy()
    V[1, hr] = np.nan                    # whole HR pillar missing for cell 1
    return ft, V


def test_missing_pillar_makes_scores_nan_and_confidence_drops():
    ft, V = _V_two_pillars_missing()
    P = scoring.pillar_scores(V, ft["w_norm"].to_numpy(), scoring.onehot(ft), 0.5)
    assert np.isnan(P[1, PILLARS.index("HR")]) and not np.isnan(P[0]).any()
    W = {p: 1 / 7 for p in PILLARS}
    c = scoring.confidence(V, ft, W)
    assert c[0] == pytest.approx(1.0) and c[1] == pytest.approx(6 / 7)
    _, S_G = scoring.aggregate(P, np.full(7, 1 / 7), 0.01)
    assert np.isnan(S_G[1])


def test_within_pillar_renorm_threshold():
    ft = scoring.feature_table()
    B = scoring.onehot(ft)
    V = np.full((1, len(ft)), 0.8)
    ec = ft.index[ft["pillar"] == "EC"]
    V[0, ft.index.get_loc("ec_co2_rate")] = np.nan       # 0.5 of EC weight missing -> still ok
    P = scoring.pillar_scores(V, ft["w_norm"].to_numpy(), B, 0.5)
    assert P[0, 0] == pytest.approx(0.8)
    V[0, ft.index.get_loc("ec_clean_share")] = np.nan    # 0.8 missing -> pillar invalid
    P = scoring.pillar_scores(V, ft["w_norm"].to_numpy(), B, 0.5)
    assert np.isnan(P[0, 0]) and len(ec) == 3


def test_geometric_penalizes_weak_pillar():
    W = np.full(7, 1 / 7)
    balanced = np.full((1, 7), 0.6)
    lopsided = np.array([[0.95] * 6 + [0.02]])
    SA_b, SG_b = scoring.aggregate(balanced, W, 0.01)
    SA_l, SG_l = scoring.aggregate(lopsided, W, 0.01)
    assert SA_l > SA_b and SG_l < SG_b


def test_pillar_weights_normalized():
    from siteselect import config
    assert sum(config.pillar_weights().values()) == pytest.approx(1.0)
    ft = scoring.feature_table()
    assert ft.groupby("pillar")["w_norm"].sum().round(9).eq(1).all()
    assert set(ft["pillar"]) == set(PILLARS)               # no empty pillar


def test_candidate_diversity():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"lat": rng.uniform(30, 48, 3000), "lon": rng.uniform(-120, -75, 3000),
                       "S_G": rng.uniform(0, 1, 3000), "eligible": True})
    c = candidates.nms(df, pool_frac=0.2, radius_km=150, max_regions=20)
    assert len(c) <= 20 and candidates.min_separation_km(c) > 150


def test_robustness_mc_and_pareto():
    ft = scoring.feature_table()
    rng = np.random.default_rng(1)
    V = rng.uniform(0.2, 0.9, (6, len(ft)))
    V[0] = 0.95                                            # dominant row
    ranks = robustness.weight_mc(V, n_draws=200, batch=100)
    assert ranks.shape == (200, 6) and (ranks[:, 0] == 1).all()
    P = scoring.pillar_scores(V, ft["w_norm"].to_numpy(), scoring.onehot(ft), 0.5)
    dom = robustness.pareto_dominated(P)
    assert not dom[0] and dom[1:].all()
