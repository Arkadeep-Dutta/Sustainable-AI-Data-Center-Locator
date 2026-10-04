# Sustainable AI Data Center Site-Selection Engine

An open, reproducible decision engine that screens every ~36 km² of the contiguous U.S. for a
next-generation sustainable AI data center across **seven pillars**: Energy & Carbon, Water,
Grid & Infrastructure, Community & Economic, Climate Resilience, Land & Materials, and Heat Reuse.
It then refines the best regions at site scale and stress-tests the answer.

Built for the "Where Should America's Next Sustainable Data Center Be Built?" challenge. The point
is the framework more than any single answer: open data, YAML-configured methodology, and modular
dataset adapters, in the spirit of OCP.

## Architecture

```
config/            datasets.yaml  features.yaml  weights.yaml  gates.yaml  scenario.yaml
siteselect/
  download.py      fetch + register raw data (HTTP / ArcGIS FeatureServer pager)
  grid.py          CONUS H3 grid (EPSG:4326 storage, EPSG:5070 metrics)
  adapters/        one module per dataset -> H3-keyed features + cov_* flags
  features.py      feature store builder (data/processed/features_res<N>.parquet)
  valuefn.py       physical piecewise-linear / winsor / percentile value functions
  gates.py         hard constraints (national + local)
  scoring.py       pillar scores, geometric + arithmetic MCDA, data confidence
  candidates.py    top-pool + non-maximum suppression
  refine.py        res-7 local refinement (30 m NLCD, 3DEP slope, FEMA SFHA)
  robustness.py    Dirichlet weight Monte Carlo, Pareto, missing-data downside
  finalists.py     finalist selection + robustness suite
  impact.py        sustainability impact calculations (docs/04)
  maps.py          static + interactive maps
  run.py           stage runner
app/streamlit_app.py   interactive re-weighting demo (precomputed features only)
docs/              SPEC + six deliverables + slides outline + critique
outputs/           rankings.csv, candidates.geojson, maps/, diagnostics/
```

## Run it

```powershell
python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
python -m siteselect.download                 # ~4 GB of open data (skips files already present)
python -m siteselect.features --res 6         # feature store, ~8.5 min
python -m siteselect.run --stage score --res 6
python -m siteselect.run --stage candidates --res 6
python -m siteselect.refine                   # res-7 refinement of approved regions (~40 min, web services)
python -m siteselect.finalists                # robustness suite
python -m siteselect.export                   # rankings.csv, candidates.geojson, maps
streamlit run app/streamlit_app.py            # demo
pytest -q
```

## 5-minute demo script
```powershell
python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
python -m pytest                                   # one-command smoke test
.\.venv\Scripts\streamlit run app\streamlit_app.py  # opens on "Final recommendation"
```
1. **Final recommendation** view (default): Wyoming Co, NY recommended, with King Co, WA shown as model #1.
   Then the top-5 table, robustness chart, sustainability comparison, and map.
2. Sidebar → **Explore & re-weight**: drag *Grid & Infrastructure* to 35 to re-rank live; tick
   *Water-cooled design* to activate the water gate.

Full click path, narration and fallback screenshots: `DEMO.md`. Slides: `docs/presentation_5min.md`.
Screenshots: `screenshots/`.

## Add a dataset
1. Register it in `config/datasets.yaml` (url, vintage, license, file).
2. Write `siteselect/adapters/<name>.py` with `build(cells) -> DataFrame` (index aligned to `cells`),
   returning raw features plus `cov_<feature>` booleans. Use the helpers in `adapters/_util.py`
   (point-in-polygon, nearest, IDW, FFT radius sums).
3. Register each analytical feature in `config/features.yaml` (pillar, unit, source, value function, weight).
4. Add the adapter name to `ADAPTERS` in `features.py` and run `python -m siteselect.features --res 6 --only <name>`.

## Change weights or scenario
* Pillar weights: `config/weights.yaml`. Feature weights and value functions: `config/features.yaml`.
* Facility assumptions (IT MW, PUE/WUE model, CFE share, grid water factors, hydro inclusion):
  `config/scenario.yaml`.
* Gates: `config/gates.yaml`. Setting `cooling.water_cooled_scenario: true` activates the water-stress gate.
* Re-scoring needs no spatial recomputation: `python -m siteselect.run --stage score`.

## Reuse elsewhere or with new data vintages
* **Another U.S. region:** pass a mask polygon to `grid.cells(res, mask=...)`. All adapters work on any
  cell set.
* **New vintages:** update the URL/file in `datasets.yaml`, then delete the matching cache in `data/interim/`.
* **Outside the U.S.:** replace the U.S.-specific adapters (eGRID, NRI, ACS, HIFLD) with equivalents that
  produce the same feature names. The scoring core doesn't change.

## Data
All inputs are open, mostly public-domain U.S. government data; Aqueduct is CC BY 4.0. The full
inventory is in `docs/03_data_analysis.md`.
