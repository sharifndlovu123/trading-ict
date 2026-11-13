"""Variant sweep with a hold-out — test review tips as rule changes, honestly.

    uv run python -m ict_engine.eval.variants 2023-02-01 2024-06-28 [--assets US100 US500] [--holdout 0.3]
    → prints the comparison, writes reports/variants-<start>-<end>.md and .parquet

Every variant runs over the whole range on every asset (in parallel). Trades
are then split by date: the first 70% of the range is **in-sample** (where tips
were found — results there are optimistic), the last 30% is **out-of-sample**
(OOS). A variant counts as an improvement only if it beats the baseline OOS.
Δ OOS is the expectancy difference with its standard error; |Δ/se| < 2 = no
evidence either way.
"""

from __future__ import annotations

import argparse
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd

from ict_engine.eval.bias import wilson
from ict_engine.models.model_2022 import Params

ROOT = Path(__file__).resolve().parents[2]
BASE = Params()
NO_LONDON = tuple(w for w in BASE.windows if w != "london_kz")
VARIANTS: dict[str, Params] = {
    "baseline": BASE,
    "tp1 cap 1.5R": replace(BASE, tp1_cap_r=1.5),
    "tp1 cap 2R": replace(BASE, tp1_cap_r=2.0),
    "tp1 cap 3R": replace(BASE, tp1_cap_r=3.0),
    "cost <= 0.1R": replace(BASE, max_cost_r=0.1),
    "cost <= 0.2R": replace(BASE, max_cost_r=0.2),
    "no London": replace(BASE, windows=NO_LONDON),
    "tp1 cap 2R + cost <= 0.1R + no London": replace(BASE, tp1_cap_r=2.0, max_cost_r=0.1, windows=NO_LONDON),
}


def _job(args) -> pd.DataFrame:
    name, params, asset, start, end = args
    from ict_engine.eval.backtest import load_range, run
    df = run(load_range(asset, start, end), start, end, asset, params, extras=False)
    return df.assign(variant_name=name)


def sweep(start: date, end: date, assets=("US100", "US500"), variants=VARIANTS, workers: int | None = None) -> pd.DataFrame:
    jobs = [(n, p, a, start, end) for n, p in variants.items() for a in assets]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return pd.concat(list(ex.map(_job, jobs)), ignore_index=True)


def split_day(start: date, end: date, holdout: float) -> pd.Timestamp:
    return pd.Timestamp(start) + (pd.Timestamp(end) - pd.Timestamp(start)) * (1 - holdout)


def _stats(t: pd.DataFrame) -> dict:
    n, k = len(t), int(t.vote.astype(bool).sum()) if len(t) else 0
    lo, hi = wilson(k, n) if n else (float("nan"), float("nan"))
    se = float(t.r.std(ddof=1)) / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "win": k / n if n else float("nan"), "win_lo": lo, "win_hi": hi,
            "exp_r": float(t.r.mean()) if n else float("nan"), "se": se, "sum_r": float(t.r.sum())}


def compare(df: pd.DataFrame, cut: pd.Timestamp, baseline: str = "baseline") -> pd.DataFrame:
    t = df[df.status == "traded"]
    rows = []
    for name, g in t.groupby("variant_name", sort=False):
        ins, oos = _stats(g[g.day < cut]), _stats(g[g.day >= cut])
        rows.append({"variant": name, **{f"is_{k}": v for k, v in ins.items()}, **{f"oos_{k}": v for k, v in oos.items()}})
    out = pd.DataFrame(rows)
    if baseline in set(out.variant):
        b = out.set_index("variant").loc[baseline]
        out["oos_delta"] = out.oos_exp_r - b.oos_exp_r
        out["oos_delta_se"] = (out.oos_se ** 2 + b.oos_se ** 2) ** 0.5
        out["oos_z"] = out.oos_delta / out.oos_delta_se
    order = list(dict.fromkeys(df.variant_name))
    return out.set_index("variant").loc[[v for v in order if v in set(out.variant)]].reset_index()


def render(cmp: pd.DataFrame, cut: pd.Timestamp, title: str) -> str:
    lines = [f"# Variant sweep {title}", f"in-sample < {cut:%Y-%m-%d} ≤ out-of-sample", "",
             "| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |",
             "|---|---|---|---|---|---|---|---|---|"]
    for _, r in cmp.iterrows():
        lines.append(f"| {r.variant} | {r.is_n} | {r.is_win:.0%} | {r.is_exp_r:+.3f} | {r.oos_n} | "
                     f"{r.oos_win:.0%} [{r.oos_win_lo:.0%}–{r.oos_win_hi:.0%}] | {r.oos_exp_r:+.3f} ± {r.oos_se:.3f} | "
                     f"{r.get('oos_delta', float('nan')):+.3f} | {r.get('oos_z', float('nan')):+.1f} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.eval.variants")
    ap.add_argument("start", type=date.fromisoformat)
    ap.add_argument("end", type=date.fromisoformat)
    ap.add_argument("--assets", nargs="+", default=["US100", "US500"])
    ap.add_argument("--holdout", type=float, default=0.3)
    a = ap.parse_args(argv)
    df = sweep(a.start, a.end, tuple(a.assets))
    cut = split_day(a.start, a.end, a.holdout)
    text = render(compare(df, cut), cut, f"{'+'.join(a.assets)} {a.start} → {a.end}")
    out = ROOT / "reports" / f"variants-{a.start}-{a.end}"
    out.parent.mkdir(exist_ok=True)
    df.to_parquet(out.with_suffix(".parquet"))
    out.with_suffix(".md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
