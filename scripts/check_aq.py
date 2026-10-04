import geopandas as gpd
from siteselect.adapters.aqueduct import GDB, BBOX
b = gpd.read_file(GDB, layer="baseline_annual", bbox=BBOX, columns=["bws_raw", "bws_cat", "bws_label"], ignore_geometry=True)
print(len(b), (b.bws_raw >= 9999).sum(), (b.bws_raw > 5).sum(), (b.bws_raw < 0).sum())
print(b[b.bws_raw >= 9999][["bws_cat", "bws_label"]].value_counts().head())
print(b[b.bws_raw > 1][["bws_cat", "bws_label"]].value_counts().head())
print(b.bws_raw[(b.bws_raw > 1) & (b.bws_raw < 9999)].describe().round(2).to_dict())
