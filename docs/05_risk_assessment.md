# 05 — Risk Assessment: Wyoming County, NY site

Scale: Likelihood (L) and Impact (I) are scored 1–5; score = L × I. **Evidence type:** M = model-derived
(datasets in docs/03), Q = qualitative/public reporting (sources listed at the end). Horizon: N = now to
2030, F = 2030–2055.

## Risk matrix

| # | Risk | Category | Horizon | L | I | Score | Evidence | Mitigation |
|---|---|---|---|---|---|---|---|---|
| 1 | NY Executive Order 62 (14 Jul 2026): pause on state discretionary permits for data centers ≥ 50 MW, for up to one year or until a statewide GEIS and standards (energy, water, air, noise, disadvantaged communities) are complete. Local approvals not covered. The legislature's ≥ 20 MW bill (90 % renewable by 2040, full cost recovery) passed in June 2026 and was unsigned as of late August; it could add conditions | Regulatory | N | 5 | 3 | **15** | Q | Use the pause for site control, NYISO studies, and community agreements. Design to exceed likely conditions (dry cooling, 24/7 CFE, heat reuse, public hearing). Phase 1 energisation ≥ 2028 |
| 2 | Interconnection delay or cost: a large new load in NYISO Zone A/B needs transmission upgrades; other large loads (STAMP, ≈ 500 MW proposed) compete for the same capacity | Grid / interconnection | N | 4 | 4 | **16** | M (0.9 km to ≥ 230 kV) + Q | Early NYISO large-load study. Phased load ramp (100 → 300 MW). Fund network upgrades. Co-locate storage for flexibility. Use demand response as a grid asset |
| 3 | Community opposition (cf. STAMP in neighbouring Genesee Co: subsidy backlash, Tonawanda Seneca Nation lawsuit over environmental review) | Community | N | 4 | 4 | **16** | Q | Consult the Seneca and Tonawanda Seneca Nations before site control. Community benefits agreement, no tax-abatement-heavy deal, local hiring, heat-reuse dividends, transparent water/energy reporting |
| 4 | Marginal emissions higher than the NYUP average (new load met by gas peakers or imports) | Environmental / carbon | N–F | 4 | 3 | 12 | M (avg 110 kg/MWh) | Hourly-matched 24/7 CFE procurement (NY offshore wind, upstate wind/solar, nuclear PPAs). Additionality requirement. Report location-, market-, and consequential-based emissions |
| 5 | Agricultural land conversion (crop/pasture is the "suitable" class; Wyoming Co is a leading dairy county) | Land / community | N | 3 | 3 | 9 | M (NLCD) + Q | Prefer previously disturbed or lower-productivity parcels among the 168 near-best cells. Compact multi-storey design. Agrivoltaics and greenhouse heat reuse to keep land productive |
| 6 | Riverine flooding and extreme precipitation (increasing with climate change) | Climate | F | 2 | 4 | 8 | M (SFHA 0 % in cell; region 3 %) | Build outside SFHA + 500-yr buffer. Elevate critical systems. On-site stormwater detention |
| 7 | Winter storms / ice (lake-effect snow; not scored by the model) | Climate | N–F | 4 | 2 | 8 | Q | Snow-load design. Redundant feeds. Fuel-free bridging (batteries, fuel cells on RNG/H₂ capable). Staff resilience plans |
| 8 | Heat waves increasing (CMIP6 not yet integrated) | Climate | F | 3 | 2 | 6 | M (NRI) | DLC + dry coolers sized for 2050 design-day temperatures. Adiabatic assist only at peaks |
| 9 | Water: low stress today (0.5 %) but hydro-water attribution could make grid water ≈ 3.5× Loudoun | Water | N–F | 2 | 2 | 4 | M | Dry cooling, reclaimed water for adiabatic assist. Report both water conventions |
| 10 | Workforce depth for construction peak (1.1 M working-age within 80 km; smaller than NoVA) | Economic | N | 3 | 2 | 6 | M | Partner with Buffalo/Rochester trades, SUNY/community-college programmes, union PLAs |
| 11 | Supply chain: transformers and switchgear lead times (2–4 yrs), GPU supply volatility | Supply chain | N | 4 | 3 | 12 | Q | Early procurement of long-lead electrical equipment. OCP-standard modular power/racks. Multi-vendor designs |
| 12 | Policy volatility: ratepayer-protection tariffs, data-center fees, permitting conditions | Regulatory | N–F | 4 | 2 | 8 | Q | Accept cost-causation tariffs. Long-term contracts. Proactive disclosure |
| 13 | Fiber/latency (not scored) | Infrastructure | N | 2 | 2 | 4 | Q | Buffalo is a fiber hub (~35 km). Diverse-path laterals. Training-heavy AI workloads tolerate latency |
| 14 | Model risk: coarse eGRID/Aqueduct inputs, missing zoning/queue data, team override of the rule-based winner | Analytical | N | 3 | 3 | 9 | M | Robustness suite (rank 1–4 under 5,000 weight draws). Parcel-level due diligence before commitment. Rule-based winner (King Co WA) kept as fallback |

**Top risks (score ≥ 15):** interconnection (2), community (3), EO 62 state-permit pause (1). All three are
non-physical, timeline risks. The site's physical risk profile (flood, wildfire, hurricane, water) is low.

## Present vs future
* **Now (2026–2030):** regulatory pause, interconnection queue, community licence. Each is a schedule risk.
* **Future (2030–2055):** wetter extremes and more heat-wave days (Northeast), grid decarbonisation
  under NY's CLCPA (70 % renewable by 2030 target, zero-emission grid by 2040). This *reduces* carbon
  risk over time, which is the core of the 20–30-year rationale.

## Comparison to the model's #1 (King Co, WA)
King County has better grid proximity, lower climate-hazard scores, and a larger workforce. Its
qualitative risks:
* the model's cell is zoned RA-10 Rural Area outside the Urban Growth Area, where the Growth Management
  Act restricts major industrial development (RCW 36.70A.070(5), .365), so siting would require relocation
  or a master-planned designation;
* the local county councilmember publicly opposes data centers on rural-zoned land;
* adjacent Pierce County enacted an emergency ban on new data centers > 10 MW in unincorporated areas
  (Aug 2026);
* PSE's large-load requests are ≈ 50 % of its peak.

Seattle's one-year moratorium (June 2026) applies only within city limits, not to this unincorporated site.
King County's location-based carbon is 2.6× higher. Neither site is risk-free. The trade is a time-limited
state permitting pause (NY) against a structural land-use constraint at the model's site plus a
persistent carbon and interconnection constraint (WA).

## Sources (qualitative)
* NY pause: Executive Order 62 (2026-07-14), summarised by Jones Day "New York Enacts First Statewide Data
  Center Moratorium" (Jul 2026) and Barclay Damon / Davis Polk client alerts; WAMC 2026-07-14. Legislature's
  S10642/A11560: Greenberg Traurig (Jun 2026); Spectrum News 2026-08-27 (sponsor urging signature).
* Town of Sheldon: townofsheldonny.gov (proposed new zoning law, draft 2026-07-22). NYISO large-load queue
  and PSC proceeding 26-E-0045 (Feb 2026).
* STAMP / Genesee Co: Investigative Post 2026-02-04 and 2026-03-18; DataCenterDynamics "Stream proposes large
  data center in Genesee County".
* Washington: Washington State Standard / E&E News on SB 6231; PSE NWESS large-load presentation (Apr 2026);
  Seattle moratorium coverage; WA Data Center Workgroup (dor.wa.gov). King County GIS zoning service
  (site: RA-10, outside UGA, not in an APD/FPD); RCW 36.70A; Seattle Red 2026-09-02 (Councilmember
  Dunn on rural zoning); Pierce County notice (Aug 2026, > 10 MW ban).
* Oregon POWER Act (HB 3546) & PGE Schedule 96; Utah SB 132; Avista 500 MW pause (Jun 2026); Wyoming
  executive order (Jun 2026); Minnesota 2025 data-center law (HF16).
