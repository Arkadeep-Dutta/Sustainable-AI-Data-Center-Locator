"""Res-7 local refinement of Gate-3-approved regions. Features recomputed directly (no interpolation
of national scores). Site-scale additions:
  * NLCD at native 30 m (windowed), PAD-US GAP 1-2 at 30 m;
  * USGS 3DEP slope (exportImage, 30 m, EPSG:5070) -> buildable requires slope <= 10 %;
  * FEMA NFHL Special Flood Hazard Area (SFHA_TF='T', layer 28) -> cr_sfha_frac + local gate G3.
Percentile/winsor features are normalised against the NATIONAL res-6 eligible reference so scores
are comparable across regions.

python -m siteselect.refine
"""
from __future__ import annotations

import io
import time

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio import features as rfeat
from rasterio.windows import from_bounds

from . import config, gates, grid, scoring
from .adapters import land
from .config import DIAG, INTERIM, PROCESSED
from .features import assemble

H = {"User-Agent": "Mozilla/5.0 siteselect-research"}
REGIONS = [1, 2, 3, 5, 7, 9, 11, 19]   # Gate 3 approved (shortlist_res6.csv region_id)
RADIUS_KM = 50
SLOPE_MAX_PCT = 10.0
NFHL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
DEP = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage"


def region_cells(lat: float, lon: float, rid: int) -> pd.DataFrame:
    k = int(np.ceil(RADIUS_KM / 2.3))
    ids = list(h3.grid_disk(h3.latlng_to_cell(lat, lon, 7), k))
    ll = np.array([h3.cell_to_latlng(c) for c in ids])
    pts = gpd.GeoDataFrame({"h3": ids}, geometry=gpd.points_from_xy(ll[:, 1], ll[:, 0]), crs=4326)
    st = grid.conus_states()
    j = gpd.sjoin(pts, st[["STUSPS", "geometry"]], predicate="within", how="inner")
    j = j[~j.index.duplicated()]
    return pd.DataFrame({"h3": j["h3"].to_numpy(), "lat": j.geometry.y.to_numpy(), "lon": j.geometry.x.to_numpy(),
                         "state": j["STUSPS"].to_numpy(),
                         "area_km2": [h3.cell_area(c, unit="km^2") for c in j["h3"]], "region_id": rid})


def _nfhl(bbox4326) -> gpd.GeoDataFrame:
    p = dict(where="SFHA_TF='T'", geometry=",".join(map(str, bbox4326)), geometryType="esriGeometryEnvelope",
             inSR=4326, spatialRel="esriSpatialRelIntersects", f="json")
    for a in range(6):   # service errors must never be read as "no floodplain"
        try:
            js = requests.get(NFHL, params={**p, "returnIdsOnly": "true"}, headers=H, timeout=120).json()
            if "objectIds" in js:
                break
        except Exception:
            pass
        time.sleep(5 * (a + 1))
    else:
        raise RuntimeError("NFHL id query failed")
    ids = js["objectIds"] or []
    frames, todo = [], [ids[i:i + 200] for i in range(0, len(ids), 200)]
    while todo:
        ch = todo.pop(0)
        for a in range(4):
            try:
                r = requests.post(NFHL, data={"objectIds": ",".join(map(str, ch)), "outFields": "FLD_ZONE",
                                              "f": "geojson", "outSR": 4326, "maxAllowableOffset": 0.0001},
                                  headers=H, timeout=180)
                js = r.json(); break
            except Exception:
                time.sleep(3 * (a + 1))
        else:
            raise RuntimeError("NFHL page failed")
        if len(js.get("features", [])) < len(ch) and len(ch) > 1:
            todo[:0] = [ch[:len(ch) // 2], ch[len(ch) // 2:]]
            continue
        if js.get("features"):
            frames.append(gpd.GeoDataFrame.from_features(js["features"], crs=4326))
    g = pd.concat(frames, ignore_index=True) if frames else gpd.GeoDataFrame(geometry=[], crs=4326)
    return gpd.GeoDataFrame(g, crs=4326), len(ids)


def _slope_pct(bounds, shape, crs_wkt) -> np.ndarray:
    xmin, ymin, xmax, ymax = bounds
    h, w = shape
    tiles = np.zeros(shape, np.float32)
    step = 1500
    for i0 in range(0, h, step):
        for j0 in range(0, w, step):
            hh, ww = min(step, h - i0), min(step, w - j0)
            px = (xmax - xmin) / w
            bb = (xmin + j0 * px, ymax - (i0 + hh) * px, xmin + (j0 + ww) * px, ymax - i0 * px)
            for a in range(5):
                try:
                    r = requests.get(DEP, params={"bbox": ",".join(map(str, bb)), "bboxSR": 5070,
                                                  "imageSR": 5070, "size": f"{ww},{hh}", "format": "tiff",
                                                  "pixelType": "F32", "interpolation": "RSP_BilinearInterpolation",
                                                  "f": "image"}, headers=H, timeout=300)
                    r.raise_for_status()
                    break
                except Exception:
                    if a == 4:
                        raise
                    time.sleep(5 * (a + 1))
            with rasterio.open(io.BytesIO(r.content)) as s:
                tiles[i0:i0 + hh, j0:j0 + ww] = s.read(1)
    px = (xmax - xmin) / w
    gy, gx = np.gradient(tiles.astype(float), px)
    return (np.hypot(gx, gy) * 100).astype(np.float32)


def land_local(cells: pd.DataFrame, rid: int, pad: gpd.GeoDataFrame) -> pd.DataFrame:
    from exactextract import exact_extract
    with rasterio.open(land._nlcd_path()) as src:
        polys = grid.to_gdf(cells[["h3"]].assign(lat=cells.lat, lon=cells.lon)).to_crs(src.crs)
        b = polys.total_bounds + np.array([-300, -300, 300, 300])
        win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        lc = src.read(1, window=win)
        tr = src.window_transform(win)
        crs = src.crs
    bounds = rasterio.windows.bounds(rasterio.windows.Window(0, 0, lc.shape[1], lc.shape[0]), tr)
    pr = pad.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
    prot = rfeat.rasterize(((g, 1) for g in pr.geometry), out_shape=lc.shape, transform=tr, fill=0, dtype="uint8") \
        if len(pr) else np.zeros(lc.shape, np.uint8)
    bb4326 = gpd.GeoSeries.from_xy([bounds[0], bounds[2]], [bounds[1], bounds[3]], crs=crs).to_crs(4326)
    nf, n_ids = _nfhl((bb4326.x.min(), bb4326.y.min(), bb4326.x.max(), bb4326.y.max()))
    sfha = rfeat.rasterize(((g, 1) for g in nf.to_crs(crs).geometry if g is not None), out_shape=lc.shape,
                           transform=tr, fill=0, dtype="uint8") if len(nf) else np.zeros(lc.shape, np.uint8)
    slope = _slope_pct(bounds, lc.shape, crs)
    code = np.full(lc.shape, 4, np.uint8)
    code[np.isin(lc, land.SUITABLE) & (slope <= SLOPE_MAX_PCT)] = 1
    code[(code == 1) & (sfha == 1)] = 5                # suitable but in SFHA
    code[np.isin(lc, land.WET)] = 3
    code[prot == 1] = 2
    code[(lc == 0) | (lc == 250)] = 0
    prof = dict(driver="GTiff", height=lc.shape[0], width=lc.shape[1], count=1, dtype="uint8", crs=crs,
                transform=tr, nodata=0, compress="deflate")
    paths = {}
    for name, arr, dt in [("code", code, "uint8"), ("sfha", sfha, "uint8"), ("slope", slope, "float32")]:
        p = INTERIM / f"refine_r{rid}_{name}.tif"
        with rasterio.open(p, "w", **{**prof, "dtype": dt, "nodata": None if name != "code" else 0}) as d:
            d.write(arr.astype(dt), 1)
        paths[name] = str(p)
    polys = polys.assign(h3=cells["h3"].to_numpy())
    ex = exact_extract(paths["code"], polys, ["unique", "frac"], include_cols=["h3"], output="pandas")
    fr = np.zeros((len(ex), 5))
    for i, (u, f) in enumerate(zip(ex["unique"], ex["frac"])):
        for k, v in zip(np.atleast_1d(u), np.atleast_1d(f)):
            if 1 <= int(k) <= 5:
                fr[i, int(k) - 1] = v
    sf = exact_extract(paths["sfha"], polys, ["mean"], output="pandas")["mean"].to_numpy()
    sl = exact_extract(paths["slope"], polys, ["median"], output="pandas")["median"].to_numpy()
    a = cells["area_km2"].to_numpy()
    out = pd.DataFrame(index=cells.index)
    out["lm_suitable_km2"] = fr[:, 0] * a
    out["lm_protected_frac"] = fr[:, 1]
    out["lm_wet_frac"] = fr[:, 2]
    out["lm_unbuildable_frac"] = fr[:, 1] + fr[:, 2]
    out["cr_sfha_frac"] = sf if n_ids else np.nan
    out["slope_median_pct"] = sl
    for c in ["lm_suitable_km2", "lm_protected_frac", "lm_wet_frac"]:
        out[f"cov_{c}"] = True
    out["cov_cr_sfha_frac"] = bool(n_ids)
    out["nfhl_polys_region"] = n_ids
    return out


def run(regions=REGIONS) -> pd.DataFrame:
    sl = pd.read_csv(DIAG / "shortlist_res6.csv").set_index("region_id")
    cells = pd.concat([region_cells(sl.at[r, "lat"], sl.at[r, "lon"], r) for r in regions], ignore_index=True)
    cells = cells.drop_duplicates("h3").reset_index(drop=True)
    cells.to_parquet(PROCESSED / "grid_res7_refine.parquet")
    # regional / vector adapters recomputed on res-7 centroids
    f = assemble(7, only=["egrid", "aqueduct", "noaa", "acs", "nri", "transmission"], cells=cells, tag="_refine")
    pad = gpd.read_parquet(INTERIM / "padus_gap12.parquet")
    with rasterio.open(land._nlcd_path()) as src:
        pad = pad.to_crs(src.crs)
    parts = []
    for r in regions:
        t = time.time()
        c = cells[cells["region_id"] == r]
        cache = INTERIM / f"refine_land_r{r}.parquet"
        if cache.exists():
            lo = pd.read_parquet(cache)
        else:
            lo = land_local(c, r, pad)
            lo.index = c["h3"].to_numpy()
            lo.to_parquet(cache)
        parts.append(lo)
        print(f"region {r}: {len(c)} cells, land/slope/flood {time.time() - t:.0f}s", flush=True)
    lo = pd.concat(parts)
    f = f.drop(columns=[c for c in lo.columns if c in f.columns]).join(lo)
    f["region_id"] = cells.set_index("h3")["region_id"]
    f.to_parquet(PROCESSED / "features_res7_refine.parquet")
    return f


def land_to_res6_scale(x, site=(0.5, 2.0), national=(2.0, 15.0)):
    """Map res-7 site-scale land sufficiency (v=0 at 0.5 km2, v=1 at 2 km2) onto the res-6 breakpoints
    (2 -> 15 km2) so the single registered linear value function applies at both resolutions."""
    (a0, a1), (b0, b1) = site, national
    return b0 + (x - a0) * (b1 - b0) / (a1 - a0)


def score_local(mode: str = "physical") -> pd.DataFrame:
    """Local gates + MCDA with national reference population for relative value functions."""
    f7 = pd.read_parquet(PROCESSED / "features_res7_refine.parquet")
    f6 = pd.read_parquet(PROCESSED / "features_res6.parquet")
    g6 = gates.apply(f6, 6)
    g7 = gates.apply(f7, 7, level="local")
    f7s = f7.copy()
    f7s["lm_suitable_km2"] = land_to_res6_scale(f7["lm_suitable_km2"])
    comb = pd.concat([f6.assign(_n=True), f7s.assign(_n=False)])
    ref = pd.concat([g6["gate_pass"], pd.Series(False, index=f7.index)])
    s = scoring.score(comb, ref, mode=mode)
    s = s[~comb["_n"].to_numpy()]
    s.index = f7.index
    s["gate_pass"] = g7["gate_pass"]
    s["eligible"] = s["pillars_complete"] & g7["gate_pass"] & \
        (s["confidence"] >= config.load("weights")["confidence_threshold"])
    s["rank_G"] = s["S_G"].where(s["eligible"]).rank(ascending=False, method="min")
    s["rank_A"] = s["S_A"].where(s["eligible"]).rank(ascending=False, method="min")
    out = pd.concat([f7[["lat", "lon", "state", "region_id"]], g7.drop(columns="gate_pass"), s], axis=1)
    out.to_parquet(PROCESSED / f"scores_res7_refine{'' if mode == 'physical' else '_' + mode}.parquet")
    return out


if __name__ == "__main__":
    run()
    o = score_local()
    score_local("percentile")
    print(f"res7 refine: {len(o)} cells, eligible {int(o['eligible'].sum())}")
