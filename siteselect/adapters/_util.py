"""Shared spatial helpers for adapters (all metric work in EPSG:5070)."""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.signal import fftconvolve
from scipy.spatial import cKDTree

from ..config import CRS_M

_T = Transformer.from_crs(4326, CRS_M, always_xy=True)


def xy_m(lon, lat) -> np.ndarray:
    x, y = _T.transform(np.asarray(lon, float), np.asarray(lat, float))
    return np.c_[x, y]


def points_in_polygons(cells: pd.DataFrame, polys: gpd.GeoDataFrame, cols: list[str]) -> pd.DataFrame:
    """Attach polygon attributes to cell centroids (first match). Unmatched -> NaN."""
    pts = gpd.GeoDataFrame(index=cells.index, geometry=gpd.points_from_xy(cells["lon"], cells["lat"]), crs=4326)
    j = gpd.sjoin(pts, polys.to_crs(4326)[cols + ["geometry"]], predicate="within", how="left")
    j = j[~j.index.duplicated()]
    return j[cols].reindex(cells.index)


def nearest_values(cells: pd.DataFrame, src_xy: np.ndarray, src_vals: pd.DataFrame,
                   max_km: float | None = None) -> tuple[pd.DataFrame, np.ndarray]:
    tree = cKDTree(src_xy)
    d, i = tree.query(xy_m(cells["lon"], cells["lat"]))
    out = src_vals.iloc[i].set_index(cells.index)
    if max_km is not None:
        out[d / 1000 > max_km] = np.nan
    return out, d / 1000


def idw(cells: pd.DataFrame, src_xy: np.ndarray, vals: np.ndarray, k: int = 8, power: float = 2.0) -> np.ndarray:
    tree = cKDTree(src_xy)
    d, i = tree.query(xy_m(cells["lon"], cells["lat"]), k=k)
    d = np.maximum(d, 1.0)
    w = 1.0 / d ** power
    return (w * vals[i]).sum(1) / w.sum(1)


class DiscSum:
    """Sum of point values within radius R of query points via raster FFT convolution.
    Pixel size trades accuracy vs speed; error ~ pixel/R at the disc edge."""

    def __init__(self, pixel_km: float, bounds=(-2.40e6, 0.20e6, 2.30e6, 3.20e6)):
        self.px = pixel_km * 1000.0
        self.x0, self.y0, x1, y1 = bounds
        self.nx = int(np.ceil((x1 - self.x0) / self.px))
        self.ny = int(np.ceil((y1 - self.y0) / self.px))

    def _ij(self, xy):
        i = np.clip(((xy[:, 1] - self.y0) / self.px).astype(int), 0, self.ny - 1)
        j = np.clip(((xy[:, 0] - self.x0) / self.px).astype(int), 0, self.nx - 1)
        return i, j

    def grid(self, xy: np.ndarray, vals: np.ndarray) -> np.ndarray:
        g = np.zeros((self.ny, self.nx))
        i, j = self._ij(xy)
        np.add.at(g, (i, j), vals)
        return g

    def disc(self, g: np.ndarray, radius_km: float) -> np.ndarray:
        r = int(np.ceil(radius_km * 1000 / self.px))
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        k = ((xx ** 2 + yy ** 2) * self.px ** 2 <= (radius_km * 1000) ** 2).astype(float)
        return np.maximum(fftconvolve(g, k, mode="same"), 0.0)

    def sample(self, conv: np.ndarray, qxy: np.ndarray) -> np.ndarray:
        i, j = self._ij(qxy)
        return conv[i, j]
