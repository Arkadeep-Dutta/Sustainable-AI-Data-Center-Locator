import pandas as pd
from siteselect import robustness, scoring
from siteselect.config import PROCESSED, DIAG
s = pd.read_parquet(PROCESSED / "scores_res6.parquet")
sl = pd.read_csv(DIAG / "shortlist_res6.csv")
ft = scoring.feature_table()
V = s.loc[sl["h3"], [f"v_{k}" for k in ft.index]].to_numpy()
for kappa in (50, 100, 200):
    r = robustness.weight_mc(V, n_draws=5000, kappa=kappa)
    sm = robustness.summarize(r, list(sl["county"]), s.loc[sl["h3"], "S_G"].to_numpy())
    sm.round(3).to_csv(DIAG / f"robust_preview_k{kappa}.csv", index=False)
    print(f"kappa={kappa}:", "; ".join(f"{a} P1={b:.2f} med={c:.0f}" for a, b, c in sm[["id", "p_rank1", "median_rank"]].head(6).values))
