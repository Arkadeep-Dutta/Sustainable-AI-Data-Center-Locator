"""CONUS H3 grid. Cells kept by centroid containment in the CONUS land mask (Census 1:500k states)."""
from __future__ import annotations

import zipfile

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Polygon

from .config import CRS_M, INTERIM, PROCESSED, RAW

NON_CONUS = {"02", "15", "60", "66", "69", "72", "78"}


def conus_states() -> gpd.GeoDataFrame:
    p = INTERIM / "conus_states.parquet"
    if p.exists():
        return gpd.read_parquet(p)
    g = gpd.read_file(f"zip://{RAW / 'cb_2023_us_state_500k.zip'}")
    g = g[~g["STATEFP"].isin(NON_CONUS)][["STATEFP", "STUSPS", "NAME", "geometry"]].to_crs(4326)
    g.to_parquet(p)
    return g


def conus_mask():
    return conus_states().union_all()


def cells(res: int, mask=None) -> pd.DataFrame:
    """DataFrame: h3, lat, lon, area_km2, state. Cached."""
    p = PROCESSED / f"grid_res{res}.parquet"
    if p.exists() and mask is None:
        return pd.read_parquet(p)
    st = conus_states()
    m = mask if mask is not None else st.union_all()
    # polyfill on a slightly buffered mask, then keep centroids inside the true mask
    ids = set(h3.geo_to_cells(m.buffer(0.05).__geo_interface__, res))
    ids = np.array(sorted(ids))
    ll = np.array([h3.cell_to_latlng(c) for c in ids])
    pts = gpd.GeoDataFrame({"h3": ids}, geometry=gpd.points_from_xy(ll[:, 1], ll[:, 0]), crs=4326)
    j = gpd.sjoin(pts, st[["STUSPS", "geometry"]], predicate="within", how="inner")
    j = j[~j.index.duplicated()]
    df = pd.DataFrame({"h3": j["h3"].to_numpy(), "lat": j.geometry.y.to_numpy(),
                       "lon": j.geometry.x.to_numpy(), "state": j["STUSPS"].to_numpy()})
    df["area_km2"] = [h3.cell_area(c, unit="km^2") for c in df["h3"]]
    if mask is None:
        df.to_parquet(p)
    return df


def to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    geoms = [Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in df["h3"]]
    return gpd.GeoDataFrame(df.copy(), geometry=geoms, crs=4326)


def centroids_m(df: pd.DataFrame) -> np.ndarray:
    from pyproj import Transformer
    t = Transformer.from_crs(4326, CRS_M, always_xy=True)
    x, y = t.transform(df["lon"].to_numpy(), df["lat"].to_numpy())
    return np.c_[x, y]
