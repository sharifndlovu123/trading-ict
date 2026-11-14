"""Day-level ΔR scorer for rules that add (or displace) trades: per asset-day, ΔR = sum of the variant's runner R − the
baseline's, over days whose trade list differs; OOS from the variants tool's 70/30 cut. Used by the counter-bias and
liquidity-hold pre-registrations.

    uv run python research/scripts/day_delta_eval.py --tag hold \
        --cell "2022_model:trigger: hold within 2 bp" --cell "mmxm:purge: hold within 2 bp" [--workers 10]
    # → reports/<tag>-trades.parquet + reports/<tag>-results.md
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
SETS = {"2022_model": VARIANTS, "mmxm": MMXM_VARIANTS}


def job(args):
    model, name, asset = args
    os.environ.setdefault("ICT_COST_BASIS", "futures")
    from ict_engine.eval.backtest import load_range, run
    df = run(load_range(asset, START, END), START, END, asset, SETS[model][name], extras=False)
    t = df[df.status == "traded"].copy()
    t["rr"] = t.runner_r.fillna(t.r)
    return t[["day", "decided_at", "side", "rr", "vote"]].assign(model=model, variant=name, asset=asset)


def score(df: pd.DataFrame, cells: list[tuple[str, str]], title: str) -> str:
    cut = split_day(START, END, 0.3)
    df = df.assign(day=pd.to_datetime(df.day))
    lines = [f"# {title} — day-level ΔR (runner R, futures), OOS ≥ {cut:%Y-%m-%d}", "",
             "| model | variant | sample | changed days | mean ΔR/day ± se | z | admitted n | admitted win | admitted exp R | displaced n | displaced exp R |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, name in cells:
        b = df[(df.model == m) & (df.variant == "baseline")]
        v = df[(df.model == m) & (df.variant == name)]
        for label, sel in (("IS", lambda x: x.day < cut), ("OOS", lambda x: x.day >= cut)):
            bb, vv = b[sel(b)], v[sel(v)]
            key = ["asset", "day"]
            kb = bb.set_index(["asset", "day", "decided_at", "side"]).index
            kv = vv.set_index(["asset", "day", "decided_at", "side"]).index
            adm, dis = vv[~kv.isin(kb)], bb[~kb.isin(kv)]
            changed = pd.concat([adm[key], dis[key]]).drop_duplicates()
            idx = pd.MultiIndex.from_frame(changed)
            d = vv.groupby(key).rr.sum().reindex(idx, fill_value=0.0) - bb.groupby(key).rr.sum().reindex(idx, fill_value=0.0)
            n = len(d)
            se = d.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
            z = d.mean() / se if n > 1 and se > 0 else float("nan")
            nan = float("nan")
            lines.append(f"| {m} | {name} | {label} | {n} | {d.mean() if n else nan:+.3f} ± {se:.3f} | {z:+.2f} | {len(adm)} | "
                         f"{adm.vote.mean() if len(adm) else nan:.0%} | {adm.rr.mean() if len(adm) else nan:+.3f} | "
                         f"{len(dis)} | {dis.rr.mean() if len(dis) else nan:+.3f} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--cell", action="append", required=True, help="model:variant name")
    ap.add_argument("--title", default=None)
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    os.environ.setdefault("ICT_COST_BASIS", "futures")
    cells = [tuple(c.split(":", 1)) for c in a.cell]
    for m, n in cells:
        assert n in SETS[m], f"unknown variant {n!r} for {m}"
    runs = sorted({(m, "baseline") for m, _ in cells} | set(cells))
    jobs = [(m, n, x) for m, n in runs for x in ASSETS]
    with ProcessPoolExecutor(a.workers) as ex:
        df = pd.concat(list(ex.map(job, jobs)), ignore_index=True)
    df.to_parquet(f"reports/{a.tag}-trades.parquet")
    text = score(df, cells, a.title or a.tag)
    print(text)
    open(f"reports/{a.tag}-results.md", "w").write(text + "\n")


if __name__ == "__main__":
    main()
