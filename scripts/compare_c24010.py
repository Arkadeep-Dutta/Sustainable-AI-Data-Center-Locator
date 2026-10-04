import pandas as pd
from siteselect import candidates
from siteselect.config import DIAG, PROCESSED
pd.set_option("display.width", 250)
d = DIAG / "pre_c24010_fix"
a = pd.read_csv(d / "finalists_robustness.csv").set_index("label")
b = pd.read_csv(DIAG / "finalists_robustness.csv").set_index("label")
cols = ["h3", "S_G", "rank_G", "rank_A", "rank_pctnorm", "P_CE", "p_rank1_k100", "median_rank_k100"]
cmp = a[cols].join(b[cols], lsuffix="_old", rsuffix="_new")
cmp["dP_CE"] = cmp["P_CE_new"] - cmp["P_CE_old"]
cmp["same_site"] = cmp["h3_old"] == cmp["h3_new"]
print(cmp[["same_site", "S_G_old", "S_G_new", "rank_G_old", "rank_G_new", "rank_pctnorm_old", "rank_pctnorm_new",
           "P_CE_old", "P_CE_new", "dP_CE", "p_rank1_k100_old", "p_rank1_k100_new", "median_rank_k100_new"]].round(4).to_string())
# raw feature change at finalist sites
f7 = pd.read_parquet(PROCESSED / "features_res7_refine.parquet")
print("skilled share new at finalists:", f7.loc[b["h3"], "ce_skilled_share_80km"].round(3).to_dict())
# national: score shift and shortlist overlap (Gate-3 regions are locked; this is a check only)
o = pd.read_parquet(d / "scores_res6.parquet"); n = pd.read_parquet(PROCESSED / "scores_res6.parquet")
print("national |dS_G| p50/p99/max:", (n.S_G - o.S_G).abs().quantile([.5, .99, 1]).round(4).to_dict())
print("national |dP_CE| p50/p99/max:", (n.P_CE - o.P_CE).abs().quantile([.5, .99, 1]).round(4).to_dict())
nc = candidates.nms(n.reset_index(), pool_frac=0.05, radius_km=150, max_regions=25)
old = pd.read_csv(d / "shortlist_res6.csv")
match = sum(candidates.min_separation_km(pd.concat([r.to_frame().T[["lat", "lon"]], old[["lat", "lon"]]]).astype(float)) < 75 and True
            for _, r in nc.iterrows())
from pyproj import Geod
g = Geod(ellps="WGS84")
def near(r):
    return min(g.inv(r.lon, r.lat, o2.lon, o2.lat)[2] for _, o2 in old.iterrows()) / 1000
nc["km_to_old_region"] = nc.apply(near, axis=1)
print("new top-25 regions within 75 km of an old region:", int((nc.km_to_old_region < 75).sum()), "/ 25")
print("new #1 region:", nc.iloc[0][["lat", "lon", "state", "S_G"]].to_dict())
cmp.round(4).to_csv(DIAG / "c24010_fix_comparison.csv")
