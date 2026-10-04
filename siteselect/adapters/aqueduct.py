"""WRI Aqueduct 4.0 -> baseline water stress (bws_raw) and 2050 BAU projected stress.

Catchment (HydroBASINS L6) polygons; centroid point-in-polygon. License CC BY 4.0.
'Arid and low water use' catchments (bws_cat == -1) are scored by Aqueduct as extremely high;
we set their raw ratio to max(raw, 0.8) and flag them (aq_arid).
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from ..config import RAW
from ._util import points_in_polygons

GDB = f"/vsizip/{RAW / 'aqueduct-4-0-water-risk-data.zip'}/Aqueduct40_waterrisk_download_Y2023M07D05/GDB/Aq40_Y2023D07M05.gdb"
BBOX = (-125.5, 24.0, -66.5, 49.8)


def build(cells: pd.DataFrame) -> pd.DataFrame:
    b = gpd.read_file(GDB, layer="baseline_annual", bbox=BBOX, columns=["bws_raw", "bws_cat"])
    out = points_in_polygons(cells, b, ["bws_raw", "bws_cat"])
    # 9999 = 'Extremely High' sentinel (near-zero available supply): cap at 10 (v=0 either way)
    raw = out["bws_raw"].where(out["bws_raw"] >= 0).clip(upper=10.0)
    arid = out["bws_cat"] == -1
    out["wa_bws"] = np.where(arid, np.fmax(raw.fillna(0.8), 0.8), raw)
    out["aq_arid"] = arid
    f = gpd.read_file(GDB, layer="future_annual", bbox=BBOX, columns=["bau50_ws_x_r"])
    fr = points_in_polygons(cells, f, ["bau50_ws_x_r"])["bau50_ws_x_r"]
    out["wa_bws_2050"] = fr.where(fr >= 0).clip(upper=10.0)
    for c in ["wa_bws", "wa_bws_2050"]:
        out[f"cov_{c}"] = out[c].notna()
    return out[["wa_bws", "wa_bws_2050", "aq_arid", "cov_wa_bws", "cov_wa_bws_2050"]]
