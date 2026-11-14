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
from ict_engine.models import model_cameron, model_mmxm, model_pd_return, model_sb
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
    "entry at market (next open)": replace(BASE, entry_mode="market"),
    # targets and holding (research/preregistered-liquidity-targets-2026-11-14.md + amendment 1; score with --metric runner_r)
    "targets: runner to strongest pool": replace(BASE, target_mode="pool"),
    "targets: FVGs ahead as TP1 candidates": replace(BASE, target_mode="fvg_tp1"),
    "targets: both": replace(BASE, target_mode="both"),
    "hold: runner to the HTF draw": replace(BASE, target_mode="hold"),
    # entry quality (research/preregistered-entry-quality-2026-11-14.md)
    "entry: sweep then displacement": replace(BASE, entry_gate="sweep_disp"),
    "entry: no chop in the zone": replace(BASE, entry_gate="no_chop"),
    "entry: both": replace(BASE, entry_gate="both"),
    # higher timeframes + trailed runner (research/preregistered-timeframes-trail-2026-11-14.md; score with --metric runner_r)
    "tf: entry 5m": replace(BASE, entry_tf="5m", sweep_lookback_min=180, tp1_swing_tfs=("15m",)),
    "tf: entry 15m": replace(BASE, entry_tf="15m", sweep_lookback_min=360, tp1_swing_tfs=("1h",)),
    "runner: trailed on 5m": replace(BASE, runner_stop="trail_5m"),
    # nested FVG / location / range target (research/preregistered-nested-fvg-2026-11-14.md; score with --metric runner_r)
    "loc: entry FVG inside a 4h FVG": replace(BASE, entry_gate="nested_4h"),
    "loc: not inside a daily FVG": replace(BASE, entry_gate="outside_daily_fvg"),
    "targets: 50% of the 4h range, runner to the HTF draw": replace(BASE, target_mode="eq_hold"),
    # range in play (research/preregistered-range-in-play-2026-11-14.md; score with --metric runner_r)
    "range: entry in the cheap half": replace(BASE, range_entry="cheap_half"),
    "range: limit at the 50%": replace(BASE, range_entry="eq_limit"),
    "leg: limit at OTE 70.5%": replace(BASE, range_entry="leg_ote"),
    # counter-bias second trade (research/preregistered-counter-bias-2026-11-15.md; scored per day by counter_bias_eval)
    "counter: after a bias trade's TP1": replace(BASE, counter_after="tp1"),
    "counter: after the daily draw": replace(BASE, counter_after="draw"),
    "trigger: hold within 2 bp": replace(BASE, liquidity_hold_bp=2.0),
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
    # entry quality (research/preregistered-entry-quality-2026-11-14.md)
    "entry: sweep then displacement": replace(MB, entry_gate="sweep_disp"),
    "entry: no chop in the zone": replace(MB, entry_gate="no_chop"),
    "entry: both": replace(MB, entry_gate="both"),
    # higher timeframes + trailed runner (research/preregistered-timeframes-trail-2026-11-14.md; score with --metric runner_r)
    "tf: frame 1h > entry 15m": replace(MB, frame_tf="1h", entry_tf="15m", curve_max_h=48.0, low_lookback_min=480),
    "tf: frame 4h > entry 1h": replace(MB, frame_tf="4h", entry_tf="1h", curve_max_h=192.0, low_lookback_min=1440),
    "runner: trailed on 5m": replace(MB, runner_stop="trail_5m"),
    # nested FVG / location / range target (research/preregistered-nested-fvg-2026-11-14.md; score with --metric runner_r)
    "loc: entry FVG inside a 4h FVG": replace(MB, entry_gate="nested_4h"),
    "loc: not inside a daily FVG": replace(MB, entry_gate="outside_daily_fvg"),
    "targets: 50% of the 4h range, runner to the HTF draw": replace(MB, target_mode="eq_hold"),
    # range in play (research/preregistered-range-in-play-2026-11-14.md; score with --metric runner_r)
    "range: entry in the cheap half": replace(MB, range_entry="cheap_half"),
    "range: limit at the 50%": replace(MB, range_entry="eq_limit"),
    "leg: limit at OTE 70.5%": replace(MB, range_entry="leg_ote"),
    # counter-bias second trade (research/preregistered-counter-bias-2026-11-15.md; scored per day by counter_bias_eval)
    "counter: after a bias trade's TP1": replace(MB, counter_after="tp1"),
    "counter: after the daily draw": replace(MB, counter_after="draw"),
    "purge: hold within 2 bp": replace(MB, liquidity_hold_bp=2.0),
    "entry: retest of the broken OC": replace(MB, entry="oc_retest"),
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
    # entry quality (research/preregistered-entry-quality-2026-11-14.md)
    "entry: sweep then displacement": replace(SB, entry_gate="sweep_disp"),
    "entry: no chop in the zone": replace(SB, entry_gate="no_chop"),
    "entry: both": replace(SB, entry_gate="both"),
}
CB = model_cameron.Params()
CAMERON_VARIANTS: dict[str, model_cameron.Params] = {
    "baseline": CB,
    "not running required": replace(CB, require_running=False),
    "with bias prev_day_dol": replace(CB, use_bias=True),
    "trigger 1m > entry 1m": replace(CB, trigger_tf="1m"),
    "entry at CE": replace(CB, entry_level="ce"),
    "tp1 cap 2R": replace(CB, tp1_cap_r=2.0),
    "one trade per window": replace(CB, cap_scope="window"),
    "partial 80% + runner at breakeven": replace(CB, partial_frac=0.8),
    "partial 75% + runner trail (lock half)": replace(CB, partial_frac=0.75, runner_stop="lock_half"),
    # entry quality (research/preregistered-entry-quality-2026-11-14.md)
    "entry: sweep then displacement": replace(CB, entry_gate="sweep_disp"),
    "entry: no chop in the zone": replace(CB, entry_gate="no_chop"),
    "entry: both": replace(CB, entry_gate="both"),
}
PR = model_pd_return.Params()
# Windows are ICT's documented ones only (clock.py). ICT's 2023-11-28 trade at 11:11 lies just after macro_1050;
# no window is invented from that single case.
PD_RETURN_VARIANTS: dict[str, model_pd_return.Params] = {
    "baseline": PR,
    "no bias": replace(PR, use_bias=False),
    "+ macros (to 11:10)": replace(PR, windows=PR.windows + ("macro_0950", "macro_1050")),
    "macros only": replace(PR, windows=("macro_0950", "macro_1050")),
    "stop beyond array": replace(PR, stop_mode="array"),
    "entry at CE": replace(PR, entry_level="ce"),
    "arrays 1h+4h only": replace(PR, htf_tfs=("1h", "4h")),
    "lookback 2 days": replace(PR, lookback_days=2),
    "tp1 cap 2R": replace(PR, tp1_cap_r=2.0),
    "no cost gate": replace(PR, max_cost_r=None),
    # models.md §6 array variants (ICT Bible pp.16-26)
    "array: order block": replace(PR, arrays=("ob",)),
    "array: breaker": replace(PR, arrays=("breaker",)),
    "array: mitigation block": replace(PR, arrays=("mitigation",)),
    "array: FVG + OB + breaker + MB": replace(PR, arrays=("fvg", "ob", "breaker", "mitigation")),
    # higher-timeframe order blocks (research/preregistered-htf-ob-2026-11-14.md; ICT rulings §11)
    "HTF OB 4h+1d (open, body)": replace(PR, htf_tfs=("4h", "1d"), arrays=("ob",), ob_confirm="open", ob_measure="body"),
    "HTF OB 4h+1d (extreme, body)": replace(PR, htf_tfs=("4h", "1d"), arrays=("ob",), ob_measure="body"),
    "HTF OB 4h+1d (open, body, lookback 10)": replace(PR, htf_tfs=("4h", "1d"), arrays=("ob",), ob_confirm="open",
                                                      ob_measure="body", lookback_days=10),
    "HTF FVG + OB 15m-1d (open, body)": replace(PR, htf_tfs=("15m", "1h", "4h", "1d"), arrays=("fvg", "ob"),
                                                ob_confirm="open", ob_measure="body"),
    "HTF daily FVGs added": replace(PR, htf_tfs=("15m", "1h", "4h", "1d")),
    # failed HTF FVGs (IFVGs) inverted on their own timeframe's close (research/preregistered-htf-ifvg-2026-11-14.md)
    "HTF IFVG 4h+1d (tf close)": replace(PR, htf_tfs=("4h", "1d"), arrays=("ifvg",), lookback_days=10),
    "HTF IFVG 4h+1d (1m close)": replace(PR, htf_tfs=("4h", "1d"), arrays=("ifvg",), ifvg_close="1m", lookback_days=10),
    "HTF IFVG + OB 4h+1d (tf close; OB open, body)": replace(PR, htf_tfs=("4h", "1d"), arrays=("ifvg", "ob"),
                                                             ob_confirm="open", ob_measure="body", lookback_days=10),
    "HTF FVG + IFVG 15m-1d (tf close)": replace(PR, htf_tfs=("15m", "1h", "4h", "1d"), arrays=("fvg", "ifvg"),
                                                lookback_days=10),
    "HTF IFVG 4h+1d (tf close, overrides bias)": replace(PR, htf_tfs=("4h", "1d"), arrays=("ifvg",), ifvg_bias="override",
                                                         lookback_days=10),
    "HTF IFVG + OB 1d+1w+1M (tf close; OB open, body)": replace(PR, htf_tfs=("1d", "1w", "1M"), arrays=("ifvg", "ob"),
                                                                ob_confirm="open", ob_measure="body", lookback_days=60),
    # targets and holding (research/preregistered-liquidity-targets-2026-11-14.md + amendment 1; score with --metric runner_r)
    "targets: runner to strongest pool": replace(PR, target_mode="pool"),
    "targets: FVGs ahead as TP1 candidates": replace(PR, target_mode="fvg_tp1"),
    "targets: both": replace(PR, target_mode="both"),
    "hold: runner to the HTF draw": replace(PR, target_mode="hold"),
    # entry quality (research/preregistered-entry-quality-2026-11-14.md)
    "entry: sweep then displacement": replace(PR, entry_gate="sweep_disp"),
    "entry: no chop in the zone": replace(PR, entry_gate="no_chop"),
    "entry: both": replace(PR, entry_gate="both"),
}
SETS = {"2022_model": VARIANTS, "mmxm": MMXM_VARIANTS, "silver_bullet": SB_VARIANTS, "cameron": CAMERON_VARIANTS,
        "pd_return": PD_RETURN_VARIANTS}

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
    ap.add_argument("--workers", type=int, default=8, help="process cap (CPU heat: 16 cores hit 96 °C)")
    ap.add_argument("--only", nargs="+", help="run only these variants (names start with; baseline always runs)")
    ap.add_argument("--cost", choices=("cfd", "futures"), default=None, help="cost basis (sets ICT_COST_BASIS)")
    ap.add_argument("--metric", choices=("r", "runner_r"), default="r",
                    help="r = all out at TP1 (the vote measure); runner_r = partial at TP1 + the runner")
    a = ap.parse_args(argv)
    if a.cost:
        import os
        os.environ["ICT_COST_BASIS"] = a.cost
    vs = SETS[a.model]
    if a.only:
        vs = {k: v for k, v in vs.items() if k == "baseline" or any(k.startswith(o) for o in a.only)}
    df = sweep(a.start, a.end, tuple(a.assets), vs, workers=a.workers)
    cut = split_day(a.start, a.end, a.holdout)
    scored = df.assign(r=df.runner_r.fillna(df.r)) if a.metric == "runner_r" else df
    text = render(compare(scored, cut), cut, f"{a.model} {'+'.join(a.assets)} {a.start} → {a.end}"
                  + (" (runner R)" if a.metric == "runner_r" else ""))
    out = ROOT / "reports" / (f"variants{'' if a.model == '2022_model' else '-' + a.model}-{a.start}-{a.end}"
                              f"{'-futures' if a.cost == 'futures' else ''}{'-only' if a.only else ''}{'-runner' if a.metric == 'runner_r' else ''}")
    out.parent.mkdir(exist_ok=True)
    df.to_parquet(out.with_suffix(".parquet"))
    out.with_suffix(".md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
