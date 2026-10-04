import geopandas as gpd, pandas as pd
g = gpd.read_parquet("data/raw/hifld_transmission.parquet")
print(g["STATUS"].value_counts(dropna=False).to_string())
print(g["VOLT_CLASS"].value_counts(dropna=False).to_string())
kv = pd.to_numeric(g["VOLTAGE"], errors="coerce")
print("kv>=230:", (kv >= 230).sum(), "kv<=0:", (kv <= 0).sum())
print(pd.crosstab(g["STATUS"], kv >= 230))
s = pd.read_csv("outputs/diagnostics/sanity_markets_res6.csv")
print(s[["market", "gi_dist_tx230_km", "ec_co2_rate", "wa_bws", "lm_suitable_km2", "gate_pass", "rank_G", "pct_rank"]].to_string())
