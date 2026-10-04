"""Land suitability: Annual NLCD 2023 (30 m) + PAD-US 4.1 GAP 1-2 -> per-cell fractions.

1. NLCD decimated by nearest sampling to `px` m (default 240 m; unbiased class-fraction sample:
   ~600 samples per res-6 cell). Res-7 refinement can use px=30 on windows.
2. PAD-US GAP status 1-2 (Fee/Easement/Designation; not Marine/Proclamation) rasterized on the same grid.
3. Code raster: 1 suitable & unprotected | 2 protected (any cover) | 3 open water/wetland, unprotected
   | 4 other land (forest, high-intensity developed, ice) | 0 nodata.
   Suitable NLCD classes: 21,22 developed open/low; 31 barren; 52 shrub; 71 grassland; 81 pasture; 82 crops.
4. exactextract 'frac' over H3 polygons (in raster CRS).
"""
from __future__ import annotations

import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import rasterio
from rasterio import features as rfeat
from rasterio.enums import Resampling

from ..config import INTERIM, RAW
from .. import grid

SUITABLE = [21, 22, 31, 52, 71, 81, 82]
WET = [11, 90, 95]
NLCD_TIF = INTERIM / "Annual_NLCD_LndCov_2023_CU_C1V1.tif"


def _nlcd_path():
    if not NLCD_TIF.exists():
        with zipfile.ZipFile(RAW / "Annual_NLCD_LndCov_2023_CU_C1V1.zip") as z:
            z.extract("Annual_NLCD_LndCov_2023_CU_C1V1.tif", INTERIM)
    return NLCD_TIF


def padus_gap12(crs) -> gpd.GeoDataFrame:
    p = INTERIM / "padus_gap12.parquet"
    if p.exists():
        return gpd.read_parquet(p).to_crs(crs)
    t = pq.read_table(RAW / "padus41_combined.parquet", columns=["GAP_Sts", "FeatClass", "SHAPE"],
                      filters=[("GAP_Sts", "in", ["1", "2"]),
                               ("FeatClass", "in", ["Fee", "Easement", "Designation"])]).to_pandas()
    geom = gpd.GeoSeries.from_wkb(t["SHAPE"])
    x0 = geom.iloc[:200].bounds["minx"].abs().max()
    src_crs = 4326 if x0 <= 180 else "ESRI:102039"     # mirror may keep USA Contiguous Albers
    g = gpd.GeoDataFrame(t[["GAP_Sts", "FeatClass"]], geometry=geom, crs=src_crs)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    g.to_parquet(p)
    return g.to_crs(crs)


def code_raster(px: int = 240) -> str:
    out = INTERIM / f"land_codes_{px}m.tif"
    if out.exists():
        return str(out)
    with rasterio.open(_nlcd_path()) as src:
        f = px / src.res[0]
        h, w = int(src.height / f), int(src.width / f)
        lc = src.read(1, out_shape=(h, w), resampling=Resampling.nearest)
        tr = src.transform * src.transform.scale(src.width / w, src.height / h)
        crs, nod = src.crs, src.nodata
    pad = padus_gap12(crs)
    prot = rfeat.rasterize(((geom, 1) for geom in pad.geometry), out_shape=lc.shape, transform=tr,
                           fill=0, dtype="uint8")
    code = np.full(lc.shape, 4, np.uint8)
    code[np.isin(lc, SUITABLE)] = 1
    code[np.isin(lc, WET)] = 3
    code[prot == 1] = 2
    code[(lc == 0) | (lc == (nod if nod is not None else 250)) | (lc == 250)] = 0
    prof = dict(driver="GTiff", height=h, width=w, count=1, dtype="uint8", crs=crs, transform=tr,
                nodata=0, compress="deflate", tiled=True)
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(code, 1)
    return str(out)


def build(cells: pd.DataFrame, res: int, px: int = 240) -> pd.DataFrame:
    from exactextract import exact_extract
    r = code_raster(px)
    with rasterio.open(r) as src:
        crs = src.crs
    polys = grid.to_gdf(cells[["h3", "lat", "lon", "area_km2"]]).to_crs(crs)
    res_df = exact_extract(r, polys, ["unique", "frac"], include_cols=["h3"], output="pandas")
    fr = pd.DataFrame(0.0, index=res_df.index, columns=[1, 2, 3, 4])
    for i, (u, f) in enumerate(zip(res_df["unique"], res_df["frac"])):
        for k, v in zip(np.atleast_1d(u), np.atleast_1d(f)):
            if int(k) in fr.columns:
                fr.iat[i, int(k) - 1] = v
    valid = fr.sum(1)   # fractions are of valid (non-nodata) pixels
    out = pd.DataFrame(index=cells.index)
    a = cells["area_km2"].to_numpy()
    out["lm_suitable_km2"] = np.where(valid > 0, fr[1].to_numpy() * a, np.nan)
    out["lm_protected_frac"] = np.where(valid > 0, fr[2].to_numpy(), np.nan)
    out["lm_wet_frac"] = np.where(valid > 0, fr[3].to_numpy(), np.nan)
    out["lm_unbuildable_frac"] = out["lm_protected_frac"] + out["lm_wet_frac"]
    for c in ["lm_suitable_km2", "lm_protected_frac", "lm_wet_frac"]:
        out[f"cov_{c}"] = out[c].notna()
    return out
