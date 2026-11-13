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
from ict_engine.models import model_mmxm, model_sb
from ict_engine.models.model_2022 import Params

ROOT = Path(__file__).resolve().parents[2]
BASE = Params()
NO_LONDON = tuple(w for w in BASE.windows if w != "london_kz")
VARIANTS: dict[str, Params] = {             # baseline = current defaults (TP1 cap 2R, cost gate 0.1R, bias prev_day_dol)
    "baseline": BASE,
    "first defaults (TP1 uncapped, no cost gate)": replace(BASE, tp1_cap_r=None, max_cost_r=None),
    "tp1 uncapped": replace(BASE, tp1_cap_r=None),
    "tp1 cap 1.5R": replace(BASE, tp1_cap_r=1.5),
    "tp1 cap 3R": replace(BASE, tp1_cap_r=3.0),
    "no cost gate": replace(BASE, max_cost_r=None),
    "cost <= 0.2R": replace(BASE, max_cost_r=0.2),
    "no London": replace(BASE, windows=NO_LONDON),
    "bias prev_day (old default)": replace(BASE, bias_rule="prev_day"),
    "bias draw_dol (strict)": replace(BASE, bias_rule="draw_dol"),
    "exit on 5m close through FVG": replace(BASE, invalidate_tf="5m"),
    "exit on 15m close through FVG": replace(BASE, invalidate_tf="15m"),
    "news blackout 30m before / 15m after": replace(BASE, news_blackout=(30, 15)),
    "FOMC day: only after the statement": replace(BASE, fomc_day="after_statement"),
    "skip FOMC days": replace(BASE, fomc_day="skip"),
    "partial 80% + runner at breakeven": replace(BASE, partial_frac=0.8),
    "partial 75% + runner trail (lock half)": replace(BASE, partial_frac=0.75, runner_stop="lock_half"),
    "partial 50% + runner trail (lock half)": replace(BASE, runner_stop="lock_half"),
}


MB = model_mmxm.Params()
MMXM_VARIANTS: dict[str, model_mmxm.Params] = {
    "baseline": MB,
    "re-accumulation zone 1": replace(MB, entry="reacc1"),
    "re-accumulation zone 2": replace(MB, entry="reacc2"),
    "frame 1h": replace(MB, frame_tf="1h", oc_bars=3),
    "entry 1m (old default)": replace(MB, entry_tf="1m"),
    "tp1 cap 2R": replace(MB, tp1_cap_r=2.0),
    "2 steps": replace(MB, min_steps=2),
    "no poi": replace(MB, use_poi=False),
    "no bias": replace(MB, use_bias=False),
    "deepest FVG": replace(MB, fvg_pick="deepest"),
    "no purge required": replace(MB, smr_purge=False),
    "bias prev_day (old default)": replace(MB, bias_rule="prev_day"),
    "bias draw_dol (strict)": replace(MB, bias_rule="draw_dol"),
    "exit on 5m close through FVG": replace(MB, invalidate_tf="5m"),
    "exit on 15m close through FVG": replace(MB, invalidate_tf="15m"),
    "news blackout 30m before / 15m after": replace(MB, news_blackout=(30, 15)),
    "FOMC day: only after the statement": replace(MB, fomc_day="after_statement"),
    "skip FOMC days": replace(MB, fomc_day="skip"),
    "partial 80% + runner at breakeven": replace(MB, partial_frac=0.8),
    "partial 75% + runner trail (lock half)": replace(MB, partial_frac=0.75, runner_stop="lock_half"),
    "partial 50% + runner trail (lock half)": replace(MB, runner_stop="lock_half"),
}
SB = model_sb.Params()
SB_VARIANTS: dict[str, model_sb.Params] = {
    "baseline": SB,
    "+ 15:00-16:00 window": replace(SB, late_window=True),
    "FVG must form in the hour": replace(SB, strict_fvg_in_hour=True),
    "entry at CE": replace(SB, entry_level="ce"),
    "no poi": replace(SB, use_poi=False),
    "no bias": replace(SB, use_bias=False),
    "tp1 cap 2R": replace(SB, tp1_cap_r=2.0),
    "one trade per window": replace(SB, cap_scope="window"),
    "bias prev_day (old default)": replace(SB, bias_rule="prev_day"),
    "bias draw_dol (strict)": replace(SB, bias_rule="draw_dol"),
    "exit on 5m close through FVG": replace(SB, invalidate_tf="5m"),
    "exit on 15m close through FVG": replace(SB, invalidate_tf="15m"),
    "news blackout 30m before / 15m after": replace(SB, news_blackout=(30, 15)),
    "FOMC day: only after the statement": replace(SB, fomc_day="after_statement"),
    "skip FOMC days": replace(SB, fomc_day="skip"),
    "partial 80% + runner at breakeven": replace(SB, partial_frac=0.8),
    "partial 75% + runner trail (lock half)": replace(SB, partial_frac=0.75, runner_stop="lock_half"),
    "partial 50% + runner trail (lock half)": replace(SB, runner_stop="lock_half"),
}
SETS = {"2022_model": VARIANTS, "mmxm": MMXM_VARIANTS, "silver_bullet": SB_VARIANTS}

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
    ap.add_argument("--model", default="2022_model", choices=tuple(SETS))
    a = ap.parse_args(argv)
    df = sweep(a.start, a.end, tuple(a.assets), SETS[a.model])
    cut = split_day(a.start, a.end, a.holdout)
    text = render(compare(df, cut), cut, f"{a.model} {'+'.join(a.assets)} {a.start} → {a.end}")
    out = ROOT / "reports" / f"variants{'' if a.model == '2022_model' else '-' + a.model}-{a.start}-{a.end}"
    out.parent.mkdir(exist_ok=True)
    df.to_parquet(out.with_suffix(".parquet"))
    out.with_suffix(".md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
