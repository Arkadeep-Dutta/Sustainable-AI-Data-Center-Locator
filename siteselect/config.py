"""Config loading + project paths."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config"
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
DIAG = OUTPUTS / "diagnostics"
PILLARS = ["EC", "WA", "GI", "CE", "CR", "LM", "HR"]
CRS_GEO = 4326
CRS_M = 5070


@lru_cache
def load(name: str) -> dict:
    with open(CFG / f"{name}.yaml", encoding="utf-8-sig") as f:
        return yaml.safe_load(f)


def features() -> dict:
    return load("features")["features"]


def pillar_weights() -> dict[str, float]:
    w = load("weights")["pillars"]
    s = sum(w.values())
    return {p: w[p] / s for p in PILLARS}


for _d in (INTERIM, PROCESSED, DIAG, OUTPUTS / "maps"):
    _d.mkdir(parents=True, exist_ok=True)
