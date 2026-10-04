import requests
H = {"User-Agent": "Mozilla/5.0 siteselect-research"}
u = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28"
for url in [u, "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28"]:
    try:
        r = requests.get(url, params={"f": "json"}, headers=H, timeout=60); j = r.json()
        print(url[:60], r.status_code, j.get("name"), j.get("maxRecordCount"), [f["name"] for f in j.get("fields", [])][:12])
        c = requests.get(url + "/query", params={"where": "SFHA_TF='T'", "geometry": "-122.1,47.1,-121.8,47.3",
            "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
            "returnCountOnly": "true", "f": "json"}, headers=H, timeout=60).json(); print(c)
    except Exception as e:
        print(url[:60], "ERR", type(e).__name__, str(e)[:100])
e = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"
j = requests.get(e, params={"f": "json"}, headers=H, timeout=60).json()
print("3DEP", j.get("maxImageWidth"), j.get("maxImageHeight"), j.get("pixelSizeX"))
r = requests.get(e + "/exportImage", params={"bbox": "-122.2,47.0,-121.7,47.4", "bboxSR": 4326, "imageSR": 5070,
    "size": "500,500", "format": "tiff", "pixelType": "F32", "f": "image"}, headers=H, timeout=120)
print("3DEP export", r.status_code, r.headers.get("Content-Type"), len(r.content))
