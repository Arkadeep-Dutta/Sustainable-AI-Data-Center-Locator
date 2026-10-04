"""Interactive decision engine demo. Runs entirely from precomputed parquet files.

streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from siteselect import config, gates, scoring  # noqa: E402
from siteselect.config import PILLARS, PROCESSED  # noqa: E402

st.set_page_config(page_title="AI Data Center Site Selector", layout="wide")
RES = 6


@st.cache_data
def load():
    f = pd.read_parquet(PROCESSED / f"features_res{RES}.parquet")
    ft = scoring.feature_table()
    return f, ft


@st.cache_data
def values(_f, mode, water_cooled, tx_max):
    sc = dict(config.load("scenario")); sc["cooling"] = dict(sc["cooling"], water_cooled_scenario=water_cooled)
    g = gates.apply(_f, RES, scenario=sc)
    if tx_max is not None:
        g["excl_G4_transmission"] = _f["gi_dist_tx230_km"] > tx_max
        g["gate_pass"] = ~g.filter(like="excl_").any(axis=1)
    V = scoring.normalize(_f, ref_mask=g["gate_pass"], mode=mode)
    return g, V


f, ft = load()
names = config.load("weights")["pillar_names"]
base = config.load("weights")["pillars"]

st.sidebar.header("Pillar weights")
w = {p: st.sidebar.slider(names[p], 0, 40, int(base[p])) for p in PILLARS}
st.sidebar.header("Scenario / constraints")
water_cooled = st.sidebar.checkbox("Water-cooled design (activates water-stress gate)", False)
tx_max = st.sidebar.slider("Max distance to >=230 kV line (km)", 10, 100, 50)
mode = st.sidebar.radio("Normalization", ["physical", "percentile"], horizontal=True)
agg = st.sidebar.radio("Aggregation", ["geometric", "arithmetic"], horizontal=True)
conf_thr = st.sidebar.slider("Min data confidence", 0.5, 1.0, 0.75, 0.05)

g, V = values(f, mode, water_cooled, tx_max)
W = np.array([w[p] for p in PILLARS], float)
W = W / W.sum() if W.sum() > 0 else np.full(7, 1 / 7)
Vm = V[ft.index].to_numpy()
P = scoring.pillar_scores(Vm, ft["w_norm"].to_numpy(), scoring.onehot(ft), 0.5)
S_A, S_G = scoring.aggregate(P, W, 0.01)
conf = scoring.confidence(Vm, ft, dict(zip(PILLARS, W)))
S = S_G if agg == "geometric" else S_A
df = f[["lat", "lon", "state"]].copy()
df["score"] = S
df["confidence"] = conf
for i, p in enumerate(PILLARS):
    df[p] = P[:, i]
df["eligible"] = g["gate_pass"] & ~np.isnan(P).any(1) & (conf >= conf_thr)
el = df[df["eligible"]].sort_values("score", ascending=False)
el["rank"] = np.arange(1, len(el) + 1)

c1, c2 = st.columns([3, 2])
with c1:
    st.subheader(f"Score map — {len(el):,} eligible H3 res-{RES} regions")
    show = el.head(20000).reset_index()
    lo, hi = show["score"].min(), show["score"].max()
    show["c"] = ((show["score"] - lo) / max(hi - lo, 1e-9) * 255).astype(int)
    layer = pdk.Layer("H3HexagonLayer", show, get_hexagon="h3", get_fill_color="[255 - c, c, 120, 180]",
                      pickable=True, extruded=False)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(latitude=39, longitude=-97, zoom=3.3),
                             tooltip={"text": "{h3}\nscore {score}\nrank {rank}"}, map_style=None))
with c2:
    st.subheader("Top regions")
    from siteselect.candidates import nms
    top = nms(el.reset_index().rename(columns={"score": "S"}), score="S", pool_frac=0.05, radius_km=150, max_regions=15)
    st.dataframe(top[["h3", "state", "lat", "lon", "S", "confidence"] + PILLARS].round(3), hide_index=True)
    pick = st.selectbox("Region detail", top["h3"])
    r = el.loc[pick]
    st.bar_chart(pd.Series({names[p]: r[p] for p in PILLARS}, name="pillar score"))
    raw = f.loc[pick, [c for c in ft.index if c in f]].astype(float).round(3)
    st.dataframe(raw.rename("raw value"))
st.caption("Open data · reproducible configs (config/*.yaml) · modular adapters (siteselect/adapters). "
           "Scores are regional screening values, not parcel valuations.")
