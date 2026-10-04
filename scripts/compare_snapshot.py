"""Compare current finalists / national scores against a snapshot dir in outputs/diagnostics/.
python scripts/compare_snapshot.py <snapshot_dir> [pillar]"""
import sys
import pandas as pd
from pyproj import Geod
from siteselect import candidates
from siteselect.config import DIAG, PROCESSED

pd.set_option("display.width", 250)
d, pil = DIAG / sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "GI")
a = pd.read_csv(d / "finalists_robustness.csv").set_index("label")
b = pd.read_csv(DIAG / "finalists_robustness.csv").set_index("label")
cols = ["h3", "S_G", "rank_G", "rank_A", "rank_pctnorm", f"P_{pil}", "p_rank1_k100", "median_rank_k100"]
cmp = a[cols].join(b[cols], lsuffix="_old", rsuffix="_new")
cmp["same_site"] = cmp["h3_old"] == cmp["h3_new"]
print(cmp[["same_site"] + [c for c in cmp.columns if c not in ("h3_old", "h3_new", "same_site")]].round(4).to_string())
o = pd.read_parquet(d / "scores_res6.parquet"); n = pd.read_parquet(PROCESSED / "scores_res6.parquet")
print("national |dS_G| p50/p99/max:", (n.S_G - o.S_G).abs().quantile([.5, .99, 1]).round(4).to_dict())
print("eligible old/new:", int(o.eligible.sum()), int(n.eligible.sum()))
nc = candidates.nms(n.reset_index(), pool_frac=0.05, radius_km=150, max_regions=25)
old = pd.read_csv(d / "shortlist_res6.csv")
g = Geod(ellps="WGS84")
nc["km_to_old"] = [min(g.inv(r.lon, r.lat, x.lon, x.lat)[2] for _, x in old.iterrows()) / 1000 for _, r in nc.iterrows()]
print("new top-25 regions within 75 km of an old region:", int((nc.km_to_old < 75).sum()), "/ 25")
print("new regions not in old list:", nc.loc[nc.km_to_old >= 75, ["state", "lat", "lon", "S_G"]].round(3).to_dict("records"))
cmp.round(4).to_csv(DIAG / f"{sys.argv[1]}_comparison.csv")
