# 02 — Decision Framework

An open, configurable siting engine: **screen → gate → score → diversify → refine → stress-test → whittle**.
Every number below is read from `config/*.yaml`; changing a YAML file and re-running reproduces the analysis.

## 1. Pipeline

```
 open datasets (15)            config/datasets.yaml  (provenance, sha256)
        │  siteselect.download
        ▼
 adapters/<name>.py  ──►  H3-keyed features + coverage flags   (cached, data/interim/)
        │  siteselect.features
        ▼
 features_res6.parquet (209,488 CONUS cells × 64 cols)
        │  gates.py (hard constraints)          config/gates.yaml
        │  valuefn.py (physical value functions) config/features.yaml
        │  scoring.py (pillars, S_G, S_A, confidence) config/weights.yaml
        ▼
 scores_res6.parquet ──► candidates.py (top-5 % pool + 150 km NMS) ──► 25 regions  [Gate 3]
        │
        ▼  refine.py — res-7 cells, 50 km radius, 30 m land / slope / FEMA SFHA, local gates
 scores_res7_refine.parquet ──► finalists.py (best eligible site per region)
        │  robustness.py — Dirichlet weights × feature jitter, method & data sensitivities, Pareto
        ▼
 qualitative whittling (zoning, moratoria, interconnection, incentives)  [Gate 4] ──► recommendation
```

Scoring is decoupled from spatial processing: re-weighting re-scores 209k cells in < 1 s (the Streamlit
demo does exactly this), while the full spatial feature build takes ≈ 8.5 min.

## 2. Spatial design (H3)

| Pass | H3 res | Cell area | Cells | Role |
|---|---|---|---|---|
| National screening | 6 | ≈ 36 km² | 209,488 | regional feasibility + scoring |
| Local refinement | 7 | ≈ 5.2 km² | ≈ 1,450 per region (50 km radius) | site-scale gates & scores |

* Direct evaluation of every cell. Random sampling + interpolation was rejected because hard gates and
  infrastructure distance thresholds make the objective surface discontinuous.
* Geometry stored in EPSG:4326; all distances/areas in EPSG:5070 (CONUS Albers).
* Res 6 chosen by benchmark (adapter_timing.json): total build ≈ 8.5 min, dominated by land (≈ 6 min).
* A res-6 cell is a **screening region, not a parcel**. Parcel-scale constraints (≥ 0.5 km² buildable,
  outside the FEMA 1 % floodplain, ≤ 15 km to 230 kV) are applied only at res 7.

## 3. Feature extraction by data type

| Type | Method | Examples |
|---|---|---|
| Raster | NLCD sampled at 240 m (national) / native 30 m (local) → exactextract class fractions per hexagon | land suitability, wetlands |
| Polygon | rasterised on the NLCD grid (PAD-US, FEMA SFHA) or centroid point-in-polygon (Aqueduct catchments, eGRID subregions) | protected fraction, water stress |
| Line / point | STRtree nearest distance in EPSG:5070; line length within 30 km via FFT disc convolution | transmission |
| Tabular regional | crosswalk by subregion / tract GEOID; coarse value assigned to all cells inside (recorded as `res_src`) | eGRID, NRI |
| Tract counts | tract centroids → 1–2 km raster → FFT disc sums (5/50/80 km) | workforce, heat demand |
| Station normals | IDW (k = 8, p = 2) of 1991–2020 NOAA normals | CDD → PUE, HDD |

## 4. Hard gates (applied before scoring)

| Gate | Rule (national, res 6) | Rationale | Source | % CONUS area removed (alone / cumulative) |
|---|---|---|---|---|
| G1 land | < 2 km² NLCD-suitable, unprotected land in cell | 300 MW–1 GW campus needs ≈ 0.5–2 km² | NLCD 2023 + PAD-US 4.1 | 7.1 / 7.1 |
| G2 protected / water | > 80 % of cell protected (GAP 1–2), open water or wetland | no feasible footprint | NLCD + PAD-US | 5.5 / 8.2 |
| G4 transmission | > 50 km to in-service AC line in the 220–287 kV class or above (HVDC excluded) | new HV line cost / multi-year permitting | HIFLD | 14.5 / 20.1 |
| G5 water (scenario) | Aqueduct baseline water stress > 0.8 | only binding for water-cooled designs; base case is dry/DLC | Aqueduct 4.0 | inactive (would remove 28.1 %) |

Local (res 7): G1 ≥ 0.5 km² of suitable land with slope ≤ 10 % outside PAD-US; G3 FEMA SFHA share ≤ 50 %;
G4 ≤ 15 km to 230 kV. Missing gate inputs never exclude a cell; they reduce data confidence instead.

## 5. Features, value functions and weights (locked at Gate 2)

Value v ∈ [0,1], 1 = best. Physical piecewise-linear breakpoints are used wherever a defensible
engineering threshold exists; winsorised (p2–p98) min–max or percentile ranks otherwise, with the
reference population = gate-passing CONUS cells. Percentile gaps are relative, not proportional benefits.

| Pillar (weight) | Feature | Within-pillar weight | Value function |
|---|---|---|---|
| **Energy & Carbon (22)** | grid CO₂e output rate, kg/MWh (eGRID2023) | 0.45 | linear 100 → 700 |
| | clean share (nuclear + renewables) | 0.25 | linear 0.9 → 0.1 |
| | climate PUE (derived from CDD65) | 0.30 | linear 1.08 → 1.17 |
| **Grid & Infrastructure (22)** | distance to ≥ 230 kV, km | 0.50 | linear 5 → 50 |
| | distance to ≥ 345 kV, km | 0.25 | linear 10 → 100 |
| | km of ≥ 230 kV line within 30 km | 0.25 | winsor, log |
| **Climate Resilience (16)** | NRI flood (inland + coastal) annualised frequency | 0.25 | percentile, lower better |
| | NRI wildfire frequency | 0.20 | percentile |
| | NRI hurricane frequency | 0.20 | percentile |
| | NRI heat-wave frequency | 0.15 | percentile |
| | NRI drought frequency | 0.10 | percentile |
| | NRI tornado frequency | 0.10 | percentile |
| **Water (15)** | Aqueduct baseline water stress (ratio) | 0.40 | linear 0.1 → 0.8 |
| | Aqueduct 2050 BAU water stress | 0.25 | linear 0.1 → 0.8 |
| | grid water consumption, L/MWh (eGRID mix × Macknick 2012; hydro excluded) | 0.35 | linear 200 → 2500 |
| **Community & Economic (11)** | working-age (18–64) population within 80 km | 0.35 | winsor, log |
| | skilled-trade + technical occupation share within 80 km | 0.20 | winsor |
| | unemployment rate within 50 km (higher = more local benefit) | 0.15 | winsor |
| | median household income within 50 km (lower = more development need) | 0.10 | winsor, inverted |
| | population density within 5 km (residential burden) | 0.20 | linear 50 → 1000 /km² |
| **Land & Materials (8)** | suitable unprotected land, km² (res 6; res 7 rescaled 2 → 0.5 km²) | 0.55 | linear 15 → 2 |
| | PAD-US GAP 1–2 fraction | 0.25 | linear 0 → 0.8 |
| | open water + wetland fraction | 0.20 | linear 0 → 0.5 |
| **Heat Reuse (6)** | HDD65 × population within 50 km | 0.70 | winsor, log |
| | HDD65 (heating-season length) | 0.30 | linear 1000 → 7000 |

Pillar weights were revised by the team at Gate 2 from the original 22/16/16/15/14/10/7 to emphasise
grid deliverability and climate resilience; the original set is retained as a sensitivity case.

### Double counting
Spearman correlations across all features (`outputs/diagnostics/correlation_res6.csv`; |r| > 0.6 flagged
in `gate2_corr_flags_res6.csv`):
* PUE vs on-site WUE r = 1.0 (both linear in CDD) → **WUE removed from scoring** (kept for impact accounting);
  its weight moved to PUE.
* PUE vs HDD r = −0.96: deliberate — cooling energy (EC) and heat-reuse demand (HR) are different
  consequences of climate. PUE + HDD carry 8.4 % of total weight (6.6 + 1.8); NRI heat-wave frequency
  adds a hazard view (2.4 %).
* Baseline vs 2050 water stress r = 0.98: deliberate present + future view (combined 9.75 % of weight).
* Workforce vs heat demand r = 0.82: population enters CE (labour) and HR (heat sink); documented.

## 6. Missing data and confidence
1. Each pillar must contain ≥ 1 observed feature, else the cell is ineligible.
2. Within a pillar, weights renormalise only if ≥ 50 % of intended pillar weight is observed.
3. Confidence = share of total intended model weight backed by observations; eligibility ≥ 0.75.
4. Coverage is ≈ 99 % for every feature, so thresholds 0.6/0.75/0.9 leave eligibility unchanged
   (`gate2_confidence_res6.csv`). Finalists also receive a missing-data downside test.

## 7. Aggregation (MCDA)
P_p = Σ w_pf·v_f;  **S_G = Π P_p^{W_p}** (primary, ε = 0.01 floor);  S_A = Σ W_p·P_p (sensitivity).
The geometric mean is only partially compensatory: a site cannot buy back a disastrous pillar with
excellence elsewhere.

## 8. Candidate extraction
Top 5 % of eligible cells by S_G (8,349 cells) → greedy non-maximum suppression with 150 km radius →
25 distinct regions (`outputs/diagnostics/shortlist_res6.csv`). Gate 3 approved 8 regions for refinement,
chosen for score and geographic / grid-region diversity (WA, NY×2, OR, UT, WA-east, WY, MN).

## 9. Local refinement (res 7)
Within 50 km of each region's best cell, all features are recomputed on res-7 centroids (no
interpolation of national scores) and land is re-derived at 30 m with: NLCD class, PAD-US, **USGS 3DEP
slope (≤ 10 %)** and **FEMA NFHL Special Flood Hazard Area**. Relative value functions use the national
reference population so local scores are comparable across regions. The best eligible res-7 cell per
region is that region's finalist.

## 10. Robustness (definitions fixed before results)
* **Weights:** pillar weights ~ Dirichlet(κ·W), κ ∈ {50, 100, 200}; within-pillar feature weights ×U(0.8, 1.2)
  then renormalised; 5,000 vectorised draws each.
* **Per finalist:** baseline rank, median rank, P(rank = 1), P(top 5), 5–95 % rank band, rank histogram.
* **Robustness winner:** max P(rank = 1) → better median rank → higher baseline S_G.
* **Method:** geometric vs arithmetic; physical vs all-percentile normalisation; original vs revised vs
  equal pillar weights; hydro-evaporation inclusion in grid water.
* **Pareto:** dominance across the seven pillar scores among finalists.
* **Missing data:** missing v replaced with national p10 and with 0.
