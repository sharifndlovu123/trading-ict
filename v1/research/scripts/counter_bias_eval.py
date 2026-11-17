"""Score the counter-bias pre-registration (research/preregistered-counter-bias-2026-11-15.md) per asset-day: ΔR = sum of
the variant's runner R − the baseline's, over days whose trade list differs; OOS from the variants tool's 70/30 cut.

    uv run python research/scripts/counter_bias_eval.py [--workers 10]   # → reports/counter-bias-*.parquet + table
"""
import argparse
import math
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import date

import pandas as pd

from ict_engine.eval.variants import MMXM_VARIANTS, VARIANTS, split_day

START, END = date(2022, 1, 3), date(2024, 6, 28)
ASSETS = ("US100", "US500", "US30", "XAUUSD", "XAGUSD")
NAMES = ("baseline", "counter: after a bias trade's TP1", "counter: after the daily draw")
SETS = {"2022_model": VARIANTS, "mmxm": MMXM_VARIANTS}


def job(args):
    model, name, asset = args
    os.environ.setdefault("ICT_COST_BASIS", "futures")
    from ict_engine.eval.backtest import load_range, run
    df = run(load_range(asset, START, END), START, END, asset, SETS[model][name], extras=False)
    t = df[df.status == "traded"].copy()
    t["rr"] = t.runner_r.fillna(t.r)
    return t[["day", "decided_at", "side", "rr", "vote"]].assign(model=model, variant=name, asset=asset)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    os.environ.setdefault("ICT_COST_BASIS", "futures")
    jobs = [(m, n, x) for m in SETS for n in NAMES for x in ASSETS]
    with ProcessPoolExecutor(a.workers) as ex:
        df = pd.concat(list(ex.map(job, jobs)), ignore_index=True)
    df.to_parquet("reports/counter-bias-trades.parquet")
    cut = split_day(START, END, 0.3)
    df["day"] = pd.to_datetime(df.day)
    lines = [f"# Counter-bias second trade — day-level ΔR (runner R, futures), OOS ≥ {cut:%Y-%m-%d}", "",
             "| model | variant | sample | changed days | mean ΔR/day ± se | z | admitted n | admitted win | admitted exp R | displaced n | displaced exp R |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in SETS:
        b = df[(df.model == m) & (df.variant == "baseline")]
        for name in NAMES[1:]:
            v = df[(df.model == m) & (df.variant == name)]
            for label, sel in (("IS", lambda x: x.day < cut), ("OOS", lambda x: x.day >= cut)):
                bb, vv = b[sel(b)], v[sel(v)]
                key = ["asset", "day"]
                kb = bb.set_index(["asset", "day", "decided_at", "side"]).index
                kv = vv.set_index(["asset", "day", "decided_at", "side"]).index
                adm, dis = vv[~kv.isin(kb)], bb[~kb.isin(kv)]
                changed = pd.concat([adm[key], dis[key]]).drop_duplicates()
                sb = bb.groupby(key).rr.sum()
                sv = vv.groupby(key).rr.sum()
                idx = pd.MultiIndex.from_frame(changed)
                d = sv.reindex(idx, fill_value=0.0) - sb.reindex(idx, fill_value=0.0)
                n = len(d)
                se = d.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
                z = d.mean() / se if n > 1 and se > 0 else float("nan")
                lines.append(f"| {m} | {name} | {label} | {n} | {d.mean():+.3f} ± {se:.3f} | {z:+.2f} | {len(adm)} | "
                             f"{adm.vote.mean() if len(adm) else float('nan'):.0%} | {adm.rr.mean() if len(adm) else float('nan'):+.3f} | "
                             f"{len(dis)} | {dis.rr.mean() if len(dis) else float('nan'):+.3f} |")
    text = "\n".join(lines)
    print(text)
    open("reports/counter-bias-results.md", "w").write(text + "\n")


if __name__ == "__main__":
    main()
