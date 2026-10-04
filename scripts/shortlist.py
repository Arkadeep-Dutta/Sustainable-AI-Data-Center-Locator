"""Gate-3 shortlist table -> outputs/diagnostics/shortlist_res6.csv"""
import geopandas as gpd
import pandas as pd
from siteselect.config import PROCESSED, RAW, DIAG, PILLARS

c = pd.read_parquet(PROCESSED / "candidates_res6.parquet")
pct = pd.read_parquet(PROCESSED / "scores_res6_percentile.parquet")
f = pd.read_parquet(PROCESSED / "features_res6.parquet")
co = gpd.read_file(f"zip://{RAW / 'cb_2023_us_county_500k.zip'}")[["NAME", "STUSPS", "geometry"]].to_crs(4326)
pts = gpd.GeoDataFrame(c, geometry=gpd.points_from_xy(c.lon, c.lat), crs=4326)
j = gpd.sjoin(pts, co, how="left", predicate="within")
j = j[~j.index.duplicated()]
j["county"] = j["NAME"] + " Co, " + j["STUSPS"]
j["rank_pct_mode"] = pct.loc[j["h3"], "S_G"].rank(ascending=False).values  # placeholder overwritten below
pr = pct["S_G"].where(pct["eligible"]).rank(ascending=False, method="min")
j["rank_pctnorm"] = pr.reindex(j["h3"]).values
for k in ["ec_co2_rate", "wa_bws", "gi_dist_tx230_km", "egrid_subrgn"]:
    j[k] = f.loc[j["h3"], k].values
cols = ["region_id", "h3", "county", "lat", "lon", "S_G", "rank_G", "rank_A", "rank_pctnorm", "pool_cells_in_region"] + \
       [f"P_{p}" for p in PILLARS] + ["ec_co2_rate", "wa_bws", "gi_dist_tx230_km", "egrid_subrgn"]
out = j[cols].round(3)
out.to_csv(DIAG / "shortlist_res6.csv", index=False)
pd.set_option("display.width", 250)
print(out[["region_id", "county", "lat", "lon", "S_G", "rank_G", "rank_A", "rank_pctnorm", "pool_cells_in_region", "P_EC", "P_WA", "P_GI", "P_CE", "P_CR", "P_LM", "P_HR", "egrid_subrgn"]].to_string(index=False))
