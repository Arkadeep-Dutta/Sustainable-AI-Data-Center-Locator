"""Adapter sanity tests on the built feature store (skipped if data not built)."""
import h3
import numpy as np
import pandas as pd
import pytest

from siteselect.adapters import _util, egrid
from siteselect.config import PROCESSED

F6 = PROCESSED / "features_res6.parquet"
pytestmark = pytest.mark.skipif(not F6.exists(), reason="feature store not built")


@pytest.fixture(scope="module")
def f6():
    return pd.read_parquet(F6)


def cell(f, lat, lon):
    return f.loc[h3.latlng_to_cell(lat, lon, 6)]


def test_crs_metric_distance():
    # EPSG:5070 metres: Seattle -> Portland ~ 233 km great-circle
    xy = _util.xy_m([-122.33, -122.68], [47.61, 45.52])
    d = np.hypot(*(xy[0] - xy[1])) / 1000
    assert 225 < d < 245


def test_egrid_units_and_known_values():
    t = egrid.subregion_table(include_hydro=False)
    # kg/MWh (not lb): CONUS subregions between ~80 and ~800
    conus = t.drop(index=[i for i in t.index if i.startswith(("AK", "HI", "PR"))])
    assert conus["ec_co2_rate"].between(80, 800).all()
    assert t.at["NYUP", "ec_co2_rate"] < t.at["SRMW", "ec_co2_rate"]       # upstate NY cleaner than coal-heavy SRMW
    assert t["ec_clean_share"].between(0, 1).all()
    # hydro inclusion raises NWPP grid water
    assert egrid.subregion_table(include_hydro=True).at["NWPP", "wa_grid_water"] > t.at["NWPP", "wa_grid_water"] * 3


def test_transmission_known_hubs(f6):
    assert cell(f6, 39.08, -77.65)["gi_dist_tx230_km"] < 15        # Loudoun
    assert cell(f6, 47.23, -119.85)["gi_dist_tx230_km"] < 15       # Quincy
    assert f6["gi_dist_tx230_km"].isna().mean() == 0


def test_water_stress_known_contrast(f6):
    assert cell(f6, 33.45, -112.07)["wa_bws"] > 0.8                 # Phoenix extremely high
    assert cell(f6, 42.77, -78.45)["wa_bws"] < 0.1                  # Western NY low
    assert f6["wa_bws"].max() <= 10                                 # sentinel capped


def test_climate_normals_direction(f6):
    mn, fl = cell(f6, 46.8, -92.1), cell(f6, 27.9, -82.5)           # Duluth vs Tampa
    assert mn["hdd65"] > 7000 > fl["hdd65"] and fl["cdd65"] > mn["cdd65"]
    assert f6["ec_pue"].between(1.08, 1.2).all()


def test_land_fractions_valid(f6):
    for c in ["lm_protected_frac", "lm_wet_frac"]:
        assert f6[c].between(0, 1).all()
    assert (f6["lm_suitable_km2"] <= f6["area_km2"] + 1e-6).all()
    assert cell(f6, 44.6, -110.5)["lm_protected_frac"] > 0.8        # Yellowstone


def test_nodata_preserved_not_zero(f6):
    # NRI coverage gaps must be NaN, never silently 0
    assert f6["cr_flood_freq"].isna().sum() > 0
    assert (f6.loc[f6["cr_flood_freq"].isna(), "cov_cr_flood_freq"] == False).all()  # noqa: E712


def test_end_to_end_smoke():
    """Score a small bbox through gates -> scoring -> candidates without touching caches."""
    from siteselect import candidates, gates, scoring
    f = pd.read_parquet(F6)
    sub = f[f["lat"].between(42, 44) & f["lon"].between(-80, -76)]
    g = gates.apply(sub, 6)
    s = scoring.score(sub, g["gate_pass"])
    assert s["eligible"].sum() > 100
    assert s.loc[s["eligible"], "S_G"].between(0, 1).all()
    c = candidates.nms(pd.concat([sub[["lat", "lon"]], s], axis=1).reset_index(), pool_frac=0.1, radius_km=50,
                       max_regions=5)
    assert 1 <= len(c) <= 5
