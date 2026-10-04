import geopandas as gpd, pandas as pd
from siteselect.adapters.transmission import lines, CLASS_KV
g = gpd.read_parquet("data/raw/hifld_transmission.parquet")
v = pd.to_numeric(g["VOLTAGE"], errors="coerce")
print("rows", len(g), "| VOLTAGE<=0 or NaN:", int((v.isna() | (v <= 0)).sum()))
print("VOLT_CLASS where VOLTAGE invalid:", g.loc[v.isna() | (v <= 0), "VOLT_CLASS"].value_counts().to_dict())
print("VOLTAGE 200-229 count:", int(v.between(200, 229.9).sum()), "values:", v[v.between(200, 229.9)].value_counts().head(5).to_dict())
print("VOLT_CLASS 220-287 with VOLTAGE<230:", int(((g.VOLT_CLASS == "220-287") & (v < 230) & (v > 0)).sum()))
print("STATUS:", g["STATUS"].value_counts().to_dict())
L = lines()
print("kept", len(L), "| kv>=230:", int((L.kv >= 230).sum()), "| kv>=345:", int((L.kv >= 345).sum()), "| kv NaN:", int(L.kv.isna().sum()))
print("DC lines:", int((g.VOLT_CLASS == "DC").sum()), g.loc[g.VOLT_CLASS == "DC", "VOLTAGE"].tolist())
