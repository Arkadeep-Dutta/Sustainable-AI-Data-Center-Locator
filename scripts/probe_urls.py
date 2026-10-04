"""HEAD-probe candidate dataset URLs; print status + size (MB). Usage: python scripts/probe_urls.py"""
import sys
import requests

URLS = sys.argv[1:] or [
    "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip",
    "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip",
    "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Table_Counties/NRI_Table_Counties.zip",
    "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Table_CensusTracts/NRI_Table_CensusTracts.zip",
    "https://files.wri.org/aqueduct/aqueduct-4-0-water-risk-data.zip",
    "https://data.bls.gov/cew/data/files/2023/csv/2023_annual_by_area.zip",
    "https://www.ncei.noaa.gov/data/normals-annualseasonal/1991-2020/archive/us-climate-normals_1991-2020_v1.0.1_annualseasonal_multivariate_by-station_c20230404.tar.gz",
    "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Electric_Power_Transmission_Lines/FeatureServer/0?f=json",
    "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Electric_Substations/FeatureServer/0?f=json",
    "https://api.census.gov/data/2023/acs/acs5?get=NAME,B01001_001E&for=state:01",
]
H = {"User-Agent": "Mozilla/5.0 siteselect-research"}
for u in URLS:
    try:
        r = requests.head(u, allow_redirects=True, timeout=30, headers=H)
        if r.status_code >= 400 or "arcgis" in u or "api.census" in u:
            r = requests.get(u, timeout=30, headers=H, stream=True)
            snippet = r.raw.read(200).decode("utf-8", "ignore").replace("\n", " ")[:120]
        else:
            snippet = ""
        mb = int(r.headers.get("Content-Length", 0)) / 1e6
        print(f"{r.status_code} {mb:8.1f}MB {u[:110]} {snippet}")
    except Exception as e:
        print(f"ERR {type(e).__name__} {u[:110]}")
