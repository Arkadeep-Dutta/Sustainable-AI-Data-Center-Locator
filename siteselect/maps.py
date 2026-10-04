"""Static (matplotlib, slide-ready) and interactive (folium) maps from scores parquet."""
from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import grid
from .config import OUTPUTS, PILLARS, load

MAPS = OUTPUTS / "maps"


def _states():
    return grid.conus_states().to_crs(5070)


def static(s: pd.DataFrame, col: str, title: str, fname: str, cmap: str = "viridis",
           finalists: pd.DataFrame | None = None, mask_ineligible: bool = True, vmin=None, vmax=None) -> None:
    pts = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s["lon"], s["lat"]), crs=4326).to_crs(5070)
    fig, ax = plt.subplots(figsize=(12, 7.2), dpi=150)
    st = _states()
    st.plot(ax=ax, color="#eeeeee", edgecolor="none")
    show = pts if not mask_ineligible else pts[pts["eligible"]]
    if mask_ineligible:
        pts[~pts["eligible"]].plot(ax=ax, color="#d9d9d9", markersize=0.6, linewidth=0)
    show.plot(ax=ax, column=col, cmap=cmap, markersize=0.6, linewidth=0, legend=True,
              vmin=vmin, vmax=vmax, legend_kwds={"shrink": 0.6, "label": col})
    st.boundary.plot(ax=ax, color="white", linewidth=0.4)
    if finalists is not None and len(finalists):
        fp = gpd.GeoDataFrame(finalists, geometry=gpd.points_from_xy(finalists["lon"], finalists["lat"]), crs=4326).to_crs(5070)
        fp.plot(ax=ax, color="none", edgecolor="crimson", markersize=90, linewidth=1.6)
        for _, r in fp.iterrows():
            ax.annotate(str(r.get("label", r.get("region_id", ""))), (r.geometry.x, r.geometry.y),
                        xytext=(5, 5), textcoords="offset points", fontsize=8, color="crimson")
    ax.set_title(title, fontsize=13, loc="left")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(MAPS / fname, bbox_inches="tight")
    plt.close(fig)


def all_static(s: pd.DataFrame, finalists: pd.DataFrame | None = None, res: int = 6) -> None:
    names = load("weights")["pillar_names"]
    static(s, "S_G", f"Overall score (weighted geometric mean), H3 res {res}", "overall_SG.png", "viridis", finalists)
    for p in PILLARS:
        static(s, f"P_{p}", f"Pillar: {names[p]}", f"pillar_{p}.png", "viridis", None, vmin=0, vmax=1)
    s = s.copy()
    excl_cols = [c for c in s.columns if c.startswith("excl_")]
    s["excluded_by"] = np.select([s[c] for c in excl_cols], [i + 1 for i in range(len(excl_cols))], 0)
    static(s.assign(eligible=True), "excluded_by",
           "Hard-gate exclusions (0 = pass; " + ", ".join(f"{i+1}={c[5:]}" for i, c in enumerate(excl_cols)) + ")",
           "exclusions.png", "tab10", mask_ineligible=False)
    static(s.assign(eligible=True), "confidence", "Data confidence (share of model weight observed)",
           "confidence.png", "magma", mask_ineligible=False, vmin=0.5, vmax=1)


def interactive(s: pd.DataFrame, finalists: pd.DataFrame | None, fname: str = "national_interactive.html",
                top_n: int = 25000) -> None:
    """Folium map: top cells by S_G as H3 polygons + finalist markers (size-limited for load time)."""
    import folium
    import branca.colormap as cm
    el = s[s["eligible"]].nlargest(top_n, "S_G")
    g = grid.to_gdf(el.reset_index()[["h3", "lat", "lon", "S_G", "rank_G"] + [f"P_{p}" for p in PILLARS]])
    g = g.round(3)
    m = folium.Map(location=[39, -97], zoom_start=4, tiles="cartodbpositron")
    cmap = cm.linear.viridis.scale(float(g["S_G"].min()), float(g["S_G"].max()))
    cmap.caption = f"S_G (top {top_n} eligible cells)"
    folium.GeoJson(g.to_json(), name="score",
                   style_function=lambda f: {"fillColor": cmap(f["properties"]["S_G"]), "color": "none",
                                             "fillOpacity": 0.75},
                   tooltip=folium.GeoJsonTooltip(["h3", "S_G", "rank_G"] + [f"P_{p}" for p in PILLARS])).add_to(m)
    cmap.add_to(m)
    if finalists is not None:
        fg = folium.FeatureGroup("finalists")
        for _, r in finalists.iterrows():
            folium.Marker([r["lat"], r["lon"]], tooltip=str(r.get("label", r.get("region_id")))).add_to(fg)
        fg.add_to(m)
    folium.LayerControl().add_to(m)
    m.save(MAPS / fname)
