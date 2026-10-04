"""Interactive decision engine demo. Runs entirely from precomputed files.

streamlit run app/streamlit_app.py            # opens on the judge-facing "Final recommendation" view
streamlit run app/streamlit_app.py -- --explore   (or add ?view=explore to the URL) for the re-weighting view

The "Final recommendation" view only READS precomputed outputs (outputs/*.csv, outputs/diagnostics/impact.csv);
it performs no scoring. The "Explore & re-weight" view re-scores the national feature store live.
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
OUT = ROOT / "outputs"
VIEWS = ["Final recommendation", "Explore & re-weight"]
RECOMMENDED, MODEL_TOP = "R2", "R1"


# --------------------------------------------------------------------------- final recommendation view
@st.cache_data
def load_final():
    fin = pd.read_csv(OUT / "finalists_rankings.csv")
    cty = pd.read_csv(OUT / "diagnostics" / "finalists_county.csv").set_index("label")["county"]
    fin["site"] = fin["label"].map(cty)
    imp = pd.read_csv(OUT / "diagnostics" / "impact.csv").iloc[:3]
    top = pd.read_csv(OUT / "rankings.csv", nrows=20000, usecols=["h3_res6", "S_G", "rank_G"])
    return fin, imp, top


def final_view():
    fin, imp, top = load_final()
    rec = fin.set_index("label").loc[RECOMMENDED]
    mod = fin.set_index("label").loc[MODEL_TOP]

    st.title("Where should America's next sustainable AI data center be built?")
    st.subheader(f"Recommendation: {rec['site']} (Town of Sheldon) — {rec['lat']:.4f} °N, {rec['lon']:.4f} °W")
    c = st.columns(4)
    c[0].metric("Final recommended site", "Wyoming Co, NY", f"S_G {rec['S_G']:.3f} · model rank #{int(rec['rank_G'])}",
                delta_color="off", delta_arrow="off")
    c[1].metric("Model #1 (quantitative)", "King Co, WA", f"S_G {mod['S_G']:.3f} · P(rank 1) {mod['p_rank1_k100']:.2f}",
                delta_color="off", delta_arrow="off")
    c[2].metric("Wyoming robustness", f"P(top 5) = {rec['p_top5_k100']:.3f}",
                f"median rank {rec['median_rank_k100']:.0f} of 8", delta_color="off", delta_arrow="off")
    g = imp.set_index("name")["co2_t"]
    c[3].metric("Operational CO₂ vs Loudoun VA", f"{g.iloc[0] / 1e3:,.0f} kt/yr",
                f"{(g.iloc[0] / g.iloc[1] - 1) * 100:+.0f} % vs {g.iloc[1] / 1e3:,.0f} kt", delta_color="inverse")

    st.info(
        "**How the final site was chosen.** The engine scores 209,488 CONUS hexagons and produces a robust shortlist. "
        "By design, the team decides manually among the top finalists. **King County, WA is the model's #1.** "
        "**Wyoming County, NY was selected** after manual review of the regulatory and political context: "
        "the King County model site is RA-10 rural land under Growth Management Act limits; adjacent Pierce County "
        "banned new data centers > 10 MW (Aug 2026); New York's EO 62 pause on state permits for ≥ 50 MW is "
        "time-limited. Grid carbon (NYUP 110 vs NWPP 288 kg CO₂e/MWh) is already in the score, not an extra factor. "
        "Details: docs/01 and docs/CRITIQUE.")

    left, right = st.columns([3, 2])
    with left:
        st.markdown("#### Map — national score (top 20,000 cells) and finalists")
        lo, hi = top["S_G"].min(), top["S_G"].max()
        top = top.assign(c=((top["S_G"] - lo) / max(hi - lo, 1e-9) * 255).astype(int))
        pts = fin.head(5).assign(
            color=[[220, 30, 30, 255] if l == RECOMMENDED else [30, 30, 30, 230] for l in fin.head(5)["label"]],
            radius=[45000 if l == RECOMMENDED else 28000 for l in fin.head(5)["label"]],
            name=[f"{s} ({'RECOMMENDED' if l == RECOMMENDED else 'model #1' if l == MODEL_TOP else 'finalist'})"
                  for s, l in zip(fin.head(5)["site"], fin.head(5)["label"])])
        layers = [pdk.Layer("H3HexagonLayer", top, get_hexagon="h3_res6",
                            get_fill_color="[230 - c * 0.8, 230 - c * 0.35, 230 - c * 0.75, 170]",
                            pickable=False, extruded=False),
                  pdk.Layer("ScatterplotLayer", pts, get_position="[lon, lat]", get_fill_color="color",
                            get_radius="radius", pickable=True, stroked=True, get_line_color=[255, 255, 255],
                            line_width_min_pixels=2)]
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=40, longitude=-98, zoom=3.2),
                                 tooltip={"text": "{name}"}, map_style=None))
        st.caption("Red = recommended (Wyoming Co, NY). Black = other top-5 finalists. Hexagons: darker green = higher "
                   "national score (top 20,000 eligible cells).")
    with right:
        st.markdown("#### Top 5 finalists (res-7 refined)")
        t = fin.head(5)[["site", "S_G", "rank_G", "rank_A", "rank_pctnorm", "p_rank1_k100", "p_top5_k100",
                         "median_rank_k100"]].copy()
        t["role"] = fin.head(5)["label"].map({MODEL_TOP: "model #1", RECOMMENDED: "★ RECOMMENDED"}).fillna("")
        t = t.rename(columns={"site": "Site", "S_G": "Score (geo)", "rank_G": "Rank", "rank_A": "Rank (arith.)",
                              "rank_pctnorm": "Rank (percentile norm.)", "p_rank1_k100": "P(rank 1)",
                              "p_top5_k100": "P(top 5)", "median_rank_k100": "Median MC rank", "role": "Role"})
        t = t[["Role", "Site", "Score (geo)", "Rank", "P(rank 1)", "P(top 5)", "Median MC rank", "Rank (arith.)",
               "Rank (percentile norm.)"]]
        st.dataframe(t.round(3), hide_index=True, use_container_width=True)
        st.markdown("#### Robustness — 5,000 weight draws (Dirichlet κ=100)")
        st.bar_chart(fin.set_index("site")["p_rank1_k100"].rename("P(rank 1)"), height=220)
        st.caption(f"Wyoming Co stays top-5 in {rec['p_top5_k100']:.1%} of draws; King Co is #1 in "
                   f"{mod['p_rank1_k100']:.0%}.")

    st.markdown("#### Sustainability comparison — 300 MW IT, identical design, location effect only")
    lab = {imp["name"].iloc[0]: "Wyoming Co, NY", imp["name"].iloc[1]: "Loudoun Co, VA", imp["name"].iloc[2]: "CONUS average"}
    s = imp.assign(Site=imp["name"].map(lab)).set_index("Site")
    tab = pd.DataFrame({"Operational CO₂ (kt/yr)": s["co2_t"] / 1e3,
                        "CO₂ with 90 % 24/7 CFE (kt/yr)": s["co2_t_cfe90"] / 1e3,
                        "On-site water (thousand m³)": s["onsite_water_m3"] / 1e3,
                        "Grid water, hydro excl. (million m³)": s["offsite_water_m3"] / 1e6,
                        "Scarcity-weighted water (million m³-eq)": s["scarcity_weighted_m3"] / 1e6,
                        "PUE": s["pue"]})
    a, b = st.columns([3, 2])
    a.dataframe(tab.round(2), use_container_width=True)
    b.bar_chart(tab["Operational CO₂ (kt/yr)"], height=220)
    st.caption("Source: siteselect/impact.py → outputs/diagnostics/impact.csv. Average (location-based) emission "
               "rates; including hydro evaporation reverses the grid-water comparison (see docs/04, docs/CRITIQUE).")


# --------------------------------------------------------------------------- explore / re-weight view
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


def explore_view():
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
    wcfg = config.load("weights")
    P = scoring.pillar_scores(Vm, ft["w_norm"].to_numpy(), scoring.onehot(ft), wcfg["min_pillar_weight_observed"])
    S_A, S_G = scoring.aggregate(P, W, wcfg["epsilon"])
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

    st.title("Explore & re-weight (national screening, H3 res 6)")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader(f"Score map — {len(el):,} eligible H3 res-{RES} regions")
        show = el.head(20000).reset_index()
        lo, hi = show["score"].min(), show["score"].max()
        show["c"] = ((show["score"] - lo) / max(hi - lo, 1e-9) * 255).astype(int)
        layer = pdk.Layer("H3HexagonLayer", show, get_hexagon="h3",
                          get_fill_color="[230 - c * 0.8, 230 - c * 0.35, 230 - c * 0.75, 170]",
                          pickable=True, extruded=False)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(latitude=39, longitude=-97, zoom=3.3),
                                 tooltip={"text": "{h3}\nscore {score}\nrank {rank}"}, map_style=None))
    with c2:
        st.subheader("Top regions")
        from siteselect.candidates import nms
        top = nms(el.reset_index().rename(columns={"score": "S"}), score="S", pool_frac=0.05, radius_km=150,
                  max_regions=15)
        st.dataframe(top[["h3", "state", "lat", "lon", "S", "confidence"] + PILLARS].round(3), hide_index=True)
        pick = st.selectbox("Region detail", top["h3"])
        r = el.loc[pick]
        st.bar_chart(pd.Series({names[p]: r[p] for p in PILLARS}, name="pillar score"))
        raw = f.loc[pick, [c for c in ft.index if c in f]].astype(float).round(3)
        st.dataframe(raw.rename("raw value"))
    st.caption("National screening scores (res 6) — regions, not parcels. The final recommendation uses res-7 "
               "refinement + manual review; see the 'Final recommendation' view.")


# --------------------------------------------------------------------------- navigation
default = 1 if (st.query_params.get("view") == "explore" or "--explore" in sys.argv) else 0
view = st.sidebar.radio("View", VIEWS, index=default)
st.sidebar.caption("Open data · reproducible configs (config/*.yaml) · modular adapters (siteselect/adapters)")
if view == VIEWS[0]:
    final_view()
else:
    explore_view()
