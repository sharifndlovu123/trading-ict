"""Ten trade examples on CME NQ 2024 for Sharif's visual review: two per model (one TP1 win, one stop-out),
each with the timeframe ladder (1m, 5m, 15m, 1h, 4h, D), the day context and every bias rule as known at the
decision, and the higher-timeframe FVGs still open at that moment.

    uv run python research/scripts/trade_examples.py      # → out/trade-examples/index.html (+ data.json)
"""
import json
import math
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import build_context
from ict_engine.concepts.events import (equal_levels, fvgs, gap_lifecycle, liquidity_pools, order_blocks, quadrants,
                                       swing_levels, swings)
from ict_engine.data import orderflow as of

NY = "America/New_York"
OUT = Path("out/trade-examples")
MODELS = {"2022_model": "2022 model", "cameron": "Cameron", "mmxm": "MMxM", "silver_bullet": "Silver Bullet",
          "pd_return": "PD array return"}
SPAN = {"1m": timedelta(hours=10), "5m": timedelta(days=1.5), "15m": timedelta(days=5), "1h": timedelta(days=15),
        "4h": timedelta(days=60), "1d": timedelta(days=180)}
HTF_GAPS = ("15m", "1h", "4h", "1d")


def wall(ts) -> int:
    """NY wall-clock as epoch seconds, so a UTC chart axis reads New York time."""
    t = pd.Timestamp(ts).tz_convert(NY)
    return int(t.tz_localize(None).timestamp())


def num(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 2)


def candles(df):
    return [[wall(t), num(o), num(h), num(l), num(c)] for t, o, h, l, c in
            zip(df.index, df.open, df.high, df.low, df.close)]


def pick(runs: dict) -> list:
    out = []
    for m in MODELS:
        d = runs[m]
        t = d[(d.status == "traded")].copy()
        t["dt"] = pd.to_datetime(t.decided_at)
        for want in ("tp1", "stop"):
            c = t[t.exit == want]
            # spread across the year, deterministic: the trade closest to mid-year in H1 for wins, H2 for losses
            target = pd.Timestamp("2024-04-15", tz=NY) if want == "tp1" else pd.Timestamp("2024-09-16", tz=NY)
            if len(c):
                out.append((m, c.loc[(c.dt - target).abs().idxmin()]))
    return out


def open_htf_gaps(hist: pd.DataFrame, at: pd.Timestamp, price: float) -> list:
    rows = []
    for tf in HTF_GAPS:
        bars = resample(hist, tf)
        for g in fvgs(bars, tf):
            if g.ts > at:
                continue
            st = gap_lifecycle(g, hist, until=at)
            if st.filled or st.inverted:
                continue
            rows.append({"tf": tf, "dir": g.direction, "top": num(g.top), "bottom": num(g.bottom),
                         "from": wall(g.origin_ts), "dist": abs(g.ce - price)})
    rows.sort(key=lambda r: r["dist"])
    keep = []
    for tf in HTF_GAPS:                                    # nearest 3 per timeframe
        keep += [r for r in rows if r["tf"] == tf][:3]
    for r in keep:
        r.pop("dist")
    return keep


def open_htf_obs(hist: pd.DataFrame, at: pd.Timestamp, price: float) -> list:
    """Order blocks on 1D/4H/1H known at ``at`` (Sharif's open-confirmation rule), still intact: no body close
    beyond the far side of the block's body since it was confirmed. Nearest 2 per timeframe and direction, with quadrants."""
    rows = []
    for tf in ("1d", "4h", "1h"):
        bars = resample(hist, tf)
        for ob in order_blocks(bars, tf, confirm="open"):
            if ob.ts > at:
                continue
            top, bot = ob.meta["body"]
            after = bars[(bars.index > ob.ts) & (bars.index <= at)]
            closes = after.close
            broken = (closes > top).any() if ob.direction == "bear" else (closes < bot).any()
            if broken:
                continue
            rows.append({"tf": tf, "dir": ob.direction, "from": wall(ob.origin_ts), "known": wall(ob.ts),
                         "levels": {k: num(v) for k, v in quadrants(top, bot).items()},
                         "dist": abs((top + bot) / 2 - price)})
    keep = []
    for tf in ("1d", "4h", "1h"):
        for side in ("bull", "bear"):
            keep += sorted([r for r in rows if r["tf"] == tf and r["dir"] == side], key=lambda r: r["dist"])[:2]
    for r in keep:
        r.pop("dist")
    return keep


def short_name(m: str) -> str:
    if "_swing_" in m:
        tf, rest = m.split("_swing_")
        return f"{tf.upper().replace('1D', 'D')} {rest.split('@')[0]}"
    if "_eq" in m:
        tf, rest = m.split("_", 1)
        k = rest.split("@")[0]
        return f"{tf.upper().replace('1D', 'D')} {k[:3].upper()}" + (f"x{k[3:]}" if k[3:] else "")
    return m.upper().replace("_", " ")


def pools_at(hist: pd.DataFrame, at: pd.Timestamp, ctx, price: float) -> list:
    """Untaken liquidity at ``at``: the day's reference levels (PDH/PDL, PWH/PWL, Asia, …) plus equal highs/lows
    on D/4H/1H, merged into pools (levels within 2 bp). Nearest 3 per side."""
    levels = [lv for lv in ctx.liquidity]
    for tf in ("1d", "4h", "1h"):
        bars = resample(hist, tf)
        sw = swings(bars, tf)
        levels += equal_levels(bars, sw, tol=price * 2 / 1e4)
        if tf in ("1d", "4h"):                       # every old HTF high/low holds stops (single pools)
            levels += swing_levels(sw)
    live = []
    for lv in levels:
        if lv.valid_from > at:
            continue
        seg = hist[(hist.index > lv.valid_from) & (hist.index <= at)]
        taken = (seg.high > lv.price).any() if lv.side == "high" else (seg.low < lv.price).any()
        if not taken:
            live.append(lv)
    out = []
    for side in ("high", "low"):
        ps = [p for p in liquidity_pools(live, tol=price * 2 / 1e4) if p.side == side]
        ps = [p for p in ps if (p.price > price if side == "high" else p.price < price)]
        ps.sort(key=lambda p: abs(p.price - price))
        out += [{"side": side, "price": num(p.price), "inner": num(p.inner), "strength": p.strength,
                 "members": [short_name(m) for m in p.members]} for p in ps[:3]]
    return out


def main():
    runs = {p.stem: pd.read_parquet(p) for p in Path("reports/nqcme").glob("*.parquet") if p.stem in MODELS}
    allbars = of.load(date(2023, 10, 1), date(2025, 1, 1), schema=of.BARS)
    flow = of.OUT / "NQ-flow1m-2024.parquet"
    flow = pd.read_parquet(flow) if flow.exists() else None
    trades = []
    for m, r in pick(runs):
        day = pd.Timestamp(r.day).date()
        dec = pd.Timestamp(r.decided_at)
        end = pd.Timestamp(datetime.combine(day, time(16, 30)), tz=NY)
        hist_at = allbars[allbars.index <= dec]
        ctx = build_context(allbars[allbars.index < end], day)
        tfs = {}
        for tf, span in SPAN.items():
            lo = (dec - span) if tf != "1m" else pd.Timestamp(datetime.combine(day, time(6)), tz=NY)
            seg = allbars[(allbars.index >= lo) & (allbars.index < end)]
            tfs[tf] = candles(seg if tf == "1m" else resample(seg, tf))
        lo20, hi20 = ctx.ranges[20]
        item = {
            "id": f"{m}-{dec:%Y%m%d-%H%M}", "model": MODELS[m], "family": m, "variant": r.variant,
            "day": str(day), "weekday": f"{dec:%A}", "side": r.side, "window": r.window,
            "decided": wall(dec), "filled": wall(r.filled_at) if pd.notna(r.filled_at) else None,
            "exit_at": wall(r.exit_at) if pd.notna(r.exit_at) else None,
            "entry": num(r.entry), "stop": num(r.stop), "tp1": num(r.tp1), "final": num(r.final),
            "tp1_name": r.tp1_name, "exit": r.exit, "r": num(r.r), "poi": r.poi, "liquidity": r.liquidity,
            "bias_used": r.bias, "bias_rule": r.bias_rule,
            "biases": {k: list(v) for k, v in ctx.biases.items()},
            "levels": {k: num(v) for k, v in ctx.levels.items()},
            "range20": [num(lo20), num(hi20)], "eq20": num((lo20 + hi20) / 2),
            "pricing20": "premium" if r.entry > (lo20 + hi20) / 2 else "discount",
            "pools": pools_at(hist_at[hist_at.index >= dec - timedelta(days=45)], dec, ctx, r.entry),
            "htf_obs": open_htf_obs(hist_at[hist_at.index >= dec - timedelta(days=90)], dec, r.entry),
            "htf_gaps": open_htf_gaps(hist_at[hist_at.index >= dec - timedelta(days=60)], dec, r.entry),
            "candles": tfs,
        }
        if flow is not None:
            f = flow[(flow.index >= dec - timedelta(hours=2)) & (flow.index < end)]
            item["delta"] = [[wall(t), int(v)] for t, v in zip(f.index, f.delta)]
            item["I5"] = num(of.imbalance(flow, dec, 5, r.side))
        trades.append(item)
        print(item["id"], r.exit, item["r"], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.dumps({"generated": str(date.today()), "trades": trades}, separators=(",", ":"))
    (OUT / "data.json").write_text(data)
    page = Path("viewer/trade-examples.html").read_text().replace("/*__DATA__*/null", data)
    (OUT / "index.html").write_text(page)
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
