import requests
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "*/*"}
base = "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/"
for s in ["Electric_Power_Transmission_Lines", "Electric_Substations"]:
    u = base + s + "/FeatureServer/0"
    try:
        j = requests.get(u, params={"f": "json"}, headers=H, timeout=30).json()
        print(s, j.get("error") or (j.get("maxRecordCount"), [f["name"] for f in j.get("fields", [])][:25]))
        print(requests.get(u + "/query", params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, headers=H, timeout=30).json())
    except Exception as e:
        print(s, "ERR", e)
for u in ["https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Table_Counties/NRI_Table_Counties.zip",
          "https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-b01001.dat",
          "https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/"]:
    r = requests.get(u, headers=H, timeout=30, stream=True)
    print(r.status_code, r.headers.get("Content-Length"), u[-70:])
