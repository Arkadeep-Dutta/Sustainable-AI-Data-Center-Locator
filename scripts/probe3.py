import requests
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
base = "https://services.arcgis.com/XG15cJAlne2vxtgt/ArcGIS/rest/services"
j = requests.get(base, params={"f": "json"}, headers=H, timeout=30).json()
names = [x["name"] for x in j["services"]]
print([n for n in names if ("Count" in n or "NRI" in n) and "Rating" not in n and "Annualized" not in n])
for n in [n for n in names if n in ("National_Risk_Index_Counties", "NRI_Counties", "National_Risk_Index_Census_Tracts")]:
    m = requests.get(f"{base}/{n}/FeatureServer/0", params={"f": "json"}, headers=H, timeout=30).json()
    f = [x["name"] for x in m.get("fields", [])]
    print(n, len(f), m.get("maxRecordCount"), [c for c in f if c.endswith(("_RISKS", "_EALS"))][:30], f[:12])
