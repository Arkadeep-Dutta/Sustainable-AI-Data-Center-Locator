import zipfile
from pathlib import Path
import pandas as pd
import pyogrio

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
out = []
def p(*a): out.append(" ".join(str(x) for x in a))
sr = pd.read_excel(RAW / "egrid2023_data_rev2.xlsx", "SRL23", header=1)
p("SR PR cols", [c for c in sr.columns if c.endswith("PR")])
p("SR rows", len(sr), list(sr["SUBRGN"]))
g = f"/vsizip/{RAW / 'egrid2023_v2_geodatabase.gdb.zip'}/Update_2024_v2.gdb"
for lyr in pyogrio.list_layers(g)[:20]:
    i = pyogrio.read_info(g, layer=lyr[0]); p("EGRID LYR", lyr[0], i["features"], i["crs"], list(i["fields"])[:8])
a = "Aqueduct40_waterrisk_download_Y2023M07D05/CVS/"
z = zipfile.ZipFile(RAW / "aqueduct-4-0-water-risk-data.zip")
b = pd.read_csv(z.open(a + "Aqueduct40_baseline_annual_y2023m07d05.csv"), nrows=3)
p("AQ base cols", [c for c in b.columns if c.startswith(("bws", "string", "pfaf", "aq30", "gid", "name"))][:20])
f = pd.read_csv(z.open(a + "Aqueduct40_future_annual_y2023m07d05.csv"), nrows=3)
p("AQ fut cols", [c for c in f.columns if "ws" in c and c.startswith("bau50")][:12], [c for c in f.columns][:4])
ag = f"/vsizip/{RAW / 'aqueduct-4-0-water-risk-data.zip'}/Aqueduct40_waterrisk_download_Y2023M07D05/GDB/Aq40_Y2023D07M05.gdb"
for lyr in pyogrio.list_layers(ag):
    i = pyogrio.read_info(ag, layer=lyr[0]); p("AQ LYR", lyr[0], i["features"], str(i["crs"])[:20], list(i["fields"])[:6])
Path(RAW.parents[1] / "outputs" / "diagnostics" / "raw_inspect2.txt").write_text("\n".join(out))
