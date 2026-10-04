# SPEC — Sustainable AI Data Center Site-Selection Engine

Authoritative technical spec. Sources: official brief ("Where Should America's Next
Sustainable Data Center Be Built?") + lead-engineer instruction prompt (2026-10-04).
NOTE: the team's *original* long instruction document was not found on disk at audit
time; this spec is distilled from the instruction prompt, which restates it. If the
original surfaces and conflicts, record the discrepancy in §17 and resolve.
Values tagged **[PROPOSED]** are defaults to be locked at Gate 2 (then retag **[LOCKED]**).

---------------------------------------------------------------------------
## 1. Objective & scope
Transparent, reproducible engine that finds the most future-ready CONUS location for a
sustainable next-gen AI data center, evaluating 7 pillars:
Energy & Carbon (EC), Water (WA), Grid & Infrastructure (GI), Community & Economic (CE),
Climate Resilience (CR), Land & Materials (LM), Heat Recovery & Reuse (HR).

Official deliverables (brief): (1) location, (2) decision framework, (3) data analysis,
(4) sustainability impact, (5) risk assessment, (6) 20–30 yr implementation vision.
Brief emphasis: "Don't just find a location — design the decision framework"; open data,
OCP systems thinking; balance, not single-metric optimization.

- **P0**: engine; ≥1 real feature in all 7 pillars; gates; confidence; national screen;
  diverse shortlist; res-7 refinement; robustness; recommendation; 6 docs; maps;
  rankings.csv; candidates.geojson; Streamlit; critique; slide outline.
- **P1**: multi-feature pillars; TOPSIS; Pareto frontier; CMIP6 future climate; AHP
  helper; richer heat reuse; dossiers.
- **P2**: market-model comparison vs existing DC geography; res 8/9; smoothed surfaces;
  large low-impact datasets.

## 2. Spatial model
- Direct grid evaluation (random sampling + interpolation REJECTED: gates and
  infrastructure thresholds make the surface non-smooth).
- Storage CRS EPSG:4326; metric ops EPSG:5070.
- CONUS mask: Census cartographic boundary states (1:500k) minus AK, HI, territories.
- H3 v4 `polygon_to_cells` (centroid containment) + boundary cells retained if
  ≥ 50 % land.

| res | mean area | ≈ CONUS cells | role |
|---|---|---|---|
| 5 | 252.9 km² | ~32 k | fallback national screen |
| 6 | 36.1 km² | ~224 k | preferred national screen |
| 7 | 5.16 km² | ~1.57 M CONUS (only shortlist used) | local refinement |

- **Resolution decision**: benchmark one raster adapter (NLCD fractions) and one vector
  distance adapter (transmission) on a ~5 % CONUS subset; extrapolate; choose res 6 if
  projected full feature build < ~45 min, else res 5. Report at Gate 2.
- National cells are SCREENING REGIONS, not parcels. Parcel-scale gates only at res 7.
- Local pass: res 7 cells for Gate-3 regions (each region = buffered cluster hull,
  ~50 km radius). Recompute features directly; never interpolate national scores.

## 3. Feature store
`data/processed/features_res<N>.parquet`, one row per H3 cell:
`h3, lat, lon, state_fips, county_fips, <raw features>, cov_<feature>, <derived>,
excl_<gate>, eligible, conf_inputs`. Geometry rebuilt on demand from h3 (not stored).
Scores live separately: `data/processed/scores_res<N>.parquet`
(`v_<feature>, P_<pillar>, S_A, S_G, confidence, rank_G, rank_A`).
Weight/scenario changes recompute scores only — never spatial features.

## 4. Adapter contract
`siteselect/adapters/<name>.py` exposes `build(cells: GeoDataFrame, cfg) -> DataFrame`
indexed by h3, returning raw features + `cov_*` flags. Rules by type:
- RASTER: zonal stats (exactextract preferred) — mean + hazard percentile (p90) where
  relevant; nodata → NaN; large rasters pre-aggregated to ≥ cell-appropriate resolution
  (e.g. NLCD 30 m → class fractions at 240–480 m) before zonal stats.
- POLYGON: area-weighted overlay fraction in EPSG:5070; coverage = fraction of cell
  covered by source extent.
- POINT/LINE: nearest distance (cell centroid, EPSG:5070, KD-tree / STRtree) + count /
  capacity within radius.
- REGIONAL TABULAR (county/state/eGRID/BA/utility): crosswalk via cell centroid
  point-in-polygon; record `res_src=<county|state|egrid_subregion|...>` in features.yaml.
- TIME SERIES: reduce to physical statistic (e.g. 1991–2020 normal, % weeks in D2+
  drought 2000–present); document window.
Each feature registered in `config/features.yaml`:
`name, pillar, unit, source, vintage, res_src, direction(+/-), valuefn{type,params},
weight, missing_rule`. Provenance in `config/datasets.yaml`:
`id, title, url, publisher, vintage, license, resolution, coverage, file, sha256,
retrieved, verified`.

## 5. Data plan (per pillar) — P0 first
| Pillar | P0 features (source) | P1 |
|---|---|---|
| EC | grid CO2e rate kg/MWh (EPA eGRID2022/2023 subregion); non-emitting gen share (eGRID) | NREL NSRDB GHI, WTK wind CF; LBNL *Queued Up* clean-capacity queue / regional peak load; EIA-861 |
| WA | Aqueduct 4.0 baseline water stress (BWS raw ratio); grid water-consumption intensity L/MWh (eGRID gen mix × Macknick et al. 2012 factors) | Aqueduct 2030/2050 future BWS; EPA CWNS POTW (reclaimed water) proximity |
| GI | distance to ≥ 230 kV (and ≥ 345 kV) transmission; distance to substation (HIFLD / EIA US Energy Atlas / OSM fallback) | EIA-861 SAIDI/SAIFI; EIA industrial price ¢/kWh; queue congestion; fiber/IX proximity (FCC / PeeringDB); NTAD road/rail |
| CE | ACS 5-yr (2019–2023) county/tract: working-age pop within 80 km, unemployment, median HH income, pop density (residential burden); BLS QCEW construction+utilities+IT employment | occupation-level OEWS; CEJST/EJScreen burden; DC saturation |
| CR | FEMA NRI 2023 tract/county EAL scores: riverine+coastal flood, wildfire, hurricane, heat wave, drought; FEMA NFHL flood-zone fraction (refinement) | USFS Wildfire Risk to Communities; IBTrACS track density; USDM D2+ frequency; NEX-GDDP-CMIP6 Δ hot days |
| LM | NLCD 2021/Annual NLCD suitable-land fraction (classes 21-22 developed-open/low, 31 barren, 52 shrub, 71 grass, 81 pasture, 82 crops; excluding 11, 90/95 wetlands, 23-24 high-intensity); slope ≤ 10 % (USGS 3DEP, optional); PAD-US protected fraction | GEM steel/cement low-carbon plant proximity; FAF freight; EC3 factors |
| HR | NOAA 1991–2020 normals HDD (base 65 °F, interpolated from stations); heat-demand proxy = HDD × population within 50 km | USDA Census of Ag greenhouse area; industrial low-temp heat (EPA GHGRP facilities); district energy systems |
- If a P0 source fails: transparent proxy, never an empty pillar.
- Cooling-climate feature (CDD / annual mean temp from NOAA normals) is used in derived
  PUE/WUE (EC, WA) — see §9 & §11 for double-counting treatment.

## 6. Hard gates (applied before MCDA) [PROPOSED]
National (region-level feasibility, NOT parcel claims):
| Gate | Rule | Rationale |
|---|---|---|
| G1 land | suitable-and-unprotected area < 2 km² in cell (res 6) / < 15 km² (res 5) → excl | ~1 GW campus needs ~0.5–2 km² buildable |
| G2 protected/water | (PAD-US GAP 1–2 + open water + wetlands) fraction > 0.8 → excl | no feasible footprint |
| G3 flood | SFHA (1 % annual) fraction > 0.5 at national pass (NRI riverine/coastal rating "Very High" if NFHL absent) | most land floodplain |
| G4 transmission | distance to ≥ 230 kV line > 50 km → excl | interconnection cost/time prohibitive |
| G5 water | Aqueduct BWS = Extremely High (> 80 %) excluded ONLY in water-dependent cooling scenario; dry/DLC base case scores it instead | avoid over-exclusion under dry cooling |
Res-7 refinement: parcel-scale interpretation (contiguous ≥ 0.5 km² suitable,
outside SFHA, outside PAD-US, ≤ 15 km to ≥ 230 kV).
Gate 2 must report per gate: threshold, rationale, source, % CONUS removed individually,
cumulative removal. Gates are never tuned to force a result.

## 7. Value functions / normalization [PROPOSED]
v ∈ [0,1], 1 = best. Piecewise-linear physical thresholds where defensible:
| Feature | v=1 at | v=0 at | dir |
|---|---|---|---|
| grid CO2e rate (kg/MWh) | ≤ 100 | ≥ 700 | − |
| clean (non-emitting) share | ≥ 0.9 | ≤ 0.1 | + |
| Aqueduct BWS ratio | ≤ 0.10 | ≥ 0.80 | − |
| grid water intensity (L/MWh consumed) | ≤ 200 | ≥ 2500 | − |
| dist ≥230 kV (km) | ≤ 5 | ≥ 50 | − |
| dist substation (km) | ≤ 3 | ≥ 30 | − |
| suitable-land area (km², res 6) | ≥ 15 | ≤ 2 | + |
| flood SFHA fraction | ≤ 0.02 | ≥ 0.5 | − |
| protected fraction | 0 | ≥ 0.8 | − |
Others (NRI hazard scores, income, unemployment, density, HDD×pop, etc.): winsorized
(p2–p98) min-max or percentile rank, reference population = ELIGIBLE cells after gates
(recorded in features.yaml). Percentiles are relative — never read a percentile gap as
proportional physical benefit. Log-transform heavy-tailed counts (population, HDD×pop).
Alternative normalization (for method sensitivity): pure percentile rank for all.

## 8. Missing data & confidence
1. Production candidate must have ≥ 1 real observed feature in every pillar; else
   ineligible for final recommendation (`excl_pillar_missing`).
2. confidence = Σ (intended weights W_p·w_pf of features observed) / 1.0.
3. Decision eligibility: confidence ≥ 0.75 (configurable; Gate 2 shows effect of
   0.6 / 0.75 / 0.9).
4. Within pillar: renormalize observed weights only if ≥ 50 % of intended pillar feature
   weight observed; otherwise pillar treated as missing (→ rule 1).
5. Never impute an observation as real. Finalists get a downside sensitivity: missing
   v_f set to eligible-population p10 (and 0 for worst case); flag candidates whose rank
   moves > 3 places.

## 9. Double counting
- Spearman |r| over ALL quantitative features (cross-pillar); |r| > 0.8 flagged, not
  auto-deleted → `outputs/diagnostics/correlation.csv` + heatmap.
- Conceptual overlap review table in docs/02: e.g. temperature → PUE (EC), WUE (WA),
  HDD (HR), heat hazard (CR); population → workforce (CE), burden (CE), heat demand
  (HR); eGRID → carbon (EC) & grid water (WA). Keep intentional overlaps only where the
  consequence differs; document.

## 10. MCDA
P_p = Σ_f w_pf · v_f (w_pf sum to 1 after valid renormalization).
S_A = Σ_p W_p · P_p.  S_G = Π_p max(P_p, ε)^{W_p}, ε = 0.01.
PRIMARY rank = S_G (non-compensatory penalty for a disastrous pillar); S_A = method
sensitivity.
Default pillar weights [PROPOSED]: EC 22, WA 16, GI 16, CE 15, CR 14, LM 10, HR 7 (=100).
Within-pillar feature weights in features.yaml. Lock at Gate 2.

## 11. Derived physics (`config/scenario.yaml`; all ASSUMPTIONS, labeled) [PROPOSED]
- Base: IT = 300 MW; sensitivity 100 MW – 1 GW; utilization (load factor) 0.80.
- Cooling: direct-to-chip liquid + dry coolers with adiabatic assist.
- PUE(climate) = 1.08 + 2.0e-5 · CDD65 (°F-day) → ~1.08–1.17 across CONUS.
- On-site WUE (L/kWh_IT) = 0.02 + 6.0e-5 · CDD65 (adiabatic hours scale with heat).
- Facility energy E (MWh/yr) = IT_MW · 8760 · LF · PUE.
- Operational carbon: tCO2e/yr = E · EF_kg/MWh / 1000 (eGRID subregion **average**
  output rate = location-based; marginal rates (eGRID non-baseload / Cambium LRMER)
  as sensitivity).
- Clean-energy scenario: 24/7 CFE share s (0.6 / 0.9) → residual = E·(1−s)·EF.
- Forward decarbonization signal: (solar+wind+storage MW in LBNL queue) / regional peak
  load (by ISO/BA) — P1.
- Water: total = on-site (E_IT · WUE) + off-site (E · grid water intensity L/MWh).
  Grid water intensity = Σ_gen share_g · consumption factor_g (Macknick et al. 2012
  medians; label as literature factors).
- Scarcity-weighted water (AWARE-INSPIRED, not AWARE): SW = on-site · CF(BWS_local)
  + off-site · CF(BWS_regional); CF = clip(BWS/BWS_CONUS_median, 0.1, 10).
- Heat reuse: recoverable heat Q = IT energy · f_rec (0.6–0.8 for DLC at 45–60 °C,
  with heat pump uplift for district heating); useful fraction u = min(1, local demand /
  Q) using demand proxy; avoided tCO2 = Q·u·EF_displaced (natural-gas boiler
  0.20 tCO2/MWh_th at 90 % eff.; range with heat-pump electricity penalty).
- Embodied carbon opportunity: qualitative/proximity (P1 GEM trackers, EC3 factors).

## 12. Robustness (definitions fixed in advance)
- Weight uncertainty: Dirichlet(α = κ·W), κ = 100 baseline; also κ = 50 and 200 if
  cheap. Draws: 5,000 target (min 1,000), vectorized.
- Within-pillar: each w_pf × U(0.8, 1.2), renormalized within pillar, per draw.
- Per finalist: baseline rank, median rank, P(rank = 1), P(top 5), rank histogram.
- **Robustness winner**: max P(rank = 1); tie-break 1 better median rank; tie-break 2
  higher baseline S_G. Do not redefine after seeing results.
- Method uncertainty (required): S_G vs S_A; physical-threshold vs percentile
  normalization. P1: TOPSIS.
- Pareto: is the recommended finalist dominated across the 7 pillar scores? Report
  finalist frontier.
- Missing-data downside (§8.5). Scenario sensitivity: IT 100 MW / 1 GW; water-cooled
  scenario (activates G5).

## 13. Candidate extraction
Pool = top 5 % eligible cells by S_G (confidence ≥ 0.75). Greedy non-maximum
suppression: take best, suppress pool cells within R = 150 km (EPSG:5070), repeat →
20–25 regions. Report per region: best cell, mean S_G of pool cells within R, state,
nearest city. Then Gate 3.

## 14. Sanity check markets
Loudoun Co. VA (39.08, −77.65); Quincy WA (47.23, −119.85); The Dalles OR (45.60,
−121.18); central Iowa / Altoona (41.65, −93.47); Abilene TX (32.45, −99.73);
Cheyenne WY (41.14, −104.82); Phoenix AZ (33.45, −112.07). Purpose: detect reversed
metrics, broken joins, implausible distances (e.g. Loudoun must be < 10 km from
≥ 230 kV), artifacts, eGRID/Aqueduct plateaus. Plateau share = fraction of eligible-cell
S_G variance explained by eGRID subregion (ANOVA R²) — report; discuss in CRITIQUE.

## 15. Local refinement & qualitative whittling
- Res 7 over Gate-3 regions: recompute land suitability (NLCD), NFHL flood, PAD-US,
  transmission/substation distance, slope; regional features re-joined (not
  interpolated). Parcel-scale gates per §6. Output 5–8 finalists.
- Qualitative research per finalist (label QUALITATIVE vs MODEL-DERIVED): large-parcel
  availability, ISO/utility interconnection timeline, zoning, moratoria, incentives,
  water-rights regime, community sentiment, recent DC announcements, congestion.
  Comparison table → Gate 4.

## 16. Outputs
- docs/01_recommendation.md (city/county/state, coords, case, score, runner-ups,
  uncertainty) · 02_decision_framework.md (H3, extraction, value fns, gates, weights,
  missing data, confidence, MCDA, candidates, refinement, robustness, pipeline diagram)
  · 03_data_analysis.md (inventory: vintage, resolution, coverage, license, use,
  transforms, assumptions, distributions, maps, limits) · 04_sustainability_impact.md
  (winner vs Loudoun VA vs CONUS-average baseline: energy, tCO2e location-based + clean
  scenario, on-site/off-site/scarcity-weighted water, embodied carbon, heat reuse +
  avoided emissions; ranges) · 05_risk_assessment.md (likelihood×impact; env, grid,
  regulatory, water, interconnection, community, supply chain; mitigations; present &
  future) · 06_implementation_vision.md (20–30 yr phases, CFE procurement, storage,
  cooling, water, heat-reuse partners, adaptation, OCP hardware/circularity, community)
  · slides_outline.md (6–8 slides, chart/map per slide) · CRITIQUE.md (weight
  subjectivity & robustness, normalization, compensatory MCDA, missing data, coarse
  regional data, MAUP, resolution mismatch, vintage, average vs marginal EF, future
  grid, parcel data, interconnection politics, sentiment, coarse-to-fine miss risk,
  omitted variables, improvements).
- outputs/maps/: interactive national (score, pillars, exclusions, confidence,
  finalists) + static PNGs. outputs/rankings.csv, outputs/candidates.geojson.
- app/streamlit_app.py: map, ranked list, finalist detail, pillar sliders (instant
  rerank from parquet), scenario/constraint toggles.
- README.md: architecture, inputs, run, add dataset, change weights/scenario, reuse for
  other regions/vintages. License only with team approval.
- Final terminal response template: FINAL SITE / COORDINATES / TOP 5 / ROBUSTNESS
  (P(rank #1), median rank, method sensitivity) / DELIVERABLE STATUS (12 items) /
  MAJOR LIMITATIONS / DEMO COMMAND / FINAL COMMIT / CODEX: NONE|TARGETED|STRONGLY.

## 16b. GATE 2 LOCK (2026-10-04) — supersedes [PROPOSED] values above
- Resolution: H3 res 6 national (full build ≈ 8.5 min), res 7 refinement.
- Pillar weights: EC 22, GI 22, CR 16, WA 15, CE 11, LM 8, HR 6.
- WUE removed from scoring (r = 1.0 with PUE; both CDD-derived); PUE weight in EC raised to 0.30
  (EC: CO2 0.45, clean 0.25, PUE 0.30). WA: BWS 0.40, BWS-2050 0.25, grid water 0.35.
  WUE still computed for the impact assessment (docs/04).
- Grid water: hydro reservoir evaporation EXCLUDED in baseline; inclusion = sensitivity.
- Gates G1, G2, G4 as §6 (G5 only in water-cooled scenario); value functions per features.yaml.
- Robustness per §12 unchanged. Authoritative numbers live in config/*.yaml.

## 16c. GATE 3 / GATE 4 LOCK (2026-10-04)
- Gate 3: regions 1, 2, 3, 5, 7, 9, 11, 19 refined at res 7 (added 3DEP slope ≤ 10 %, FEMA NFHL SFHA).
- Model robustness winner (rule §12): R1 King Co WA, P(rank1)=0.874 (κ=100).
- **Gate 4 TEAM DECISION: recommend R2 — Wyoming County NY, H3 872aa6c44ffffff (42.772, −78.446),
  ≈5 km from Strykersville.** Rationale: 20–30 yr carbon-led view — NYUP grid 110 vs 288 kg CO2e/MWh
  (−62 %), lowest water scarcity, robust top-3 (P(top5)=0.998, median rank 3); accepts the NY one-year
  >20 MW moratorium (Jul 2026) as a near-term delay. This override of the rule-based winner must be stated
  explicitly in every deliverable. Claims = scenario.yaml base case (300 MW IT), docs/04.

## 17. Discrepancy log
- 2026-10-04: original long instruction document not located; spec built from the
  instruction prompt. HIFLD Open Data portal was retired in 2025 — transmission /
  substation layers may need an archived mirror, EIA US Energy Atlas, or OSM fallback.
