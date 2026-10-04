# CLAUDE.md — Sustainable AI Data Center Site-Selection Engine

Operating rules only. Technical design lives in `docs/SPEC.md` (authoritative).
Official brief: `~/Downloads/Copy of Data Center Locator.pdf` (controls deliverables).
Do NOT reread the brief or the original long prompt unless a discrepancy arises.

## Mode
- DEADLINE MODE. Preserve analytical credibility + all deliverables; minimize tokens.
- Priority: P0 > P1 > P2 (see SPEC §1). If short on time, CUT DATASET BREADTH FIRST.
- Never cut: robustness, provenance, critique, final deliverables.
- Site must emerge from analysis. Never pick a winner first.

## Approval gates (the ONLY stops)
1. GATE 1 — plan / data scope (after audit).
2. GATE 2 — methodology lock (gates, normalization, weights, missing-data,
   resolution + benchmark, robustness config) BEFORE production national scoring.
3. GATE 3 — ~20 diverse candidates + sanity checks + 5–8 regions for res-7 refinement.
4. GATE 4 — finalists, winner, robustness stats, uncertainties, impact claims.
- No approval needed for: coding, tests, adapters, plots, docs, caching,
  rerunning an approved pipeline, minor bug fixes.
- Ask before: any download > ~2 GB; any paid API; adding a license.

## Bug policy
- Fix routine bugs silently.
- STOP only if a bug may invalidate prior results (CRS, units, scoring direction,
  exclusion failure, join/crosswalk failure, corrupted data, unexplained large
  rank shift). Report:
  `BUG: / IMPACT: / FIX: / NEED APPROVAL: YES`

## Check-ins
- After each work unit (audit, core engine, dataset batch, national scoring,
  refinement, robustness, final deliverables). Format, <~120 words:
  `DONE: / DATA: / RESULT: / ISSUE: / NEXT:`
- Detailed status ONLY in `STATUS.md`. Do not duplicate status elsewhere.
- No time-based check-ins.

## Dataset onboarding response (compact)
```
DATASET: / TYPE / SIZE: / COVERAGE / VINTAGE: / CRS / UNITS: / USE: /
LIMITATION: / RECOMMEND: ACCEPT | DEFER | REJECT
```
- If accepted: `siteselect/adapters/<name>.py` → H3-keyed features + coverage flags;
  register in `config/features.yaml` and `config/datasets.yaml` (provenance).
- After integration: targeted test → rescore → check distribution/missingness →
  report only material rank changes.

## Token / tool rules
- Tables: schema + `head(5)` only. Never print full DataFrames or long logs.
- Geodata: `ogrinfo -so` / `gdalinfo` / `rio info` / `pyogrio.read_info` BEFORE loading.
- Scripts run quietly; diagnostics → `outputs/diagnostics/*.{csv,md,png}`, not chat.
- Cache every expensive result (Parquet in `data/processed/`, interim in `data/interim/`).
- Never redownload a dataset already recorded as verified in `config/datasets.yaml`.
- Don't reopen unchanged large files. Weight changes must NOT trigger spatial recompute.
- Subagents only for isolated inspections that would pollute main context.
- Never hard-code secrets; use env vars / `.env` (gitignored).

## Repo layout
```
siteselect/            python package
  grid.py              H3 grid build (CONUS mask, res N), CRS helpers
  adapters/<name>.py   one per dataset → DataFrame[h3, features..., cov_*]
  features.py          assemble feature store (features_res<N>.parquet)
  valuefn.py           value functions / normalization
  gates.py             hard constraints
  scoring.py           pillar scores, S_A, S_G, confidence
  derived.py           carbon / water / PUE / heat-reuse physics
  candidates.py        top-pool + NMS/DBSCAN diversity
  robustness.py        Dirichlet MC, method sensitivity, Pareto, missing-data downside
  refine.py            res-7 local recompute
  maps.py              interactive + static maps
config/  features.yaml  scenario.yaml  weights.yaml  gates.yaml  datasets.yaml
data/    raw/ (gitignored)  interim/  processed/
outputs/ maps/ diagnostics/ rankings.csv candidates.geojson
app/streamlit_app.py   runs from precomputed parquet only
docs/    SPEC.md 01..06_*.md slides_outline.md CRITIQUE.md
tests/   pytest
STATUS.md README.md
```

## Coding conventions
- Python 3.11+ (verify geo wheels on installed interpreter), venv at `.venv`.
- Libraries: pandas, geopandas, shapely 2, pyproj, h3 (v4 API), rasterio,
  exactextract or rasterstats, pyarrow, scikit-learn, pyyaml, streamlit, pydeck/folium.
- Storage CRS EPSG:4326; distance/area in EPSG:5070 (CONUS Albers). Never compute
  distances in degrees.
- Every adapter: explicit unit conversion, nodata preserved as NaN, `cov_<feature>`
  boolean column, docstring citing source + vintage + license.
- All tunables in `config/*.yaml`; no magic numbers in code.
- Assumptions (scenario.yaml) vs observations (datasets) always labeled distinctly.
- Never fabricate or impute a missing observation as if real.
- Vectorize (numpy) robustness draws; no per-cell Python loops over 100k+ cells.
- Functions small and pure; pipeline entry: `python -m siteselect.run --stage <x>`.
- Pin deps in `requirements.txt`.

## Testing (high-risk logic only)
- value-fn direction + thresholds; gates; missing-data rules; confidence;
  pillar aggregation; S_A/S_G; weight normalization; candidate diversity;
  one end-to-end smoke test on a small bbox.
- Per major adapter: CRS, units, nodata, one known sanity case.
- `pytest -q` must pass before any gate presentation.

## Final validation checklist (before completion)
7 pillars represented · 6 official deliverables · recommendation + coordinates ·
every major number traceable to a config/dataset · assumptions labeled ·
provenance complete · rankings.csv + candidates.geojson load · maps load ·
Streamlit launches · tests pass · no placeholders · no secrets · no fabricated
values · candid limitations · one end-to-end smoke test.
Final terminal response format: see SPEC §16.
