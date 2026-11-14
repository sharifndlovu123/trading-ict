"""Liquidity reach (descriptive, in-sample only — selects nothing): for every filled 2022 model / MMxM trade in
2022-01-03 → 2023-09-28 (futures backtests), list every untaken liquidity level ahead of the entry as known at the
decision, and record whether price reached it (a) before the trade's stop, (b) by the session close (16:55) ignoring the
stop, (c) by the next day's close. Shows which liquidity actually gets taken, by type and distance in R — the raw
material for a TP ladder (Sharif 2026-11-14: "we need a better finding of liquidity and more TP areas").

    uv run python research/scripts/liquidity_reach.py [--workers 6]   # → reports/liquidity-reach.parquet + summary

Level types (lookback 20 days, untaken from formation to the decision):
    pdh/pdl, pwh/pwl, asia_high/low, london_high/low (02:00–05:00, if finished)
    swing_{15m,1h,4h,1d}    strength-1 swing highs (long) / lows (short)
    eq_{1h,4h}              equal highs/lows (2 bp)
    fvg_{1h,4h,1d}_{near,ce,far}   unfilled opposite-polarity FVG ahead (a long aims at a bearish FVG above)
Same-bar stop and level touch → counted as stop first (conservative).
"""
import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import build_context
from ict_engine.concepts.events import equal_levels, fvgs, swing_levels, swings
from ict_engine.data import dukascopy

NY = "America/New_York"
START, CUT = date(2022, 1, 3), date(2023, 9, 29)
LOOKBACK = timedelta(days=20)
TOL_BP = 2.0
MODELS = {"2022_model": "reports/backtest-{a}-2022-01-03-2024-06-28-futures.parquet",
          "mmxm": "reports/backtest-mmxm-{a}-2022-01-03-2024-06-28-futures.parquet"}
ASSETS = ("US100", "US500", "US30", "XAUUSD", "XAGUSD")
BUCKETS = [0, 1, 2, 3, 5, 10, np.inf]


def levels_ahead(hist: pd.DataFrame, ctx, decided: pd.Timestamp, long: bool, entry: float) -> list[tuple[str, float]]:
    """(type, price) of every untaken level ahead of entry on the trade's side, from bars before ``decided`` only."""
    ahead = (lambda p: p > entry) if long else (lambda p: p < entry)
    out = []

    def untaken(price, since):
        seg = hist[hist.index > since]
        return seg.empty or (price > seg.high.max() if long else price < seg.low.min())

    day0 = pd.Timestamp(datetime.combine(decided.date(), time(0)), tz=NY)
    for n in (("pdh", "pwh", "asia_high") if long else ("pdl", "pwl", "asia_low")):
        if n in ctx.levels and ahead(ctx.levels[n]) and untaken(ctx.levels[n], day0 - timedelta(hours=6)):
            out.append((n.replace("asia_high", "asia").replace("asia_low", "asia"), ctx.levels[n]))
    lon = hist[(hist.index >= day0 + timedelta(hours=2)) & (hist.index < day0 + timedelta(hours=5))]
    if decided >= day0 + timedelta(hours=5) and len(lon):
        p = float(lon.high.max() if long else lon.low.min())
        if ahead(p) and untaken(p, day0 + timedelta(hours=5)):
            out.append(("london", p))
    side = "high" if long else "low"
    tol = entry * TOL_BP / 1e4
    for tf in ("15m", "1h", "4h", "1d"):
        bars = resample(hist, tf)
        bars = bars[bars.close_ts <= decided]
        sw = [e for e in swings(bars, tf) if e.ts <= decided]
        for lv in swing_levels(sw):
            if lv.side == side and ahead(lv.price) and untaken(lv.price, lv.valid_from):
                out.append((f"swing_{tf}", float(lv.price)))
        if tf in ("1h", "4h"):
            for lv in equal_levels(bars, sw, tol):
                if lv.side == side and lv.valid_from <= decided and ahead(lv.price) and untaken(lv.price, lv.valid_from):
                    out.append((f"eq_{tf}", float(lv.price)))
        if tf in ("1h", "4h", "1d"):
            for g in fvgs(bars, tf):
                if g.ts > decided or g.direction == ("bull" if long else "bear"):
                    continue
                near, far = (g.bottom, g.top) if long else (g.top, g.bottom)
                seg = hist[hist.index > g.ts]
                filled = (not seg.empty) and (seg.high.max() >= far if long else seg.low.min() <= far)
                if filled or not ahead(near):
                    continue
                for part, p in (("near", near), ("ce", (near + far) / 2), ("far", far)):
                    out.append((f"fvg_{tf}_{part}", float(p)))
    return out


def first_hit(path: pd.DataFrame, price: float, long: bool) -> pd.Timestamp | None:
    m = (path.high >= price) if long else (path.low <= price)
    return path.index[m.argmax()] if m.any() else None


def job(args):
    model, asset = args
    d = pd.read_parquet(MODELS[model].format(a=asset))
    d = d[(d.status == "traded") & d.filled_at.notna()]
    d = d[(pd.to_datetime(d.day).dt.date >= START) & (pd.to_datetime(d.day).dt.date < CUT)]
    bars = dukascopy.load(asset, START - timedelta(days=30), CUT + timedelta(days=4))
    rows = []
    for r in d.itertuples():
        day = pd.Timestamp(r.day).date()
        dec, fill = pd.Timestamp(r.decided_at), pd.Timestamp(r.filled_at)
        long, entry, stop = r.side == "long", float(r.entry), float(r.stop)
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        hist = bars[(bars.index >= dec - LOOKBACK) & (bars.index < dec)]
        ctx = build_context(bars[bars.index < pd.Timestamp(datetime.combine(day, time(0)), tz=NY) + timedelta(hours=17)], day)
        close = pd.Timestamp(datetime.combine(day, time(16, 55)), tz=NY)
        nxt = close + timedelta(days=1 if day.weekday() < 4 else 3)
        path = bars[(bars.index >= fill) & (bars.index <= nxt)]
        t_stop = first_hit(path, stop, not long)
        seen = set()
        for kind, price in levels_ahead(hist, ctx, dec, long, entry):
            key = (kind, round(price, 2))
            if key in seen:
                continue
            seen.add(key)
            t = first_hit(path, price, long)
            rows.append(dict(model=model, asset=asset, day=str(day), decided=dec, side=r.side, kind=kind, price=price,
                             dist_r=abs(price - entry) / risk, trade_r=r.r, runner_r=r.runner_r,
                             before_stop=t is not None and (t_stop is None or t < t_stop),
                             by_close=t is not None and t <= close, by_next=t is not None))
    print(model, asset, len(d), "trades", len(rows), "levels", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    os.environ.setdefault("ICT_COST_BASIS", "futures")
    jobs = [(m, x) for m in MODELS for x in ASSETS]
    with ProcessPoolExecutor(a.workers) as ex:
        rows = [r for part in ex.map(job, jobs) for r in part]
    df = pd.DataFrame(rows)
    df.to_parquet("reports/liquidity-reach.parquet")
    df["family"] = df.kind.str.replace(r"_(near|ce|far)$", "", regex=True)
    df["dist"] = pd.cut(df.dist_r, BUCKETS, right=False, labels=["0-1R", "1-2R", "2-3R", "3-5R", "5-10R", "10R+"])
    for m, g in df.groupby("model"):
        print(f"\n=== {m}: {g.decided.nunique()} trades, {len(g)} levels ahead (median {g.groupby('decided').size().median():.0f} per trade)")
        t = g.groupby(["kind", "dist"], observed=True).before_stop.agg(["size", "mean"]).unstack("dist")
        print("reached before the stop — share (n):")
        print(pd.DataFrame({c: [f"{t['mean'][c][k]:.0%} ({int(t['size'][c][k])})" if pd.notna(t["size"][c][k]) else ""
                               for k in t.index] for c in t["mean"].columns}, index=t.index).to_string())
        s = g.groupby("kind").agg(n=("price", "size"), trades=("decided", "nunique"), med_r=("dist_r", "median"),
                                   before_stop=("before_stop", "mean"), by_close=("by_close", "mean"), by_next=("by_next", "mean"))
        print("\nby type:")
        print(s.round(2).to_string())


if __name__ == "__main__":
    main()
