"""Verify C24010 line numbers against the official 2023 ACS 5-year table-based SF shell."""
import io
import requests
import pandas as pd

H = {"User-Agent": "Mozilla/5.0 siteselect-research"}
base = "https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/documentation/"
for name in ["ACS20235YR_Table_Shells.txt", "ACS20235YR_Table_Shells.xlsx"]:
    r = requests.get(base + name, headers=H, timeout=120)
    print(name, r.status_code, len(r.content))
    if r.status_code == 200:
        break
if name.endswith(".txt"):
    t = pd.read_csv(io.StringIO(r.content.decode("utf-8", "ignore")), sep="|", dtype=str)
else:
    t = pd.read_excel(io.BytesIO(r.content), dtype=str)
print(list(t.columns))
c = t[t.iloc[:, 0].astype(str).str.upper() == "C24010"]
keep = {"001", "002", "003", "007", "008", "009", "010", "030", "031", "032", "033", "034", "035", "036", "037",
        "038", "039", "043", "044", "045", "046", "066", "067", "068", "069", "070", "071", "072", "073"}
for _, row in c.iterrows():
    uid = str(row.get("Unique ID", row.iloc[2]))
    if uid[-3:] in keep:
        print(uid, "|", row.get("Label", row.iloc[3]))
