"""Cheap schema inspection of raw files -> outputs/diagnostics/raw_inspect.txt (not chat)."""
import io, sys, tarfile, zipfile
from pathlib import Path
import pandas as pd
import pyogrio

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
out = []
def p(*a): out.append(" ".join(str(x) for x in a))

xl = pd.ExcelFile(RAW / "egrid2023_data_rev2.xlsx")
p("EGRID sheets", xl.sheet_names)
sr = pd.read_excel(xl, "SRL23", header=1, nrows=3)
p("SRL23 cols", list(sr.columns))
z = zipfile.ZipFile(RAW / "egrid2023_v2_geodatabase.gdb.zip"); p("EGRID GDB", z.namelist()[:5])
z = zipfile.ZipFile(RAW / "aqueduct-4-0-water-risk-data.zip"); p("AQ", [n for n in z.namelist() if not n.endswith("/")][:40])
t = tarfile.open(RAW / "noaa_normals_annualseasonal_1991_2020.tar.gz"); m = t.getmembers()
p("NOAA n", len(m), m[1].name)
f = t.extractfile(m[1]); df = pd.read_csv(f); p("NOAA cols", [c for c in df.columns if c in ("STATION","LATITUDE","LONGITUDE","ANN-HTDD-NORMAL","ANN-CLDD-NORMAL")], df.shape)
for tb in ["b01001", "c24010", "b23025", "b19013"]:
    with open(RAW / f"acsdt5y2023-{tb}.dat") as fh:
        hdr = fh.readline().strip().split("|"); first = fh.readline()[:60]
    p("ACS", tb, len(hdr), hdr[:6], first)
z = zipfile.ZipFile(RAW / "2023_Gaz_tracts_national.zip"); p("GAZ", z.namelist())
Path(RAW.parents[1] / "outputs" / "diagnostics" / "raw_inspect.txt").write_text("\n".join(out))
