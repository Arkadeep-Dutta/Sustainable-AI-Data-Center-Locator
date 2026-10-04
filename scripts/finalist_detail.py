import geopandas as gpd, pandas as pd
from siteselect.config import PROCESSED, RAW, DIAG
pd.set_option("display.width", 250)
t = pd.read_csv(DIAG / "finalists_robustness.csv")
f = pd.read_parquet(PROCESSED / "features_res7_refine.parquet").loc[t["h3"]]
co = gpd.read_file(f"zip://{RAW / 'cb_2023_us_county_500k.zip'}")[["NAME", "STUSPS", "geometry"]]
p = gpd.GeoDataFrame(t[["label", "h3"]], geometry=gpd.points_from_xy(t.lon, t.lat), crs=4326)
j = gpd.sjoin(p, co.to_crs(4326), how="left", predicate="within")
t["county"] = (j["NAME"] + " Co, " + j["STUSPS"]).values
cols = ["ec_co2_rate", "ec_clean_share", "ec_pue", "wa_bws", "wa_bws_2050", "wa_grid_water", "gi_dist_tx230_km",
        "gi_dist_tx345_km", "ce_workforce_80km", "ce_popdens_5km", "lm_suitable_km2", "slope_median_pct",
        "cr_sfha_frac", "hdd65", "cdd65", "egrid_subrgn"]
d = pd.concat([t[["label", "county"]].reset_index(drop=True), f[cols].reset_index(drop=True)], axis=1)
d.to_csv(DIAG / "finalists_detail.csv", index=False)
print(d.round(2).to_string(index=False))
t[["label", "county"]].to_csv(DIAG / "finalists_county.csv", index=False)
