# 01 — Recommended Location

## Recommendation
**Town of Sheldon, northwestern Wyoming County, New York (Western New York), about 5 km from
Strykersville and 35 km southeast of Buffalo.**

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

The region has depth: 168 res-7 cells in the 50 km refinement area score within 0.02 of the site.
That leaves room to choose among parcels during land acquisition.

## How the recommendation was reached (transparency)
1. A national screen of 209,488 H3 cells → 25 diverse candidate regions → 8 refined at res 7
   (30 m land, 3DEP slope, FEMA floodplain).
2. **Design of the method:** the quantitative engine produces a robust shortlist. The final choice among
   the top finalists is made by manual review, to cover what public datasets cannot capture (zoning,
   regulation, interconnection, community context) and the model's own variance.
3. By the pre-registered robustness rule (highest P(rank = 1)), the **model's top finalist is King County,
   WA** (site 47.254, −121.952; S_G 0.861; P(rank 1) = 0.86). Wyoming County is a close #2 (S_G 0.847;
   P(top 5) = 0.999; median rank 3).
4. **At Gate 4 the team selected Wyoming County, NY** on the political and regulatory landscape and current
   events. Qualitative evidence (sources in docs/05):
   * **King County site:** the model's cell is zoned **RA-10 Rural Area**, outside the Urban Growth Area,
     next to single-family parcels. Washington's Growth Management Act does not permit major industrial
     development in rural areas except through the RCW 36.70A.365 master-planned process. The local
     county councilmember has publicly opposed data centers on rural-zoned land. Adjacent Pierce County
     enacted an emergency ban on new data centers > 10 MW in unincorporated areas (Aug 2026). Puget Sound
     Energy reports large-load requests ≈ 50 % of its peak.
   * **Wyoming County site:** New York's pause is temporary. Executive Order 62 (14 Jul 2026) halts
     *state discretionary* permits for data centers ≥ 50 MW for up to one year, or until the statewide
     environmental review and standards are complete. It does not cover local approvals. No town or county
     action against data centers was found for Sheldon or Wyoming County.
   * **Sustainability context (already scored by the model, not an additional factor):** NYUP grid
     110 vs 288 kg CO₂e/MWh for King County's NWPP subregion (−62 %, ≈ 0.40 Mt CO₂/yr at 300 MW), and the
     lowest water stress of all finalists.
5. Accepted cost: the EO 62 pause delays state permits to roughly mid-2027, and the legislature's stricter
   ≥ 20 MW bill (passed June 2026, unsigned as of late August) may add conditions. Over a 20–30-year asset
   life that is a schedule and compliance risk, not a location flaw. See docs/05.

The engine's quantitative ranking is reported unchanged. The recommendation reflects the team's
pre-planned manual decision step applied to the model's top finalists.

## Runner-ups

| # | Site | S_G | P(rank 1) | Median rank | Note |
|---|---|---|---|---|---|
| Model #1 | King Co, WA (47.254, −121.952) | 0.861 | 0.86 | 1 | Best grid access. Higher-carbon grid; site zoned RA-10 rural (GMA limits on major industry); PSE large-load backlog; Pierce Co ban adjacent |
| 2 | **Wyoming Co, NY (recommended)** | 0.847 | 0.09 | 3 | P(top 5) = 0.999 |
| 3 | Lewis Co, NY (43.766, −75.472) | 0.845 | 0.05 | 3 | Same grid. Smaller labour shed. Same EO 62 pause |
| 4 | Yamhill Co, OR (45.340, −122.999) | 0.839 | 0.00 | 4 | POWER Act large-load rate class; farmland zoning |
| 5 | Morgan Co, UT (41.034, −111.724) | 0.819 | 0.00 | 5 | Steep terrain limits parcels |

## Uncertainty
* **Score uncertainty:** under 5,000 Dirichlet weight draws (κ = 100) the site's rank stays within 1–4
  (5–95 %). It ranks #2 under geometric and arithmetic aggregation and under original, revised and
  hydro-water variants. It ranks #4 under all-percentile normalisation.
* **Coarse inputs:** grid carbon and grid water come from the eGRID subregion (NYUP), so every NYUP
  site shares them. Local features (land, flood, slope, transmission) decide within the region.
* **Not in any dataset:** parcel ownership, zoning, NYISO interconnection timing, and community
  sentiment. The Town of Sheldon is revising its zoning law (draft dated 22 Jul 2026), and its treatment
  of data centers is not yet known. The STAMP data-center controversy in neighbouring Genesee County shows real local risk
  (docs/05).
