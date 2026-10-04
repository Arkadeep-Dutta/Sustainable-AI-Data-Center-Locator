"""EPA eGRID2023 (rev2) -> subregion carbon rate, clean share, grid water intensity.

Source: https://www.epa.gov/egrid ; subregion boundaries are EPA's approximate representational
polygons. Coarse REGIONAL value assigned to every H3 cell whose centroid falls in the subregion.
Grid water intensity uses literature consumption factors (scenario.yaml, Macknick et al. 2012):
ASSUMPTION applied to OBSERVED generation mix.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .. import config
from ..config import RAW
from ._util import points_in_polygons

LB_TO_KG = 0.45359237
GAL_TO_L = 3.785411784
MIX = {"coal": "SRCLPR", "oil": "SROLPR", "gas": "SRGSPR", "nuclear": "SRNCPR", "hydro": "SRHYPR",
       "biomass": "SRBMPR", "wind": "SRWIPR", "solar": "SRSOPR", "geothermal": "SRGTPR",
       "other_fossil": "SROFPR", "other": "SROPPR"}


def subregion_table(include_hydro: bool | None = None) -> pd.DataFrame:
    sc = config.load("scenario")
    if include_hydro is None:
        include_hydro = sc["include_hydro_water"]
    sr = pd.read_excel(RAW / "egrid2023_data_rev2.xlsx", "SRL23", header=1).set_index("SUBRGN")
    t = pd.DataFrame(index=sr.index)
    t["ec_co2_rate"] = sr["SRC2ERTA"].astype(float) * LB_TO_KG          # lb/MWh -> kg/MWh
    t["ec_clean_share"] = (sr["SRNCPR"].fillna(0) + sr["SRTRPR"].fillna(0)).astype(float)
    f = sc["grid_water_gal_per_mwh"]
    w = sum(sr[c].fillna(0).astype(float) * f[k] * (0 if (k == "hydro" and not include_hydro) else 1)
            for k, c in MIX.items())
    t["wa_grid_water"] = w * GAL_TO_L                                    # L/MWh
    t["egrid_hydro_share"] = sr["SRHYPR"].astype(float)
    return t


def build(cells: pd.DataFrame) -> pd.DataFrame:
    g = gpd.read_file(f"/vsizip/{RAW / 'egrid2023_v2_geodatabase.gdb.zip'}/Update_2024_v2.gdb",
                      layer="eGRID2023_Subregions")
    j = points_in_polygons(cells, g, ["Subregion"]).rename(columns={"Subregion": "egrid_subrgn"})
    t = subregion_table()
    out = j.join(t, on="egrid_subrgn")
    for c in ["ec_co2_rate", "ec_clean_share", "wa_grid_water"]:
        out[f"cov_{c}"] = out[c].notna()
    return out
