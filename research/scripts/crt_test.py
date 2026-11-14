"""Candle Range Theory as a pattern: research/preregistered-crt-2026-11-14.md.

    nice uv run python research/scripts/crt_test.py      # → reports/crt-trades.parquet, research/crt-results-2026-11-14.md

Engine pieces only (resample, bias, simulate, cost_at); no engine code is changed. The FX 4h grid (01/05/09 NY) is built
here, since the engine's 4h is the CME grid.
"""
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import bias_prev_day_dol, completed_daily
from ict_engine.data import dukascopy
from ict_engine.data.instruments import cost_at
from ict_engine.models.base import TradePlan
from ict_engine.sim.simulate import simulate

ASSETS = ("US100", "US500", "US30", "XAUUSD", "XAGUSD")
START, END, HOLDOUT = date(2022, 1, 3), date(2024, 6, 28), 0.3
CUT = pd.Timestamp(START) + (pd.Timestamp(END) - pd.Timestamp(START)) * (1 - HOLDOUT)
EXPIRY_CANDLES = 3
ONE = pd.Timedelta(minutes=1)


def fx4h(bars: pd.DataFrame) -> pd.DataFrame:
    naive = bars.index.tz_localize(None)
    key = pd.Index((naive - pd.Timedelta(hours=1)).floor("4h") + pd.Timedelta(hours=1), name="bin")
    df = bars.assign(_ts=bars.index)
    out = df.groupby(key, sort=True).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                         close=("close", "last"), first_ts=("_ts", "first"), close_ts=("_ts", "last"))
    return out.set_index("first_ts")


def candles(bars: pd.DataFrame, frame: str) -> pd.DataFrame:
    return fx4h(bars) if frame == "4h_fx" else resample(bars, {"4h_cme": "4h"}.get(frame, frame))


def events(c: pd.DataFrame, frame: str, timed: str | None):
    """(i, side, kind) for C1 = row i, C2 = row i+1. kind 'inside' = CRT, 'outside' = one-sided sweep closed beyond."""
    h, l, cl = c.high.to_numpy(), c.low.to_numpy(), c.close.to_numpy()
    starts = c.index
    for i in range(len(c) - 1 - EXPIRY_CANDLES):
        if timed and starts[i].strftime("%H:%M") != timed:
            continue
        gap = starts[i + 1] - starts[i]
        if frame != "1d" and gap > pd.Timedelta(hours=4 if "4h" in frame else 1) + pd.Timedelta(hours=1):
            continue                                   # a halt/weekend between C1 and C2: not consecutive
        up, dn = h[i + 1] > h[i], l[i + 1] < l[i]
        if up == dn:
            continue                                   # neither side or both sides taken
        side = "short" if up else "long"
        inside = l[i] < cl[i + 1] < h[i]
        beyond = (cl[i + 1] > h[i]) if up else (cl[i + 1] < l[i])
        kind = "inside" if inside else ("outside" if beyond else None)
        if kind:
            yield i, side, kind


def trading_date(ts: pd.Timestamp) -> date:
    return (ts + pd.Timedelta(hours=6)).date()       # 18:00 NY starts the next trading day


CELLS = [("1h", None), ("4h_cme", None), ("4h_fx", None), ("1d", None), ("4h_fx", "01:00"), ("1h", "08:00")]
NAMES = {("1h", None): "1h", ("4h_cme", None): "4h CME grid", ("4h_fx", None): "4h FX grid", ("1d", None): "1d",
         ("4h_fx", "01:00"): "1-5-9 (4h 01:00 → 05:00)", ("1h", "08:00"): "1H 08 → 09"}


def run_asset(asset: str) -> list[dict]:
    bars = dukascopy.load(asset, START - timedelta(days=90), END + timedelta(days=5))
    daily = resample(bars, "1d")
    bias_cache: dict[date, str] = {}

    def bias(d):
        if d not in bias_cache:
            done = completed_daily(daily, d)
            bias_cache[d] = bias_prev_day_dol(done)[0] if len(done) > 25 else "neutral"
        return bias_cache[d]

    idx = bars.index
    rows = []
    for frame, timed in CELLS:
        c = candles(bars, frame)
        cts = c.close_ts.to_numpy()
        for i, side, kind in events(c, frame, timed):
            placed = pd.Timestamp(cts[i + 1])
            day = trading_date(placed + ONE)
            if not (START <= day <= END):
                continue
            c1, c2 = c.iloc[i], c.iloc[i + 1]
            long = side == "long"
            stop = c2.low if long else c2.high
            mid, far = (c1.high + c1.low) / 2, (c1.high if long else c1.low)
            t_exit = pd.Timestamp(cts[i + 1 + EXPIRY_CANDLES]) + ONE
            a, b = idx.searchsorted(placed, "left"), idx.searchsorted(t_exit, "right")
            seg = bars.iloc[a:b]
            if len(seg) < 2:
                continue
            px = float(seg.open.iloc[1])
            tp1 = mid if ((mid > px) if long else (mid < px)) else far
            plan = TradePlan(side, placed, t_exit, px, stop, tp1, far, order="market")
            out = {"asset": asset, "frame": frame, "timed": timed or "", "kind": kind, "side": side, "day": day,
                   "placed": placed, "bias": bias(day), "risk": abs(px - stop)}
            for basis in ("cfd", "futures"):
                os.environ["ICT_COST_BASIS"] = basis
                res = simulate(plan, seg, t_exit, cost_at(asset, px, placed))
                out[f"{basis}_exit"] = res.exit_reason
                out[f"{basis}_r"] = res.r
                out[f"{basis}_runner_r"] = res.runner_r
                out[f"{basis}_vote"] = res.vote
            rows.append(out)
    print(asset, len(rows), flush=True)
    return rows


def stats(x: pd.Series) -> tuple[int, float, float]:
    x = x.dropna()
    n = len(x)
    if n < 2:
        return n, float("nan"), float("nan")
    return n, x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(n))


def main():
    df = pd.DataFrame([r for a in ASSETS for r in run_asset(a)])
    df.to_parquet("reports/crt-trades.parquet")
    traded = lambda g, b: g[~g[f"{b}_exit"].isin(["not_filled", "missed", "cancelled"])]
    agree = lambda g: g[((g.side == "long") & (g.bias == "bull")) | ((g.side == "short") & (g.bias == "bear"))]
    lines = ["# Candle Range Theory as a pattern: results (2026-11-14)", "",
             "Pre-registration: `research/preregistered-crt-2026-11-14.md`. Script `research/scripts/crt_test.py`; rows "
             f"`reports/crt-trades.parquet`. {', '.join(ASSETS)}, {START}→{END}; OOS from {CUT.date()}. Exp = runner R "
             "after costs (50% at C1's 50%, runner to the far end); TP1% = C1's 50% (or far end) hit before C2's wick.", ""]
    for basis in ("cfd", "futures"):
        lines += [f"## {basis}", "", "| # | cell | filter | IS n | IS exp | OOS n | OOS TP1% | OOS exp (all out) | OOS exp | z | pass |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        k = 0
        for key in CELLS:
            g0 = df[(df.frame == key[0]) & (df.timed == (key[1] or "")) & (df.kind == "inside")]
            for filt, g in (("all", g0), ("bias agrees", agree(g0))):
                k += 1
                t = traded(g, basis)
                ins, oos = t[pd.to_datetime(t.day) < CUT], t[pd.to_datetime(t.day) >= CUT]
                ni, ei, _ = stats(ins[f"{basis}_runner_r"])
                no, eo, z = stats(oos[f"{basis}_runner_r"])
                _, ea, _ = stats(oos[f"{basis}_r"])
                ok = no >= 30 and eo > 0 and z >= 2.6 and ei > 0
                lines.append(f"| {k} | {NAMES[key]} | {filt} | {ni} | {ei:+.3f} | {no} | {oos[f'{basis}_vote'].mean():.0%} | "
                             f"{ea:+.3f} | {eo:+.3f} | {z:+.1f} | {'yes' if ok else 'no'} |")
        lines += ["", f"Descriptive ({basis}, all periods): CRT (closed back inside) vs a one-sided sweep that closed outside, "
                  "same trade (fade toward C1's 50%).", "", "| cell | inside: n / TP1% / exp | outside: n / TP1% / exp |", "|---|---|---|"]
        for key in CELLS:
            g = df[(df.frame == key[0]) & (df.timed == (key[1] or ""))]
            cellv = []
            for kind in ("inside", "outside"):
                t = traded(g[g.kind == kind], basis)
                n, e, _ = stats(t[f"{basis}_runner_r"])
                cellv.append(f"{n} / {t[f'{basis}_vote'].mean():.0%} / {e:+.3f}")
            lines.append(f"| {NAMES[key]} | {cellv[0]} | {cellv[1]} |")
        lines.append("")
    open("research/crt-results-2026-11-14.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
