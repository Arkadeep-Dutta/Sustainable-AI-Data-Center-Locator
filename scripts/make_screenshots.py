"""Capture demo screenshots of the running Streamlit app (dev tool; needs `pip install playwright` and
Microsoft Edge or Chrome installed).

streamlit run app/streamlit_app.py --server.port 8620 --server.headless true --theme.base light
python scripts/make_screenshots.py [http://localhost:8620]
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8620"
OUT = Path(__file__).resolve().parents[1] / "screenshots"
OUT.mkdir(exist_ok=True)
ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def wait_text(page, text, timeout=120_000):
    page.get_by_text(text, exact=False).first.wait_for(timeout=timeout)


def shot_at(page, heading, name, settle=2.5):
    page.get_by_text(heading, exact=False).first.evaluate("e => e.scrollIntoView({block: 'start'})")
    time.sleep(settle)
    page.screenshot(path=str(OUT / name))


with sync_playwright() as p:
    try:
        b = p.chromium.launch(channel="msedge", headless=True, args=ARGS)
    except Exception:
        b = p.chromium.launch(channel="chrome", headless=True, args=ARGS)
    page = b.new_page(viewport={"width": 1600, "height": 950}, device_scale_factor=1)
    page.goto(URL)
    wait_text(page, "Recommendation:")
    wait_text(page, "Top 5 finalists")
    wait_text(page, "OpenStreetMap")
    time.sleep(6)                                   # let deck.gl and charts render
    page.screenshot(path=str(OUT / "01_final_recommendation.png"))
    shot_at(page, "Map — national score", "02_map_and_top5.png", settle=4)
    shot_at(page, "Robustness — 5,000", "03_robustness.png")
    shot_at(page, "Sustainability comparison", "04_sustainability.png")

    page.goto(URL + "/?view=explore")
    wait_text(page, "Score map", timeout=180_000)
    wait_text(page, "OpenStreetMap", timeout=180_000)   # deck.gl basemap attribution = map rendered
    time.sleep(8)
    page.screenshot(path=str(OUT / "05_explore_default.png"))
    s = page.get_by_role("slider").nth(2)           # Grid & Infrastructure weight
    s.focus()
    for _ in range(13):                             # 22 -> 35
        page.keyboard.press("ArrowRight")
    time.sleep(1)
    wait_text(page, "Score map", timeout=180_000)
    time.sleep(10)
    page.screenshot(path=str(OUT / "06_explore_grid_weight_35.png"))
    b.close()
print("saved:", sorted(x.name for x in OUT.glob("*.png")))
