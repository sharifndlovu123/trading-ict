"""The flip after a failed trade (research/preregistered-ifvg-flip-2026-11-14.md; review log #2, ICT rulings §10).

Sharif: "there's nothing wrong with being incorrect … a fail turned into a win". For each trade a model takes that
is **stopped out**:

1. failure  — the trade's entry FVG has a candle of its own timeframe close beyond its far edge; the candle must
              start at or before the stop-out bar. It is now an IFVG, known at that candle's close.
2. retest   — a limit at the IFVG's near edge, live from that close for 90 minutes (never past 16:00).
3. flip     — the opposite side. Stop (amendment 1, both reported): ``"far_edge"`` = the IFVG's far edge (as first
              written) | ``"failed_extreme"`` = beyond the failed trade's extreme from its fill to the inversion
              (Sharif: the flip short sits under the high the failed long made). TP1 = the
              nearest untaken liquidity ≥ 1R (the models' ``_targets``); runner as the model's partials. No bias
              gate. The model's own cost gate applies (``max_cost_r``). One flip per failed trade, no flip of a flip.

``python -m ict_engine.eval.flip 2022-01-03 2024-06-28 --cost cfd --workers 8`` runs all five models.
"""

from __future__ import annotations

import argparse
import math
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import Event, swings
from ict_engine.data.instruments import cost_at
from ict_engine.models.base import TradePlan
from ict_engine.models.model_2022 import _targets

NY = "America/New_York"
RETEST_MIN = 90
SESSION_END = time(16)
MODELS = ("2022_model", "mmxm", "silver_bullet", "cameron", "pd_return")


def inversion_close(fvg: Event, day_1m: pd.DataFrame, stop_at: pd.Timestamp) -> pd.Timestamp | None:
    """close_ts of the first ``fvg.tf`` candle after the FVG formed that closes beyond its far edge, among
    candles that start at or before ``stop_at``."""
    bars = resample(day_1m, fvg.tf)
    bars = bars[(bars.close_ts > fvg.ts) & (bars.index <= stop_at)]
    if bars.empty:
        return None
    beyond = bars.close < fvg.bottom if fvg.direction == "bull" else bars.close > fvg.top
    return pd.Timestamp(bars.close_ts[beyond].iloc[0]) if beyond.any() else None


STOP_RULES = ("far_edge", "failed_extreme")


def flip_plan(setup, day_1m: pd.DataFrame, ctx, params, stop_rule: str = "far_edge") -> TradePlan | None:
    """The opposite trade for a stopped-out ``setup``, or None when no flip arises (no own-TF close through the
    entry FVG, no liquidity ≥ 1R beyond, or the cost gate)."""
    res, plan, fvg = setup.result, setup.plan, setup.evidence.get("fvg")
    if plan is None or res is None or res.exit_reason != "stop" or fvg is None or fvg.kind != "fvg":
        return None
    inv = inversion_close(fvg, day_1m[day_1m.index <= res.exit_at], res.exit_at)
    if inv is None:
        return None
    if stop_rule not in STOP_RULES:
        raise ValueError(f"stop_rule must be one of {STOP_RULES}, got {stop_rule!r}")
    short = plan.side == "long"                      # the flip is the other side
    entry, stop = (fvg.bottom, fvg.top) if short else (fvg.top, fvg.bottom)
    if stop_rule == "failed_extreme":
        leg = day_1m[(day_1m.index >= (res.filled_at or plan.placed_at)) & (day_1m.index <= inv)]
        if not leg.empty:
            ext = float(leg.high.max()) if short else float(leg.low.min())
            stop = max(stop, ext) if short else min(stop, ext)
    risk = abs(stop - entry)
    if risk <= 0:
        return None
    seen = day_1m[day_1m.index <= inv]
    swing_pts = swings(resample(seen, "5m"), "5m") + swings(resample(seen, "15m"), "15m")
    tp1, tp1_name, final, final_name = _targets(entry, not short, ctx, day_1m, inv, swing_pts, min_dist=risk)
    if tp1 is None:
        return None
    max_cost_r = getattr(params, "max_cost_r", None)
    if max_cost_r is not None and cost_at(setup.asset, entry, inv) / risk > max_cost_r:
        return None
    close = pd.Timestamp(datetime.combine(setup.day, SESSION_END), tz=NY)
    return TradePlan("short" if short else "long", inv, min(inv + timedelta(minutes=RETEST_MIN), close),
                     entry, stop, tp1, final, f"flip: {tp1_name}", final_name,
                     partial_frac=getattr(params, "partial_frac", 0.5), runner_stop=getattr(params, "runner_stop", "entry"))


def run_asset(model: str, asset: str, start: date, end: date) -> pd.DataFrame:
    """One row per model trade (kind="model") and per flip trade (kind="flip"), with R, vote and day."""
    from ict_engine.concepts.context import build_context
    from ict_engine.eval.backtest import load_range
    from ict_engine.models.registry import modules
    from ict_engine.sim.run import run_day
    from ict_engine.sim.simulate import simulate

    params = modules()[model].Params()
    bars = load_range(asset, start, end)
    rows, d = [], start
    while d <= end:
        if d.weekday() < 5:
            try:
                ctx = build_context(bars, d)
            except ValueError:
                ctx = None
            if ctx is not None and "pdh" in ctx.levels:
                close = pd.Timestamp(datetime.combine(d, SESSION_END), tz=NY)
                day_1m = bars[(bars.index >= pd.Timestamp(datetime.combine(d, time(0)), tz=NY)) &
                              (bars.index < pd.Timestamp(datetime.combine(d, time(16, 30)), tz=NY))]
                for s in run_day(bars, d, asset, params, ctx=ctx):
                    if s.plan is None or s.result is None or s.result.filled_at is None:
                        continue
                    rows.append({"model": model, "asset": asset, "day": pd.Timestamp(d), "kind": "model",
                                 "side": s.side, "r": s.result.r, "vote": bool(s.result.vote),
                                 "exit": s.result.exit_reason})
                    for rule in STOP_RULES:
                        fp = flip_plan(s, day_1m, ctx, params, rule)
                        if fp is None:
                            continue
                        r = simulate(fp, bars, close, cost=cost_at(asset, fp.entry, fp.placed_at))
                        rows.append({"model": model, "asset": asset, "day": pd.Timestamp(d), "kind": f"flip:{rule}",
                                     "side": fp.side, "risk": fp.risk, "r": r.r if r.filled_at is not None else None,
                                     "vote": bool(r.vote) if r.filled_at is not None else None,
                                     "exit": r.exit_reason})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def _job(a):
    return run_asset(*a)


def summarize(df: pd.DataFrame, cut: pd.Timestamp) -> pd.DataFrame:
    """Per model × stop rule: flip trades OOS (exp R, se, z vs 0); model alone vs model + flips in R per trading day."""
    out = []
    for model, g in df.groupby("model", sort=False):
        oos = g[g.day >= cut]
        days = max(oos.day.nunique(), 1)
        mod = oos[oos.kind == "model"]
        model_r = float(mod.r.sum())
        for kind in sorted(k for k in g.kind.unique() if k.startswith("flip")):
            flips = oos[oos.kind == kind]
            filled = flips[flips.r.notna()]
            n = len(filled)
            exp = float(filled.r.mean()) if n else float("nan")
            se = float(filled.r.std(ddof=1)) / math.sqrt(n) if n > 1 else float("nan")
            out.append({"model": model, "rule": kind.split(":", 1)[-1], "oos_model_trades": len(mod),
                        "oos_stopped": int((mod.exit == "stop").sum()), "flips_armed": len(flips), "flips_filled": n,
                        "flip_win": float(filled.vote.astype(bool).mean()) if n else float("nan"),
                        "flip_exp_r": exp, "flip_se": se,
                        "flip_z": exp / se if n > 1 and se > 0 else float("nan"),
                        "model_r_per_day": model_r / days,
                        "with_flips_r_per_day": (model_r + float(filled.r.sum())) / days})
    return pd.DataFrame(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.eval.flip")
    ap.add_argument("start", type=date.fromisoformat)
    ap.add_argument("end", type=date.fromisoformat)
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--assets", nargs="+", default=["US100", "US500", "US30", "XAUUSD", "XAGUSD"])
    ap.add_argument("--cost", choices=("cfd", "futures"), default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--holdout", type=float, default=0.3)
    ap.add_argument("--out", default=None, help="parquet of every model/flip trade")
    a = ap.parse_args(argv)
    if a.cost:
        import os
        os.environ["ICT_COST_BASIS"] = a.cost
    jobs = [(m, s, a.start, a.end) for m in a.models for s in a.assets]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        df = pd.concat(list(ex.map(_job, jobs)), ignore_index=True)
    if a.out:
        df.to_parquet(a.out)
    cut = pd.Timestamp(a.start) + (pd.Timestamp(a.end) - pd.Timestamp(a.start)) * (1 - a.holdout)
    s = summarize(df, cut)
    print(f"# Flip after a failed trade ({a.cost or 'default'} costs), out-of-sample ≥ {cut:%Y-%m-%d}\n")
    print("| model | flip stop | OOS trades | stopped | flips armed | filled | flip win | flip exp R ± se | z | R/day model | R/day + flips |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in s.iterrows():
        print(f"| {r.model} | {r.rule} | {r.oos_model_trades} | {r.oos_stopped} | {r.flips_armed} | {r.flips_filled} | "
              f"{r.flip_win:.0%} | {r.flip_exp_r:+.3f} ± {r.flip_se:.3f} | {r.flip_z:+.1f} | "
              f"{r.model_r_per_day:+.4f} | {r.with_flips_r_per_day:+.4f} |")


if __name__ == "__main__":
    main()
