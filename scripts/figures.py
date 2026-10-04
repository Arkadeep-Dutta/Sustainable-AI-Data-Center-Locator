"""Slide figures -> outputs/maps/fig_*.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import h3
from siteselect.config import DIAG, PROCESSED, PILLARS, load

M = "outputs/maps/"
names = load("weights")["pillar_names"]
cty = pd.read_csv(DIAG / "finalists_county.csv").set_index("label")["county"]
# 1. rank distribution under Dirichlet weight uncertainty (kappa=100)
h = pd.read_csv(DIAG / "finalists_rank_hist_k100.csv", index_col=0)
fig, ax = plt.subplots(figsize=(9, 4.5), dpi=150)
bottom = np.zeros(h.shape[1])
cols = plt.cm.viridis(np.linspace(0, 0.9, len(h)))
for i, (rank, row) in enumerate(h.iterrows()):
    ax.bar([f"{l}\n{cty[l]}" for l in h.columns], row.values, bottom=bottom, color=cols[i], label=f"rank {rank}")
    bottom += row.values
ax.set_ylabel("share of 5,000 weight draws")
ax.set_title("Rank distribution of finalists under weight uncertainty (Dirichlet κ=100 + feature jitter)", loc="left", fontsize=10)
ax.legend(ncol=8, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.28))
plt.xticks(fontsize=7)
fig.tight_layout(); fig.savefig(M + "fig_robustness_ranks.png"); plt.close(fig)
# 2. pillar comparison: R2 (recommended), R1 (model winner), Loudoun (res 6)
s7 = pd.read_parquet(PROCESSED / "scores_res7_refine.parquet")
s6 = pd.read_parquet(PROCESSED / "scores_res6.parquet")
fin = pd.read_csv(DIAG / "finalists_robustness.csv").set_index("label")
rows = {"Wyoming Co NY (recommended)": s7.loc[fin.at["R2", "h3"]], "King Co WA (model #1)": s7.loc[fin.at["R1", "h3"]],
        "Loudoun Co VA (benchmark)": s6.loc[h3.latlng_to_cell(39.08, -77.65, 6)]}
fig, ax = plt.subplots(figsize=(9, 4.5), dpi=150)
x = np.arange(7); w = 0.27
for i, (k, r) in enumerate(rows.items()):
    ax.bar(x + (i - 1) * w, [r[f"P_{p}"] for p in PILLARS], w, label=k, color=["#2a9d8f", "#577590", "#bbbbbb"][i])
ax.set_xticks(x, [names[p] for p in PILLARS], fontsize=8)
ax.set_ylim(0, 1.05); ax.set_ylabel("pillar score (0-1)")
ax.set_title("Pillar scores: recommended site vs model #1 vs Loudoun", loc="left", fontsize=10)
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(M + "fig_pillars_compare.png"); plt.close(fig)
# 3. impact comparison
imp = pd.read_csv(DIAG / "impact.csv").iloc[:3]
fig, axs = plt.subplots(1, 3, figsize=(11, 3.6), dpi=150)
lab = ["Wyoming Co NY", "Loudoun VA", "CONUS avg"]
for ax, col, t, sc in zip(axs, ["co2_t", "offsite_water_m3", "scarcity_weighted_m3"],
                          ["Operational CO₂ (kt/yr, location-based)", "Grid water consumed (Mm³/yr, hydro excl.)",
                           "Scarcity-weighted water (Mm³-eq/yr)"], [1e3, 1e6, 1e6]):
    ax.bar(lab, imp[col] / sc, color=["#2a9d8f", "#bbbbbb", "#888888"])
    ax.set_title(t, fontsize=9); ax.tick_params(labelsize=8)
fig.suptitle("300 MW IT, identical DLC + dry-cooling design; differences are due to location", fontsize=9)
fig.tight_layout(); fig.savefig(M + "fig_impact.png"); plt.close(fig)
