"""Score the re-entry pre-registration (research/preregistered-reentry-2026-11-16.md): the ADDED trades of each variant
(tagged `reentry`) on their own, in-sample and OOS, runner R. Reads reports/reentry-<model>.parquet
(research/scripts/run_reentry_sweeps.sh).

    uv run python research/scripts/reentry_eval.py
"""
import math
from datetime import date

import pandas as pd

from ict_engine.eval.variants import split_day

START, END = date(2022, 1, 3), date(2024, 6, 28)
CUT = split_day(START, END, 0.3)


def stats(t):
    n = len(t)
    if not n:
        return "n 0"
    m, se = t.r.mean(), (t.r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan"))
    return f"n {n:4d} · win {t.vote.astype(bool).mean():.0%} · mean {m:+.3f} R · se {se:.3f} · z {m / se if se else float('nan'):+.2f} · sum {t.r.sum():+.1f} R"


import os
for model in ("2022_model", "mmxm"):
    if not os.path.exists(f"reports/reentry-{model}.parquet"):
        print(f"=== {model}: no results yet"); continue
    df = pd.read_parquet(f"reports/reentry-{model}.parquet")
    df = df[df.status == "traded"].assign(r=lambda d: d.runner_r.fillna(d.r))
    print(f"=== {model}  (OOS from {CUT.date()})")
    for v in ("re-entry: after a stop, same side", "control: any second trade"):
        add = df[(df.variant_name == v) & df.reentry]
        print(f"  {v}")
        print(f"    added IS : {stats(add[add.day < CUT])}")
        print(f"    added OOS: {stats(add[add.day >= CUT])}")
        for a, g in add[add.day >= CUT].groupby("asset"):
            print(f"      {a:7} {stats(g)}")
