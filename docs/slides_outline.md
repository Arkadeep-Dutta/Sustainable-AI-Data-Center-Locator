# Slides outline (8 slides, ≈ 6–8 min)

| # | Title | Key message | Visual |
|---|---|---|---|
| 1 | **Don't just find a site — build the engine** | An open, reproducible decision engine screened every ~36 km² of CONUS (209,488 hexagons) across 7 pillars. Recommendation: **Wyoming County, NY (42.77 N, 78.45 W)** | `outputs/maps/overall_SG.png` with the recommended site starred |
| 2 | How the engine works | 15 open datasets → modular adapters → H3 feature store → hard gates → physical value functions → geometric-mean MCDA → diversified shortlist → 30 m refinement → robustness. All of it is YAML-configured | Pipeline diagram from docs/02 §1 |
| 3 | What rules a place out | 20 % of CONUS fails hard gates. Transmission (> 50 km from 230 kV) removes 14 %, more than land and protection combined. A water-cooled design would remove another 28 % | `outputs/maps/exclusions.png` + gate table |
| 4 | Where the seven pillars agree | Pillar maps; clean, low-stress grids (Upstate NY, Pacific NW) dominate. Sanity check: Loudoun 98th percentile, Phoenix 9th | 2×4 grid of `pillar_*.png` + sanity bar |
| 5 | From 25 regions to one site | 25 diverse regions → 8 refined at res 7 (3DEP slope, FEMA floodplain, PAD-US, 30 m land) → finalists | `finalists.png` + `refine_R2.png` |
| 6 | Stress-tested, and an honest choice | 5,000 weight draws × 3 uncertainty levels. King Co WA is the rule-based #1 (P = 0.87). Wyoming Co NY is a stable top-3 (P(top 5) = 0.998) with a 62 % cleaner grid. **The team chose carbon for a 30-year asset** | `fig_robustness_ranks.png` + `fig_pillars_compare.png` |
| 7 | Impact and risk | vs Loudoun at 300 MW: −60 % operational CO₂ (−375 kt/yr), −68 % scarcity-weighted water, 1.3–1.7 TWh_th reusable heat. Top risks: NY moratorium (to mid-2027), interconnection, community. Mitigations | `fig_impact.png` + top-5 risk matrix from docs/05 |
| 8 | 30-year vision and reuse of the engine | Phases 0–4: licence → 100 MW DLC + dry cooling + 24/7 CFE → 300 MW + heat network (greenhouses, dairy, district heat) → OCP circular hardware → adapt or repurpose. Live demo: re-weight and re-rank in Streamlit | Phase timeline + Streamlit screenshot |

**Backup slides:** CRITIQUE highlights (eGRID plateau, average vs marginal carbon, omitted zoning), data
inventory table (docs/03), full finalist table (`outputs/finalists_rankings.csv`).

**Demo script (60 s):** `streamlit run app/streamlit_app.py`. Show the default map → raise Grid weight to 35
(PNW rises) → toggle water-cooled design (arid West drops out) → switch to arithmetic aggregation → open the
Wyoming Co detail panel.
