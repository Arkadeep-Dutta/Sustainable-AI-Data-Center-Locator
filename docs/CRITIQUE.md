# CRITIQUE — What could make this answer wrong

A candid review of the engine and the recommendation. Issues are ordered roughly by how much they could
change the answer.

### 1. The final pick is a manual decision among the top finalists
The robustness rule (max P(rank = 1)) ranks **King County, WA** first (P = 0.86). By design, the team used
the engine to produce a shortlist and then decided manually among the top finalists. It chose **Wyoming
County, NY** (P(rank 1) = 0.09, median rank 3, P(top 5) = 0.999) on the political/regulatory landscape and
current events (docs/01, docs/05):
* the King County model site is RA-10 rural land under Growth Management Act limits;
* adjacent Pierce County enacted a > 10 MW ban;
* NY's EO 62 pause is time-limited.

Caveats a reviewer should weigh:
* Grid carbon and water are already in the score. Purely on the model's terms, Wyoming overtakes King
  only if Energy & Carbon weight rises from 22 % to ≥ 29 %.
* Relocating within King County to Urban Growth Area or industrial-zoned land (132 near-best cells) was not
  tested.
* The Town of Sheldon's zoning treatment of data centers is unverified (law under revision).
* NY's legislature passed a stricter ≥ 20 MW bill that, if signed, could add lasting conditions.

Both sites remain in all outputs.

### 2. Weight subjectivity and robustness
Pillar weights (EC 22, GI 22, CR 16, WA 15, CE 11, LM 8, HR 6) were set by the team at Gate 2, revised
from an original 22/16/16/15/14/10/7. The finalist ordering is stable under Dirichlet perturbation
(κ = 50/100/200, ±20 % feature jitter) and under original or equal weights. But Dirichlet noise around
*our* weights does not represent stakeholders with fundamentally different priorities. An AHP or
stakeholder-elicitation exercise (P1, not done) would be better.

### 3. Normalisation effects
Physical breakpoints (e.g. carbon 100 → 700 kg/MWh) encode judgements about what "good" and "bad" mean.
Switching all features to percentile ranks moves Wyoming Co from #2 to #4 and Lewis Co to #2. The
national top-25 list changes substantially (Wyoming Co was #1,201 nationally under percentile mode).
Percentile scores are relative and exaggerate small differences inside crowded distributions.

### 4. Compensatory aggregation
The geometric mean is only partially non-compensatory. A site with 0.66 climate resilience can still win
on other pillars. Hard gates are the only fully non-compensatory element. Arithmetic aggregation gave the
same finalist order, which suggests this choice is not decisive here.

### 5. Coarse regional datasets, plateaus, and MAUP
eGRID subregions (27 polygons, approximate boundaries) drive EC and part of WA. Every cell in NYUP gets
110 kg/MWh, whether it sits next to Niagara hydro or a gas plant. Subregion explains 26 % of national score
variance. The final choice between NY and WA is largely a choice between two eGRID polygons. Aqueduct
catchments, NRI tract centroids, and station-interpolated normals add further plateaus. Results depend on
these zoning units (modifiable areal unit problem). Balancing-authority or nodal emission data would be
more defensible.

### 6. Spatial-resolution mismatch
Features range from 30 m (NLCD) to ~100,000 km² (eGRID) and are combined on a 36 km² (national) or
5 km² (local) hexagon. A res-6 cell is a screening region: a high score means the region probably
contains a good site, not that every parcel is good. NLCD was sampled at 240 m nationally.

### 7. Coarse-to-fine search can miss the optimum
Only 8 of 25 regions were refined, and NMS kept one region per 150 km. A region that scored modestly at
res 6 (e.g. because a large share of its cell was unsuitable) could contain an excellent res-7 site. The
regions dropped at Gate 3 (e.g. Skagit WA, Otsego NY, San Benito CA) were not refined.

### 8. Average vs marginal emissions; uncertain future grid
All carbon figures use average location-based rates. A new 300 MW load is served at the margin, often by
gas, which can be several times the NYUP average. eGRID2023 is a snapshot; NY's CLCPA and WA's CETA trajectories,
interconnection queues (LBNL *Queued Up*), and Cambium long-run marginal rates were not integrated (P1).
The 60–69 % carbon advantage over Loudoun/CONUS should be read as "the regional grid is cleaner", not as
a consequential emissions reduction.

### 9. Water accounting conventions
The hydro-evaporation choice flips the grid-water comparison (−37 % vs +250 % vs Loudoun). The scarcity
factor is AWARE-inspired, not AWARE. At the site it hits its 0.1 floor, so the scarcity-weighted benefit
is partly an assumption. Aqueduct 2050 projections carry large model uncertainty.

### 10. Missing data
Coverage is ≈ 99 %, so confidence rules rarely bind. Missing data is not the main risk; *absent
variables* are (next item). Whitman Co (R9) lacks digitised FEMA floodplains. NFHL "no polygons" is
ambiguous between "no flood risk" and "not mapped".

### 11. Omitted variables
Not scored: parcel availability and price, zoning (King County's RA-10 rural zoning and GMA urban-growth limits; NY agricultural
districts), substation capacity and interconnection queue position, electricity price, fiber/IX proximity,
winter-storm/ice hazard, CMIP6 future climate, seismic, low-carbon steel/cement supply, existing data-center
saturation, tax incentives, and community sentiment. Several of these (moratoria, opposition, utility
backlog) dominated the qualitative Gate-4 discussion. Leaving out the factors that matter most for
near-term feasibility is the engine's largest blind spot.

### 12. Public parcel data limitations
"Suitable land" is land cover (crop, pasture, grass, shrub, barren, developed-open/low) with slope ≤ 10 %
and no PAD-US protection. It says nothing about ownership, assemblage, zoning, easements, or
prime-farmland status. In agricultural regions (Wyoming Co, Enumclaw Plateau, Yamhill Co) this
overstates buildable supply.

### 13. Interconnection politics and community sentiment
2026 brought moratoria (New York State EO 62 for ≥ 50 MW state permits; Seattle city limits; Pierce
County WA > 10 MW), ratepayer-protection laws (Oregon POWER Act, Minnesota,
Utah SB 132), and utility pauses after pushback (Avista). No open dataset captures this, and it changes
faster than any data vintage. The qualitative layer is a snapshot as of October 2026.

### 14. Data vintage
ACS 2019–2023, eGRID 2023, NLCD 2023, normals 1991–2020 (a warming climate makes these optimistic for
cooling), HIFLD snapshot of uneven currency (21 % unknown status), and live NRI/NFHL services that can change.

### 15. Implementation and QA lessons
Three data bugs (ArcGIS page truncation, status filtering, a transient service error read as "no flood")
would each have changed the ranking. All were caught by sanity checks against known markets. Hard
failures on service errors and count verification are now built into the pager. Adapter-level tests
exist only for core logic and a smoke test. More adapter unit tests would be prudent.

**Post-lock audit (C24010).** I verified the ACS occupation line numbers against the official 2023 5-year
table shell (`scripts/verify_c24010.py`). The original mapping used the 007 subtotal, which includes
life/physical/social-science occupations. It was replaced with 008 + 009 (computer/math +
architecture/engineering) to measure data-center-relevant technical labour. Effect
(`outputs/diagnostics/c24010_fix_comparison.csv`):
* finalist sites, geometric/arithmetic/weight-variant ranks, and the national top-25 regions are unchanged;
* finalist CE scores change by ≤ 0.011 (largest: Whitman WA, a university town);
* R1's P(rank 1) moved from 0.874 to 0.860 and R2's from 0.082 to 0.087.

**Post-lock audit (transmission).** 10 HVDC lines (e.g. Pacific DC Intertie, CU line, Quebec–New England,
CHPE) had been counted as "≥ 230 kV access". They are now excluded, because a load cannot tap a
point-to-point HVDC line without a converter station. Five 220 kV AC lines (220–287 kV class) are now
included. Nationally, 480 cells along HVDC corridors newly fail G4 (14.2 → 14.5 % of CONUS) and the
largest single-cell score change is −0.47. The finalists, their ranks, and the national top-25 regions are
unchanged (`outputs/diagnostics/pre_tx_fix_comparison.csv`). The VOLT_CLASS fallback never triggers
(no invalid VOLTAGE values).

**Post-lock audit (scoring and impact).** Within-pillar renormalisation, the 50 % observed-weight rule,
and geometric aggregation were reviewed: no defect. Impact unit chains were verified; the heat-pump
credit is conservative (docs/04). The res-7 land rescale was factored out and unit-tested. A latent empty
`rank_A` column in res-7 scores was fixed (not used by any reported result).

## What more time or data would improve
1. Nodal/hourly marginal emissions (Cambium, WattTime) and interconnection-queue headroom per substation.
2. Parcel and zoning data (Regrid or county assessors) and prime-farmland/ag-district layers.
3. CMIP6 (NEX-GDDP) heat, precipitation, and drought deltas; winter-storm hazard.
4. Electricity price (EIA-861), reliability (SAIDI/SAIFI), fiber/IX (FCC, PeeringDB).
5. Refinement of all 25 regions (cheap: ≈ 1–2 min per region) and res-8 parcel screens.
6. Stakeholder weight elicitation (AHP) and a TOPSIS cross-check.
7. Market-model comparison against existing data-center locations (revealed preference).
