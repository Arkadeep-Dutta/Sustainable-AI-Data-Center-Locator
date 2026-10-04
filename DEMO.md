# 5-Minute Judge Demo

## Setup (once, ~3 min; do this before the session)
```powershell
cd siteselect                       # or the unzipped submission/ folder
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
python -m pytest                    # smoke test: all tests should pass (1 may skip without raw data)
.\.venv\Scripts\streamlit run app\streamlit_app.py
```
macOS/Linux: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m pytest && .venv/bin/streamlit run app/streamlit_app.py`

The browser opens at `http://localhost:8501` on the **Final recommendation** view. No data downloads
are needed; the app reads the packaged precomputed files. Open the app once before presenting so the
caches are warm. The Explore view takes ~10 s on first load.

## Click path
| Time | Action | What judges see |
|---|---|---|
| 0:00 | App already open on **Final recommendation** | Recommendation header + 4 metrics |
| 0:45 | Point at the blue box | Why Wyoming was chosen, with King Co shown as model #1 |
| 1:30 | Scroll to **Map** + **Top 5 finalists** | Red dot = Wyoming; table shows model #1 and ★ RECOMMENDED |
| 2:15 | Point at **Robustness** chart | P(rank 1) per finalist; caption shows Wyoming P(top 5) = 99.9 % |
| 2:45 | Scroll to **Sustainability comparison** | CO₂ and water vs Loudoun VA and the CONUS average |
| 3:30 | Sidebar → **Explore & re-weight** | Live national map + top regions (≈ 10 s first load) |
| 3:50 | Drag **Grid & Infrastructure** slider 22 → 35 | Rankings update instantly |
| 4:20 | Tick **Water-cooled design** | Arid West drops out (water-stress gate) |
| 4:40 | Sidebar → back to **Final recommendation** | Close |

## Narration (≈ 5 min)
1. **(0:00) Problem.** "Where should the next sustainable AI data center go? We didn't pick a city and
   justify it. We built an open decision engine that scores every 36 km² of the contiguous U.S. on seven
   pillars: energy and carbon, water, grid, community, climate resilience, land, and heat reuse."
2. **(0:45) Answer.** "The engine's quantitative #1 is King County, Washington. Our recommendation is
   Wyoming County, New York, in the Town of Sheldon, the model's #2. By design, the model produces a robust
   shortlist and the team makes the final call on what public data can't see. King County's site sits on
   rural-zoned land where Washington's Growth Management Act limits major industry, and the neighbouring
   county just banned large data centers. New York's state-permit pause is time-limited."
3. **(1:30) Map and table.** "209,000 hexagons, 20 % removed by hard gates, mostly for distance from
   high-voltage lines. 25 diverse regions, 8 refined at 5 km² with 30-metre land cover, slope, and FEMA
   floodplains. Here are the top five."
4. **(2:15) Robustness.** "We perturbed the weights 5,000 times. King County is #1 in 86 % of draws.
   Wyoming stays top-5 in 99.9 %. We show this openly; the model doesn't hide the trade-off."
5. **(2:45) Impact.** "Same 300 MW design, three locations. Wyoming's grid is 110 kg CO₂/MWh, so operating
   emissions are about 60 % below Loudoun, Virginia, ~375 kilotonnes a year. Water stress is minimal, and
   7,200 heating degree-days make waste-heat reuse (greenhouses, dairy, district heat) realistic."
6. **(3:30) Live engine.** "Everything is configurable. If a judge cares more about grid access, raise its
   weight and the map re-ranks instantly. Switch to a water-cooled design and the arid West drops out. Open
   data, YAML configs, modular adapters: the framework is reusable."
7. **(4:40) Close.** "Risks: New York's permit pause, interconnection, and community acceptance. Our
   30-year plan: dry cooling, 24/7 carbon-free power, a heat network, and OCP circular hardware.
   Full details are in docs/01–06."

## Fallback if Streamlit fails
Show `screenshots/` in this order (any image viewer or the slide deck):

| File | Use for |
|---|---|
| `01_final_recommendation.png` | Steps 1–2: header, metrics, decision box |
| `02_map_and_top5.png` | Step 3: map + top-5 table |
| `03_robustness.png` | Step 4: robustness chart |
| `04_sustainability.png` | Step 5: impact table/chart |
| `05_explore_default.png` | Step 6: live engine (default weights) |
| `06_explore_grid_weight_35.png` | Step 6: after raising the Grid weight to 35 |
| `07_fallback_static_national_map.png` | Static national score map (no browser/WebGL needed) |

Also available offline: `outputs/maps/national_interactive.html` (open in any browser) and the figures in
`outputs/maps/fig_*.png`.

**Common fixes:** blank map → WebGL disabled in the browser (use another browser or fallback 07); port in use
→ `streamlit run app\streamlit_app.py --server.port 8502`.
