"""Cost realism check on CME NQ 2024 (futures basis): is "1 tick + $4.50, fills at the exact price" honest?

    A. spread      quoted bid-ask on the TBBO day (2024-03-05), by NY hour
    B. stop slip   for every stop-out of the five models (reports/nqcme): the stop triggers at the first trade at or
                   through it; a stop-market order then fills at the first trade by an aggressor on our side
                   (sell stop: a seller 'A' hitting the bid). Slip = how far beyond the stop that fill is.
    C. touch fills the simulator fills a limit when price merely touches it. On 1m CME bars: winning trades whose
                   price never traded ≥ 1 tick through the entry (a touch-only fill; in the queue you may not get it),
                   and TP1 hits that were touch-only.
    Impact: expectancy (all out at TP1, futures costs) as simulated, with real stop slippage, and with the worst case
    for touch fills (touch-only entries → no trade; touch-only TP1 → the trade runs on to its stop or the 16:00 exit).

    uv run python research/scripts/cost_check.py      # → research/cost-check-NQ-2024.md
"""
from datetime import date, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from ict_engine.data import orderflow as of

NY = "America/New_York"
TICK = 0.25
MODELS = ("2022_model", "cameron", "mmxm", "silver_bullet", "pd_return")
OUT = Path("research/cost-check-NQ-2024.md")


def spread_table() -> pd.DataFrame:
    t = pd.read_parquet(of.OUT / "NQ-tbbo-day-2024-03-05.parquet")
    t["spread"] = t.ask_px_00 - t.bid_px_00
    t["hour"] = t.index.hour
    g = t.groupby("hour").spread
    return pd.DataFrame({"trades": g.size(), "mean_pts": g.mean().round(3),
                         "one_tick_share": g.apply(lambda s: (s.round(2) == TICK).mean()).round(3)})


def month_trades(cache: dict, ts: pd.Timestamp) -> pd.DataFrame:
    key = ts.strftime("%Y-%m")
    if key not in cache:
        cache.clear()                                   # one month in memory at a time
        d0 = ts.normalize().replace(day=1).date()
        cache[key] = of.load(d0 - timedelta(days=1), (pd.Timestamp(d0) + pd.offsets.MonthBegin(1)).date() + timedelta(days=1))
    return cache[key]


def stop_slip(trades: pd.DataFrame, side: str, stop: float, minute: pd.Timestamp) -> float | None:
    """Points beyond the stop at which a stop-market order fills (≥ 0 = worse than the stop)."""
    seg = trades[(trades.index >= minute) & (trades.index < minute + timedelta(minutes=2))]
    if seg.empty:
        return None
    long = side == "long"                               # a long's stop is a sell stop
    hit = seg.price <= stop if long else seg.price >= stop
    if not hit.any():
        return None
    after = seg[seg.index >= seg.index[hit.to_numpy().argmax()]]
    ours = after[after.side == ("A" if long else "B")]
    if ours.empty:
        return None
    px = float(ours.price.iloc[0])
    return (stop - px) if long else (px - stop)


def after_tp_outcome(bars: pd.DataFrame, r) -> float:
    """R if a touch-only TP1 did not fill: the trade runs on to its stop or the 16:00 exit (all out)."""
    long = r.side == "long"
    close = pd.Timestamp(r.day).tz_localize(NY) + timedelta(hours=16)
    seg = bars[(bars.index > pd.Timestamp(r.exit_at)) & (bars.index < close)]
    risk = abs(r.entry - r.stop)
    cost_r = (TICK + 4.5 / 20) / risk
    for _, b in seg.iterrows():
        if (b.low <= r.stop) if long else (b.high >= r.stop):
            return -1.0 - cost_r
        if (b.high >= r.tp1 + TICK) if long else (b.low <= r.tp1 - TICK):
            return r.r                                    # traded through TP1 later: filled after all
    px = float(seg.close.iloc[-1]) if len(seg) else r.tp1
    return ((px - r.entry) if long else (r.entry - px)) / risk - cost_r


def main():
    bars = of.load(date(2023, 12, 25), date(2025, 1, 2), schema=of.BARS)
    cache, rows = {}, []
    for m in MODELS:
        d = pd.read_parquet(f"reports/nqcme/{m}.parquet")
        t = d[d.status == "traded"].copy()
        for _, r in t.iterrows():
            long, risk = r.side == "long", abs(r.entry - r.stop)
            fill, ex = pd.Timestamp(r.filled_at), pd.Timestamp(r.exit_at)
            seg = bars[(bars.index >= fill) & (bars.index <= ex)]
            through = (seg.low <= r.entry - TICK).any() if long else (seg.high >= r.entry + TICK).any()
            slip = tp_touch = None
            if r.exit == "stop":
                slip = stop_slip(month_trades(cache, ex), r.side, r.stop, ex)
            if r.exit == "tp1":
                hit_bar = bars[bars.index == ex]
                tp_touch = bool(len(hit_bar)) and not (((hit_bar.high >= r.tp1 + TICK) if long else (hit_bar.low <= r.tp1 - TICK)).iloc[0])
            rows.append({"model": m, "exit": r.exit, "r": r.r, "risk_pts": risk, "entry_through": bool(through),
                         "slip_pts": slip, "tp_touch_only": tp_touch,
                         "r_if_tp_unfilled": after_tp_outcome(bars, r) if tp_touch else None})
    df = pd.DataFrame(rows)
    df.to_parquet("reports/nqcme/cost-check.parquet")

    lines = ["# Cost realism check: CME NQ 2024, futures basis", "",
             "Run once on the five models' 2024 CME NQ trades (`reports/nqcme`, futures costs: 1 tick + $4.50 = 0.475 pt "
             "round trip, every fill at the exact price). Script: `research/scripts/cost_check.py`; rows: "
             "`reports/nqcme/cost-check.parquet`.", "", "## A. Quoted spread (TBBO, 2024-03-05)", "",
             "| NY hour | trades | mean spread (pts) | share at 1 tick |", "|---|---|---|---|"]
    for h, s in spread_table().iterrows():
        lines.append(f"| {h:02d} | {s.trades} | {s.mean_pts} | {s.one_tick_share:.1%} |")
    lines += ["", "## B–C. Stop slippage and touch fills, and what they do to expectancy", "",
              "| model | trades | stops | stop slip median / p90 (pts) | slip in R (mean) | wins touch-only at entry | "
              "TP1 touch-only | exp R as simulated | + real stop slip | + worst case for touch fills |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for m, g in df.groupby("model", sort=False):
        st = g[g.exit == "stop"].dropna(subset=["slip_pts"])
        slip_r = (st.slip_pts / st.risk_pts)
        wins = g[g.exit == "tp1"]
        r1 = g.r.copy()
        r1.loc[st.index] = st.r - slip_r
        r2 = r1.copy()
        tp_only = g.tp_touch_only.fillna(False).astype(bool)
        r2.loc[tp_only] = g.loc[tp_only, "r_if_tp_unfilled"]
        drop = (g.exit == "tp1") & ~g.entry_through
        lines.append(f"| {m} | {len(g)} | {len(st)} | {st.slip_pts.median():.2f} / {st.slip_pts.quantile(.9):.2f} | "
                     f"{slip_r.mean():.3f} | {drop.sum()} of {len(wins)} | {tp_only.sum()} of {len(wins)} | "
                     f"{g.r.mean():+.3f} | {r1.mean():+.3f} | {r2[~drop].mean():+.3f} |")
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
