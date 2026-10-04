# 03 — Data Analysis

Machine-readable provenance: `config/datasets.yaml` (source URL, vintage, licence) and
`data/raw/_download_log.tsv` (size, download time, SHA-256). Each feature's source, unit, value function,
and weight are in `config/features.yaml`.

## 1. Dataset inventory

| Dataset | Publisher / vintage | Native resolution | Coverage | Licence | Used for | Transformation |
|---|---|---|---|---|---|---|
| eGRID2023 (rev2) + subregion GDB | US EPA, data 2023 (rel. 2025) | 27 subregions (approx. polygons) | US | Public domain | CO₂e rate, clean share, generation mix | point-in-polygon on cell centroid; lb→kg |
| Aqueduct 4.0 | WRI, 2023 | HydroBASINS L6 catchments | Global | CC BY 4.0 | baseline + 2050 BAU water stress | point-in-polygon; 9999 sentinel → 10; arid/low-use → ≥ 0.8 |
| U.S. Climate Normals 1991–2020 | NOAA NCEI | 7,304 stations with annual HDD & CDD | US | Public domain | CDD65 → PUE/WUE; HDD65 | IDW (k = 8, p = 2) in EPSG:5070 |
| HIFLD Electric Power Transmission Lines | DHS HIFLD (ArcGIS Online) | vector, 52,244 lines | US | Public | distance to ≥ 230 / ≥ 345 kV; line density | VOLTAGE (VOLT_CLASS fallback); planned/inactive and HVDC dropped; 220–287 kV class counted as "230"; STRtree nearest |
| FEMA National Risk Index | FEMA, tract table (v1.19+) | 85,154 census tracts | US | Public domain | annualised frequency: flood, wildfire, hurricane, heat wave, drought, tornado | GEOID join to tract centroid; nearest tract (≤ 60 km) |
| ACS 5-year 2019–2023 (B01001, B23025, B19013, C24010) | US Census Bureau | census tract | US | Public domain | workforce, skilled share, unemployment, income, population | tract centroids → 1–2 km raster → FFT radius sums |
| 2023 Gazetteer — tracts | US Census Bureau | tract centroids | US | Public domain | geocoding ACS / NRI | — |
| Annual NLCD Collection 1 — Land Cover 2023 | USGS / MRLC | 30 m | CONUS | Public domain | suitable land, water/wetland | national: 240 m nearest-sample → exactextract fractions; local: native 30 m |
| PAD-US 4.1 (GeoParquet mirror, source.coop) | USGS GAP | polygons | US | Public domain | GAP 1–2 protected areas | rasterised on NLCD grid |
| 3DEP elevation (ImageServer) | USGS | 1/3″ resampled to 30 m | refinement areas | Public domain | slope ≤ 10 % buildability | finite-difference slope |
| FEMA NFHL Flood Hazard Zones (layer 28) | FEMA, live service | polygons | refinement areas, where digitised | Public domain | 1 % annual-chance floodplain (SFHA) share; local gate G3 | rasterised at 30 m |
| Census cartographic boundaries (states, counties, NY places) | US Census Bureau 2023 | 1:500k | US | Public domain | CONUS mask, labelling | — |

Downloads total ≈ 4 GB; no single file > 2 GB; no paid APIs; no credentials.

## 2. Feature store
`data/processed/features_res6.parquet`: 209,488 res-6 cells (7.80 million km²) × 64 columns (raw features,
`cov_*` flags, intermediates). Full build ≈ 8.5 min (`outputs/diagnostics/adapter_timing.json`).
Refinement store: `features_res7_refine.parquet`, 12,049 res-7 cells in 8 regions.

**Coverage.** Missing share per feature (`missingness_res6.csv`): eGRID 0.16 %, Aqueduct 0.1 %, NRI 0.85 %,
income/unemployment ≈ 2.5 % (empty tracts in remote areas), all others 0 %. Every gate-passing cell has
confidence ≥ 0.75, so the confidence threshold does not bind (`gate2_confidence_res6.csv`). NFHL returned
no polygons for Whitman Co WA (R9, likely not digitised), which is recorded as missing rather than zero.

## 3. Feature distributions (gate-passing cells; `feature_distributions_res6.csv`)

| Feature | 5th pct | Median | 95th pct | Value-function breakpoints |
|---|---|---|---|---|
| Grid CO₂e (kg/MWh) | 195 | 356 | 473 | 100 → 700 |
| Clean share | 0.25 | 0.42 | 0.58 | 0.9 → 0.1 |
| Water stress (ratio) | 0.004 | 0.28 | 5.3 | 0.1 → 0.8 |
| Grid water, hydro excl. (L/MWh) | 727 | 1,120 | 1,809 | 200 → 2,500 |
| Distance ≥ 230 kV (km) | 0.8 | 11.8 | 42 | 5 → 50 |
| Suitable land per res-6 cell (km²) | 4.7 | 26.9 | 40.9 | 2 → 15 |
| HDD65 | 1,530 | 5,340 | 8,740 | 1,000 → 7,000 |

Breakpoints were checked against these distributions at Gate 2. Physical thresholds do not saturate the
discriminating range of the carbon, water, or transmission features. Land saturates (most cells have
"enough" land), which is intended: land is a sufficiency criterion.

## 4. Insights
1. **Transmission access is the binding national constraint.** 14.5 % of CONUS is > 50 km from a ≥ 220–230 kV AC
   line, more than all land and protection gates combined (`exclusions.png`).
2. **Grid region is the largest single driver.** eGRID subregion explains 26 % of national S_G variance
   (`plateau_res6.txt`). Upstate NY and the Pacific Northwest dominate the top 5 % because their grids are
   clean (NYUP 110 kg/MWh) or water-light. Local features break ties inside each subregion.
3. **Water stress splits the West.** 28 % of CONUS area exceeds Aqueduct "extremely high" stress (> 0.8).
   Quincy, WA, an existing hub, is held to the 74th percentile mainly by its catchment's stress.
4. **Sanity check of existing markets** (`sanity_markets_res6.csv`): The Dalles 97th percentile, Loudoun
   94th, central Iowa 86th, Quincy 74th, Cheyenne 50th, Abilene 45th, Phoenix 16th. Infrastructure
   distances are plausible: Loudoun 5.5 km, Quincy 1.4 km, Altoona 0.4 km to ≥ 230 kV.
5. **Bugs caught by these checks.** An ArcGIS paging truncation had dropped 38 % of transmission lines
   (Quincy appeared 1,219 km from a line). Treating "status unknown" lines as absent was a second error. Both
   were fixed before methodology lock. A transient FEMA service error that read as "no floodplain" was
   also fixed before the final ranking.

## 5. Assumptions (summary — see `config/scenario.yaml`)
Facility (300 MW, 80 % load), PUE/WUE climate model, Macknick (2012) water factors, hydro exclusion,
AWARE-inspired scarcity factor, heat-recovery fractions, and displaced-boiler EF are **assumptions**.
Everything in the dataset inventory is an **observation** (or a modelled public product, e.g. NRI frequencies).

## 6. Maps (`outputs/maps/`)
`overall_SG.png`, `pillar_{EC,WA,GI,CE,CR,LM,HR}.png`, `exclusions.png`, `confidence.png`, `finalists.png`,
`refine_R*.png` (res-7 regions), `national_interactive.html` (top 25k cells, pillar tooltips), slide figures
`fig_*.png`.

## 7. Limitations
* eGRID subregions and Aqueduct catchments are coarse. Many cells share identical values (plateaus).
* NRI is assigned from the nearest tract centroid (no tract polygons). Rural tracts are large.
* ACS radius sums use tract centroids, so local density in large rural tracts reads as ≈ 0.
* 240 m nearest sampling of NLCD for the national pass (unbiased but noisy for small classes);
  30 m only in refinement.
* HIFLD voltage/status attributes are incomplete (21 % "NOT AVAILABLE" status kept as existing).
* No substation capacity, queue position, fiber, electricity price, or parcel/zoning data in the score.
* Data vintages differ (2019–2023 ACS, 2023 eGRID/NLCD, 1991–2020 normals, live FEMA services).
