"""Machine-readable outputs + maps.

outputs/rankings.csv          national res-6 eligible cells ranked by S_G (pillars, confidence, ranks)
outputs/finalists_rankings.csv res-7 finalists with robustness statistics
outputs/candidates.geojson    25 national candidate regions + res-7 finalists (H3 polygons, properties)
outputs/maps/*                static PNGs + interactive HTML
"""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from . import grid, maps
from .config import DIAG, OUTPUTS, PILLARS, PROCESSED


def run() -> None:
    s = pd.read_parquet(PROCESSED / "scores_res6.parquet")
    cols = ["lat", "lon", "state", "S_G", "S_A", "rank_G", "rank_A", "confidence"] + [f"P_{p}" for p in PILLARS]
    r = s[s["eligible"]].sort_values("rank_G")[cols].round(4)
    r.index.name = "h3_res6"
    r.to_csv(OUTPUTS / "rankings.csv")
    sl = pd.read_csv(DIAG / "shortlist_res6.csv")
    fin = pd.read_csv(DIAG / "finalists_robustness.csv")
    fin.to_csv(OUTPUTS / "finalists_rankings.csv", index=False)
    a = grid.to_gdf(sl.rename(columns={"region_id": "candidate_region"}))
    a["kind"] = "national_candidate_res6"
    b = grid.to_gdf(fin)
    b["kind"] = "finalist_site_res7"
    g = pd.concat([a, b], ignore_index=True)
    g = gpd.GeoDataFrame(g, geometry="geometry", crs=4326)
    g.to_file(OUTPUTS / "candidates.geojson", driver="GeoJSON")
    # maps
    sl["label"] = sl["region_id"]
    maps.all_static(s, sl)
    f = fin.assign(label=fin["label"] + " " + fin["state"])
    maps.static(s, "S_G", "Finalist sites (res-7 refined) on national score", "finalists.png", "viridis", f)
    maps.interactive(s, f)
    s7 = pd.read_parquet(PROCESSED / "scores_res7_refine.parquet")
    for rid in s7["region_id"].unique():
        _region_map(s7[s7["region_id"] == rid], fin[fin["region_id"] == rid], rid)


def _region_map(s7: pd.DataFrame, f: pd.DataFrame, rid: int) -> None:
    import matplotlib.pyplot as plt
    g = grid.to_gdf(s7.reset_index()[["h3", "lat", "lon", "S_G", "eligible"]]).to_crs(5070)
    fig, ax = plt.subplots(figsize=(6, 6), dpi=130)
    g[~g["eligible"]].plot(ax=ax, color="#d0d0d0", edgecolor="none")
    g[g["eligible"]].plot(ax=ax, column="S_G", cmap="viridis", legend=True, edgecolor="none",
                          legend_kwds={"shrink": 0.6, "label": "S_G (res 7)"})
    if len(f):
        fp = gpd.GeoDataFrame(f, geometry=gpd.points_from_xy(f["lon"], f["lat"]), crs=4326).to_crs(5070)
        fp.plot(ax=ax, color="none", edgecolor="crimson", markersize=160, linewidth=2)
    ax.set_title(f"Region R{rid} — res-7 refinement (grey = fails local gates)", fontsize=10, loc="left")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(maps.MAPS / f"refine_R{rid}.png")
    plt.close(fig)


if __name__ == "__main__":
    run()
