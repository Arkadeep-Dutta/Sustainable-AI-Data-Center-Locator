"""Assemble the feature store data/processed/features_res<N>.parquet from cached adapter outputs.

python -m siteselect.features --res 6 [--only egrid,acs] [--force egrid]
Each adapter output is cached at data/interim/<name>_res<N>.parquet; weight changes never touch it.
"""
from __future__ import annotations

import argparse
import importlib
import json
import time

import numpy as np
import pandas as pd

from . import grid
from .config import DIAG, INTERIM, PROCESSED

ADAPTERS = ["egrid", "aqueduct", "noaa", "acs", "nri", "transmission", "land"]


def run_adapter(name: str, cells: pd.DataFrame, res: int, force: bool = False, tag: str = "") -> pd.DataFrame:
    p = INTERIM / f"{name}_res{res}{tag}.parquet"
    if p.exists() and not force:
        return pd.read_parquet(p)
    t = time.time()
    mod = importlib.import_module(f"siteselect.adapters.{name}")
    out = mod.build(cells) if name != "land" else mod.build(cells, res)
    out.index = cells["h3"].to_numpy()
    out.to_parquet(p)
    timing = DIAG / "adapter_timing.json"
    d = json.loads(timing.read_text()) if timing.exists() else {}
    d[f"{name}_res{res}{tag}"] = {"seconds": round(time.time() - t, 1), "cells": len(cells)}
    timing.write_text(json.dumps(d, indent=1))
    return out


def derived(df: pd.DataFrame) -> pd.DataFrame:
    if {"hdd65", "pop_50km"} <= set(df.columns):
        df["hr_heat_demand"] = df["hdd65"] * df["pop_50km"]
        df["cov_hr_heat_demand"] = df["hr_heat_demand"].notna()
    return df


def assemble(res: int, only: list[str] | None = None, force: list[str] | None = None,
             cells: pd.DataFrame | None = None, tag: str = "") -> pd.DataFrame:
    cells = cells if cells is not None else grid.cells(res)
    parts = [cells.set_index("h3")]
    for a in only or ADAPTERS:
        try:
            parts.append(run_adapter(a, cells, res, force=a in (force or []), tag=tag))
        except FileNotFoundError as e:
            print(f"[skip] {a}: missing raw file ({e.filename})")
    df = derived(pd.concat(parts, axis=1))
    df.index.name = "h3"
    df.to_parquet(PROCESSED / f"features_res{res}{tag}.parquet")
    miss = df.filter(regex="^(ec|wa|gi|ce|cr|lm|hr)_").isna().mean().round(4)
    miss.to_csv(DIAG / f"missingness_res{res}{tag}.csv", header=["frac_missing"])
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", default="")
    a = ap.parse_args()
    df = assemble(a.res, [x for x in a.only.split(",") if x] or None, [x for x in a.force.split(",") if x])
    print(f"features_res{a.res}: {df.shape[0]} cells x {df.shape[1]} cols")
