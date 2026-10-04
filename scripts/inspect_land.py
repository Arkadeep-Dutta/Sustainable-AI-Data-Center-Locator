import json, zipfile
from pathlib import Path
import pyarrow.parquet as pq
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
z = zipfile.ZipFile(RAW / "Annual_NLCD_LndCov_2023_CU_C1V1.zip")
print("NLCD", [(i.filename, i.file_size // 10**6) for i in z.infolist()][:8])
f = pq.ParquetFile(RAW / "padus41_combined.parquet")
print("PADUS rows", f.metadata.num_rows, "rg", f.num_row_groups)
print("PADUS cols", f.schema_arrow.names)
geo = f.schema_arrow.metadata.get(b"geo")
if geo:
    g = json.loads(geo); c = g["columns"][g["primary_column"]]
    print("geo", g["primary_column"], c.get("encoding"), str(c.get("crs", "4326?"))[:200])
t = pq.read_table(RAW / "padus41_combined.parquet", columns=["GAP_Sts", "FeatClass"])
print(t.group_by(["GAP_Sts", "FeatClass"]).aggregate([([], "count_all")]).to_pandas().to_string()[:1500])
