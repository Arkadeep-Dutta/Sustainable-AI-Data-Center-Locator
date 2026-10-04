# 04 — Sustainability Impact Assessment

**Scope.** The same facility design is placed at three locations, so every difference below comes from
**location**, not technology:
1. the recommended site (Wyoming Co, NY);
2. Loudoun County, VA (the largest existing U.S. data-center market);
3. a CONUS-average baseline (U.S. eGRID2023 average grid; median climate and water stress of
   gate-passing CONUS cells).

Calculations: `siteselect/impact.py` → `outputs/diagnostics/impact.csv`, inputs in `impact_inputs.json`.

## Design assumptions (ASSUMPTIONS — `config/scenario.yaml`)
| Parameter | Value |
|---|---|
| IT capacity | 300 MW base (sensitivity 100 MW – 1 GW) |
| Average utilisation | 80 % → 2.10 TWh IT energy/yr at 300 MW |
| Cooling | direct-to-chip liquid + dry coolers with adiabatic assist |
| PUE model | 1.08 + 2×10⁻⁵ × CDD65 (observed NOAA 1991–2020 cooling degree-days) |
| On-site WUE model | 0.02 + 6×10⁻⁵ × CDD65 L/kWh_IT |
| Grid emission factor | eGRID2023 subregion CO₂e output rate (location-based **average**) |
| Grid water | eGRID generation mix × Macknick et al. (2012) median consumption factors; hydro reservoir evaporation excluded (sensitivity: included) |
| Scarcity weighting | AWARE-*inspired* factor CF = local Aqueduct water stress ÷ CONUS median (0.283), clipped to [0.1, 10]. **Not a formal AWARE implementation** |
| Heat recovery | 60–80 % of IT heat recoverable at 45–60 °C; 10–30 % of it put to use; displaces natural-gas boilers (0.20 t CO₂/MWh_th) net of heat-pump uplift electricity (COP 3) |

## Results — 300 MW IT, per year

| Metric | **Wyoming Co, NY** | Loudoun Co, VA | CONUS average | vs Loudoun | vs CONUS |
|---|---|---|---|---|---|
| Climate PUE | 1.088 | 1.101 | 1.099 | −1.2 % | −1.0 % |
| Facility energy (TWh) | 2.29 | 2.32 | 2.31 | −1.2 % | −1.0 % |
| Grid carbon intensity (kg CO₂e/MWh) | 110 | 270 | 350 | −59 % | −69 % |
| **Operational CO₂e, location-based (kt)** | **252** | 626 | 808 | **−60 %** | **−69 %** |
| … with 60 % 24/7 carbon-free procurement | 101 | 251 | 323 | | |
| … with 90 % 24/7 carbon-free procurement | 25 | 63 | 81 | | |
| On-site water (thousand m³) | 90 | 177 | 160 | −49 % | −44 % |
| Off-site grid water, hydro excluded (million m³) | 2.40 | 3.79 | 2.92 | −37 % | −18 % |
| Off-site grid water, hydro included (million m³) | 15.2 | 4.3 | 5.2 | **+250 %** | **+194 %** |
| Scarcity-weighted total water (million m³-eq) | 0.25 | 0.78 | 3.08 | −68 % | −92 % |
| Recoverable waste heat (TWh_th) | 1.26–1.68 | same design | same design | | |
| Avoided CO₂ from heat reuse (kt) | 21–82 | 14–55 | 11–42 | | |

**Scale range (Wyoming Co):** 100 MW → 84 kt CO₂e and 0.83 million m³ grid water; 1 GW → 839 kt and
8.0 million m³.

## Interpretation (and honest caveats)
* **Carbon is the headline benefit.** Moving the same 300 MW load from Loudoun to Wyoming County avoids
  ≈ **375 kt CO₂e/yr** on a location basis, about 80,000 passenger cars' worth (EPA, 4.6 t/car/yr).
  This rests on the NYUP *average* emission rate (nuclear + hydro + wind heavy). New load is met at the
  margin, often by gas, so marginal emissions are higher (see CRITIQUE). That is why 24/7
  carbon-free procurement is part of the implementation plan (docs/06).
* **Water depends on the hydro convention.** Excluding hydro reservoir evaporation, the site uses 37 %
  less grid water than Loudoun. Including it, NYUP's hydro share (Niagara and St. Lawrence) makes grid
  water ≈ 3.5× higher. Both figures are reported because the attribution of multi-purpose reservoir
  evaporation is contested. Scarcity weighting favours the site under either convention: local
  water stress is 0.5 % vs 5.6 % at Loudoun. The CF hits its 0.1 floor here, so the scarcity-weighted
  benefit is bounded by an assumption.
* **On-site water is small by design.** Dry cooling with adiabatic assist keeps on-site use ≈ 90,000 m³/yr.
  A conventional evaporative-cooled facility of this size would use an order of magnitude more.
* **Heat reuse is real but must be built.** 7,200 HDD and the Buffalo metro within 50 km create
  demand, but useful reuse requires partners: district heating, greenhouses, food processing, and
  the agricultural economy of Wyoming County (NY's top dairy county). The 10–30 % utilisation range is
  an assumption, not a commitment.
* **PUE differences are small** because direct-to-chip cooling decouples efficiency from climate. Siting
  matters far more for carbon and water than for PUE.

## Embodied carbon and materials (qualitative)
Not quantified. Building Transparency EC3 and the GEM steel/cement trackers were deferred (P1)
and no facility bill of materials exists. Opportunities documented for docs/06:
* rail-served Western NY logistics for low-clinker cement and recycled-content steel from Great Lakes
  mills;
* mass-timber or low-carbon concrete for non-critical structures;
* OCP-standard modular, reusable racks and power shelves to cut refresh-cycle embodied carbon.

## What the numbers do not include
Construction emissions, backup generation, transmission upgrades, refrigerant leakage, Scope-3 hardware,
and marginal-emission effects of new load. Ranges reflect assumption bands, not statistical intervals.
