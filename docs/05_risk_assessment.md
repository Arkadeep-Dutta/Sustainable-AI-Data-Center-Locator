# 05 — Risk Assessment: Wyoming County, NY site

Scale: Likelihood (L) and Impact (I) are scored 1–5; score = L × I. **Evidence type:** M = model-derived
(datasets in docs/03), Q = qualitative/public reporting (sources listed at the end). Horizon: N = now to
2030, F = 2030–2055.

## Risk matrix

| # | Risk | Category | Horizon | L | I | Score | Evidence | Mitigation |
|---|---|---|---|---|---|---|---|---|
| 1 | NY one-year moratorium on new data centers > 20 MW (signed Jul 2026), plus statewide DEC environmental review (18 months) with possible new conditions | Regulatory | N | 5 | 3 | **15** | Q | Use the pause for site control, NYISO studies, and community agreements. Design to exceed likely conditions (dry cooling, 24/7 CFE, heat reuse, public hearing). Phase 1 energisation ≥ 2028 |
| 2 | Interconnection delay or cost: a large new load in NYISO Zone A/B needs transmission upgrades; other large loads (STAMP, ≈ 500 MW proposed) compete for the same capacity | Grid / interconnection | N | 4 | 4 | **16** | M (0.9 km to ≥ 230 kV) + Q | Early NYISO large-load study. Phased load ramp (100 → 300 MW). Fund network upgrades. Co-locate storage for flexibility. Use demand response as a grid asset |
| 3 | Community opposition (cf. STAMP in neighbouring Genesee Co: subsidy backlash, Tonawanda Seneca Nation lawsuit over environmental review) | Community | N | 4 | 4 | **16** | Q | Consult the Seneca and Tonawanda Seneca Nations before site control. Community benefits agreement, no tax-abatement-heavy deal, local hiring, heat-reuse dividends, transparent water/energy reporting |
| 4 | Marginal emissions higher than the NYUP average (new load met by gas peakers or imports) | Environmental / carbon | N–F | 4 | 3 | 12 | M (avg 110 kg/MWh) | Hourly-matched 24/7 CFE procurement (NY offshore wind, upstate wind/solar, nuclear PPAs). Additionality requirement. Report location-, market-, and consequential-based emissions |
| 5 | Agricultural land conversion (crop/pasture is the "suitable" class; Wyoming Co is a leading dairy county) | Land / community | N | 3 | 3 | 9 | M (NLCD) + Q | Prefer previously disturbed or lower-productivity parcels among the 170 near-best cells. Compact multi-storey design. Agrivoltaics and greenhouse heat reuse to keep land productive |
| 6 | Riverine flooding and extreme precipitation (increasing with climate change) | Climate | F | 2 | 4 | 8 | M (SFHA 0 % in cell; region 3 %) | Build outside SFHA + 500-yr buffer. Elevate critical systems. On-site stormwater detention |
| 7 | Winter storms / ice (lake-effect snow; not scored by the model) | Climate | N–F | 4 | 2 | 8 | Q | Snow-load design. Redundant feeds. Fuel-free bridging (batteries, fuel cells on RNG/H₂ capable). Staff resilience plans |
| 8 | Heat waves increasing (CMIP6 not yet integrated) | Climate | F | 3 | 2 | 6 | M (NRI) | DLC + dry coolers sized for 2050 design-day temperatures. Adiabatic assist only at peaks |
| 9 | Water: low stress today (0.5 %) but hydro-water attribution could make grid water ≈ 3.5× Loudoun | Water | N–F | 2 | 2 | 4 | M | Dry cooling, reclaimed water for adiabatic assist. Report both water conventions |
| 10 | Workforce depth for construction peak (1.1 M working-age within 80 km; smaller than NoVA) | Economic | N | 3 | 2 | 6 | M | Partner with Buffalo/Rochester trades, SUNY/community-college programmes, union PLAs |
| 11 | Supply chain: transformers and switchgear lead times (2–4 yrs), GPU supply volatility | Supply chain | N | 4 | 3 | 12 | Q | Early procurement of long-lead electrical equipment. OCP-standard modular power/racks. Multi-vendor designs |
| 12 | Policy volatility: ratepayer-protection tariffs, data-center fees, permitting conditions | Regulatory | N–F | 4 | 2 | 8 | Q | Accept cost-causation tariffs. Long-term contracts. Proactive disclosure |
| 13 | Fiber/latency (not scored) | Infrastructure | N | 2 | 2 | 4 | Q | Buffalo is a fiber hub (~35 km). Diverse-path laterals. Training-heavy AI workloads tolerate latency |
| 14 | Model risk: coarse eGRID/Aqueduct inputs, missing zoning/queue data, team override of the rule-based winner | Analytical | N | 3 | 3 | 9 | M | Robustness suite (rank 1–4 under 5,000 weight draws). Parcel-level due diligence before commitment. Rule-based winner (King Co WA) kept as fallback |

**Top risks (score ≥ 15):** interconnection (2), community (3), moratorium (1). All three are
non-physical, timeline risks. The site's physical risk profile (flood, wildfire, hurricane, water) is low.

## Present vs future
* **Now (2026–2030):** regulatory pause, interconnection queue, community licence. Each is a schedule risk.
* **Future (2030–2055):** wetter extremes and more heat-wave days (Northeast), grid decarbonisation
  under NY's CLCPA (70 % renewable by 2030 target, zero-emission grid by 2040). This *reduces* carbon
  risk over time, which is the core of the 20–30-year rationale.

## Comparison to the model's #1 (King Co, WA)
King County has better grid proximity, lower climate-hazard scores, and a larger workforce. Its
qualitative risks are comparable in scale: PSE's large-load requests ≈ 50 % of its peak, Seattle's
moratorium and activists targeting the county, and Enumclaw Plateau agricultural zoning. Its location-based
carbon is 2.6× higher. Neither site is risk-free. The trade is a near-term regulatory delay (NY) against a
persistent carbon and interconnection constraint (WA).

## Sources (qualitative)
* NY moratorium: WAMC 2026-07-14 "Hochul order puts large data centers on hold in NY"; DataCenterDynamics
  "New York becomes first US state to enact data center moratorium"; DLA Piper 2026-02-09.
* STAMP / Genesee Co: Investigative Post 2026-02-04 and 2026-03-18; DataCenterDynamics "Stream proposes large
  data center in Genesee County".
* Washington: Washington State Standard / E&E News on SB 6231; PSE NWESS large-load presentation (Apr 2026);
  Seattle moratorium coverage; WA Data Center Workgroup (dor.wa.gov).
* Oregon POWER Act (HB 3546) & PGE Schedule 96; Utah SB 132; Avista 500 MW pause (Jun 2026); Wyoming
  executive order (Jun 2026); Minnesota 2025 data-center law (HF16).
