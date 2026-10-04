# 01 — Recommended Location

## Recommendation
**Northwestern Wyoming County, New York (Western New York), about 5 km from Strykersville and 35 km
southeast of Buffalo.**

| | |
|---|---|
| Site centroid | **42.772 °N, −78.446 °W** (H3 res-7 cell `872aa6c44ffffff`, ≈ 5.2 km²) |
| Region | Western New York; NYISO control area; eGRID subregion NYUP (Upstate NY) |
| Overall score | S_G = 0.847 (weighted geometric mean, 0–1); arithmetic S_A = 0.857 |
| Finalist rank | #2 of 8 refined finalists (model); **recommended by team decision at Gate 4** |
| Data confidence | 1.00 (every feature observed) |

### Why this site

| Pillar | Score | Evidence at the site (MODEL-DERIVED) |
|---|---|---|
| Energy & Carbon | 0.92 | Grid output rate 110 kg CO₂e/MWh (NYUP, eGRID2023): 59 % below Loudoun VA and 69 % below the U.S. average. 74 % nuclear + renewable generation. Climate PUE ≈ 1.09 |
| Water | 0.87 | Aqueduct baseline water stress 0.5 % (low), 2050 projection also low. Grid water 1,049 L/MWh (hydro excluded) |
| Grid & Infra | 0.96 | 0.9 km to a ≥ 230 kV line, 9.9 km to ≥ 345 kV |
| Community & Econ | 0.65 | 1.14 M working-age residents within 80 km (Buffalo–Rochester labour shed). Rural surroundings (≈ 0 residents/km² within 5 km at tract resolution) |
| Climate Resilience | 0.66 | No FEMA 1 % floodplain in the cell. Inland location (no hurricane or coastal-flood exposure). Low wildfire. Riverine flooding and tornado/heat frequency drive the remaining risk (winter storms are not scored, see CRITIQUE) |
| Land & Materials | 0.98 | 3.7 km² of NLCD-suitable land (crop/pasture, slope ≤ 10 %) in the cell. No PAD-US protected land. Median slope 3.8 % |
| Heat Reuse | 0.97 | 7,200 heating degree-days (°F) and Buffalo metro heat demand within 50 km. Strong district-heating, greenhouse and agricultural reuse case |

The region has depth: 170 res-7 cells in the 50 km refinement area score within 0.02 of the site.
That leaves room to choose among parcels during land acquisition.

## How the recommendation was reached (transparency)
1. A national screen of 209,488 H3 cells → 25 diverse candidate regions → 8 refined at res 7
   (30 m land, 3DEP slope, FEMA floodplain).
2. By the pre-registered robustness rule (highest P(rank = 1)), the **model's winner is King County, WA**
   (site 47.254, −121.952; S_G 0.861; P(rank 1) = 0.86).
3. **At Gate 4 the team chose Wyoming County, NY instead.** On a 20–30-year view, the deciding factor was
   operating carbon: NYUP's grid emits 110 vs 288 kg CO₂e/MWh for King County's NWPP subregion (−62 %).
   For a 300 MW facility that is ≈ 0.40 Mt CO₂ per year less on a location basis. Combined with the lowest
   baseline water stress of all finalists, a near-best and stable rank, and the second-highest heat-reuse
   score, this outweighed King County's grid-proximity and workforce advantage. King County's location-based
   carbon is also higher than Loudoun's, which undercuts a sustainability-led pitch.
4. Our accepted cost: New York's one-year moratorium on new data centers > 20 MW (enacted July 2026)
   delays permitting to roughly mid-2027. Over a 20–30-year asset life that is a schedule risk, not a
   location flaw. See docs/05.

This override of the rule-based winner is a deliberate, documented judgement. The engine still reports
King County as #1 under the pre-registered rule.

## Runner-ups

| # | Site | S_G | P(rank 1) | Median rank | Note |
|---|---|---|---|---|---|
| Model #1 | King Co, WA (47.254, −121.952) | 0.861 | 0.86 | 1 | Best grid access. Higher-carbon grid; zoning (Enumclaw Plateau APD) and PSE large-load backlog |
| 2 | **Wyoming Co, NY (recommended)** | 0.847 | 0.09 | 3 | P(top 5) = 0.999 |
| 3 | Lewis Co, NY (43.766, −75.472) | 0.845 | 0.05 | 3 | Same grid. Smaller labour shed. Same moratorium |
| 4 | Yamhill Co, OR (45.340, −122.999) | 0.839 | 0.00 | 4 | POWER Act large-load rate class; farmland zoning |
| 5 | Morgan Co, UT (41.034, −111.724) | 0.819 | 0.00 | 5 | Steep terrain limits parcels |

## Uncertainty
* **Score uncertainty:** under 5,000 Dirichlet weight draws (κ = 100) the site's rank stays within 1–4
  (5–95 %). It ranks #2 under geometric and arithmetic aggregation and under original, revised and
  hydro-water variants. It ranks #4 under all-percentile normalisation.
* **Coarse inputs:** grid carbon and grid water come from the eGRID subregion (NYUP), so every NYUP
  site shares them. Local features (land, flood, slope, transmission) decide within the region.
* **Not in any dataset:** parcel ownership, zoning, NYISO interconnection timing, and community
  sentiment. The STAMP data-center controversy in neighbouring Genesee County shows real local risk
  (docs/05).
