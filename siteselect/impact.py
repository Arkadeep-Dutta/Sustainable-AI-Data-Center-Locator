"""Sustainability impact accounting (docs/04). Same facility design at every location so differences
are attributable to LOCATION. All facility parameters are ASSUMPTIONS from config/scenario.yaml;
location inputs are OBSERVED (eGRID, NOAA normals, Aqueduct, ACS).

python -m siteselect.impact <h3_res7_winner>
"""
from __future__ import annotations

import json
import sys

import h3
import numpy as np
import pandas as pd

from . import config
from .adapters import egrid
from .config import DIAG, PROCESSED, RAW

LB_TO_KG = 0.45359237
GAL_TO_L = 3.785411784


def conus_baseline() -> dict:
    """US-average grid (eGRID2023 US totals) + area-median climate/water of eligible CONUS cells."""
    us = pd.read_excel(RAW / "egrid2023_data_rev2.xlsx", "US23", header=1).iloc[0]
    sc = config.load("scenario")
    f = sc["grid_water_gal_per_mwh"]
    mix = {"coal": "USCLPR", "oil": "USOLPR", "gas": "USGSPR", "nuclear": "USNCPR", "hydro": "USHYPR",
           "biomass": "USBMPR", "wind": "USWIPR", "solar": "USSOPR", "geothermal": "USGTPR",
           "other_fossil": "USOFPR", "other": "USOPPR"}
    gw = {inc: sum(float(us.get(c, 0) or 0) * f[k] * (0 if (k == "hydro" and not inc) else 1)
                   for k, c in mix.items()) * GAL_TO_L for inc in (False, True)}
    s = pd.read_parquet(PROCESSED / "scores_res6.parquet", columns=["eligible"])
    ft = pd.read_parquet(PROCESSED / "features_res6.parquet",
                         columns=["cdd65", "hdd65", "wa_bws", "pop_50km"]).loc[s["eligible"]]
    return {"name": "CONUS average", "co2_kg_mwh": float(us["USC2ERTA"]) * LB_TO_KG,
            "clean_share": float(us["USNCPR"] + us["USTRPR"]), "grid_water_l_mwh": gw[False],
            "grid_water_l_mwh_hydro": gw[True], "cdd65": float(ft["cdd65"].median()),
            "hdd65": float(ft["hdd65"].median()), "bws": float(ft["wa_bws"].median()),
            "pop_50km": float(ft["pop_50km"].median())}


def site(h3id: str, name: str) -> dict:
    res = h3.get_resolution(h3id)
    f = pd.read_parquet(PROCESSED / ("features_res7_refine.parquet" if res == 7 else "features_res6.parquet"))
    r = f.loc[h3id]
    hyd = egrid.subregion_table(include_hydro=True)["wa_grid_water"]
    return {"name": name, "h3": h3id, "egrid": r["egrid_subrgn"], "co2_kg_mwh": float(r["ec_co2_rate"]),
            "clean_share": float(r["ec_clean_share"]), "grid_water_l_mwh": float(r["wa_grid_water"]),
            "grid_water_l_mwh_hydro": float(hyd[r["egrid_subrgn"]]), "cdd65": float(r["cdd65"]),
            "hdd65": float(r["hdd65"]), "bws": float(r["wa_bws"]), "pop_50km": float(r["pop_50km"])}


def account(loc: dict, it_mw: float | None = None) -> dict:
    sc = config.load("scenario")
    c, fac, hr = sc["cooling"], sc["facility"], sc["heat_reuse"]
    it_mw = it_mw or fac["it_mw"]
    e_it = it_mw * 8760 * fac["load_factor"]                          # MWh/yr
    pue = c["pue_base"] + c["pue_per_cdd"] * loc["cdd65"]
    wue = c["wue_base_l_per_kwh"] + c["wue_per_cdd"] * loc["cdd65"]
    e_fac = e_it * pue
    co2 = e_fac * loc["co2_kg_mwh"] / 1000                            # t/yr, location-based average
    onsite_m3 = e_it * 1000 * wue / 1000
    offsite_m3 = e_fac * loc["grid_water_l_mwh"] / 1000
    offsite_hyd_m3 = e_fac * loc["grid_water_l_mwh_hydro"] / 1000
    lo, hi = sc["scarcity_cf_clip"]
    cf = float(np.clip(loc["bws"] / loc["bws_ref"], lo, hi))
    q_lo, q_hi = (e_it * f for f in hr["recoverable_fraction"])       # MWh_th recoverable
    ef_gas = hr["displaced_ef_tco2_per_mwh_th"]
    # avoided = useful heat x gas EF - heat-pump uplift electricity (COP 3) x grid EF; utilisation 10-30 %
    def avoided(q, u):
        return q * u * (ef_gas - loc["co2_kg_mwh"] / 1000 / 3.0)
    return {**loc, "it_mw": it_mw, "pue": pue, "wue_l_per_kwh": wue,
            "facility_mwh": e_fac, "it_mwh": e_it, "co2_t": co2,
            **{f"co2_t_cfe{int(s*100)}": co2 * (1 - s) for s in sc["energy"]["cfe_shares"]},
            "onsite_water_m3": onsite_m3, "offsite_water_m3": offsite_m3,
            "offsite_water_hydro_m3": offsite_hyd_m3, "scarcity_cf": cf,
            "scarcity_weighted_m3": (onsite_m3 + offsite_m3) * cf,
            "heat_recoverable_mwh_th_lo": q_lo, "heat_recoverable_mwh_th_hi": q_hi,
            "avoided_t_lo": avoided(q_lo, 0.10), "avoided_t_hi": avoided(q_hi, 0.30)}


def run(winner_h3: str, winner_name: str) -> pd.DataFrame:
    base = conus_baseline()
    loud = site(h3.latlng_to_cell(39.08, -77.65, 6), "Loudoun County, VA")
    win = site(winner_h3, winner_name)
    for d in (base, loud, win):
        d["bws_ref"] = base["bws"]
    rows = [account(d) for d in (win, loud, base)]
    rows += [account(win, 100), account(win, 1000)]
    df = pd.DataFrame(rows)
    df.to_csv(DIAG / "impact.csv", index=False)
    (DIAG / "impact_inputs.json").write_text(json.dumps({"baseline": base, "loudoun": loud, "winner": win},
                                                       indent=1, default=str))
    return df


if __name__ == "__main__":
    print(run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "Winner").round(3).T.to_string())
