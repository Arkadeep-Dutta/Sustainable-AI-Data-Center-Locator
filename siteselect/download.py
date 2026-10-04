"""Fetch datasets listed in config/datasets.yaml into data/raw/. Skips existing files.

python -m siteselect.download [id ...]
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) siteselect-research"}


def _http(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120, headers=H) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.replace(dest)


def _arcgis(d: dict, dest: Path) -> None:
    import geopandas as gpd
    import pandas as pd

    url = d["url"] + "/query"
    ids = requests.get(url, params={"where": "1=1", "returnIdsOnly": "true", "f": "json"},
                       headers=H, timeout=120).json()["objectIds"]
    ids.sort()
    frames, todo = [], [ids[i:i + 250] for i in range(0, len(ids), 250)]
    while todo:
        chunk = todo.pop(0)
        params = {"objectIds": ",".join(map(str, chunk)),
                  "outFields": d.get("out_fields", "*"), "f": "geojson", "outSR": 4326,
                  "returnGeometry": "false" if d.get("no_geometry") else "true"}
        for attempt in range(4):
            try:
                r = requests.post(url, data=params, headers=H, timeout=180)
                r.raise_for_status()
                js = r.json()
                break
            except Exception:
                time.sleep(3 * (attempt + 1))
        else:
            raise RuntimeError(f"arcgis page failed at {chunk[0]}")
        feats = js.get("features", [])
        if len(feats) < len(chunk):          # server truncated (transfer limit): split and retry
            if len(chunk) == 1:
                raise RuntimeError(f"feature {chunk[0]} not returned")
            h = len(chunk) // 2
            todo[:0] = [chunk[:h], chunk[h:]]
            continue
        if d.get("no_geometry"):
            frames.append(pd.DataFrame([f["properties"] for f in feats]))
        else:
            frames.append(gpd.GeoDataFrame.from_features(feats, crs=4326))
    out = pd.concat(frames, ignore_index=True)
    if len(out) != len(ids):
        raise RuntimeError(f"expected {len(ids)} features, got {len(out)}")
    if d.get("no_geometry"):
        out.to_parquet(dest)
    else:
        gpd.GeoDataFrame(out, crs=4326).to_parquet(dest)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main(ids: list[str]) -> None:
    reg = yaml.safe_load(open(ROOT / "config" / "datasets.yaml"))["datasets"]
    RAW.mkdir(parents=True, exist_ok=True)
    log = ROOT / "data" / "raw" / "_download_log.tsv"
    for k in ids or list(reg):
        d = reg[k]
        dest = RAW / d["file"]
        if dest.exists():
            continue
        t = time.time()
        try:
            if d["kind"] == "arcgis":
                _arcgis(d, dest)
            else:
                _http(d["url"], dest)
            msg = f"{k}\tOK\t{dest.stat().st_size/1e6:.1f}MB\t{time.time()-t:.0f}s\t{sha256(dest)}"
        except Exception as e:  # noqa: BLE001
            msg = f"{k}\tFAIL\t{type(e).__name__}: {str(e)[:150]}"
        with open(log, "a") as f:
            f.write(msg + "\n")
        print(msg[:120], flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
