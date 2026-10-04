# CRITIQUE — What could make this answer wrong

A candid review of the engine and the recommendation. Issues are ordered roughly by how much they could
change the answer.

### 1. The final pick overrides the pre-registered rule
The robustness rule (max P(rank = 1)) selects **King County, WA** (P = 0.87). The team chose **Wyoming
County, NY** (P(rank 1) = 0.08, median rank 3, P(top 5) = 0.998) on a 20–30-year carbon argument. This is
a value judgement layered on the model: the model treats carbon as 22 % of the decision, while the team
effectively weighted it higher. The override is documented in docs/01 and SPEC §16c, and both sites remain
in the outputs. A reviewer who weights grid access and near-term deliverability more should prefer King
County.

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
Not scored: parcel availability and price, zoning (King County's Enumclaw Plateau APD; NY agricultural
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
2026 brought moratoria (New York State, Seattle), ratepayer-protection laws (Oregon POWER Act, Minnesota,
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

## What more time or data would improve
1. Nodal/hourly marginal emissions (Cambium, WattTime) and interconnection-queue headroom per substation.
2. Parcel and zoning data (Regrid or county assessors) and prime-farmland/ag-district layers.
3. CMIP6 (NEX-GDDP) heat, precipitation, and drought deltas; winter-storm hazard.
4. Electricity price (EIA-861), reliability (SAIDI/SAIFI), fiber/IX (FCC, PeeringDB).
5. Refinement of all 25 regions (cheap: ≈ 1–2 min per region) and res-8 parcel screens.
6. Stakeholder weight elicitation (AHP) and a TOPSIS cross-check.
7. Market-model comparison against existing data-center locations (revealed preference).
