"""Market conditions for a trading day, known before it starts (concept layer: facts, not a score).

Sharif 2026-11-16: "identify the conditions of the market … if something works really well in most conditions that's a
keeper, if something works when the market is consolidating we know this helps more during consolidation periods, or
if something works more when it's clearly bullish or bearish."

For each trading day, from completed daily bars up to the day before (no look-ahead):
  state      "trending up" | "trending down" | "consolidating": the 20-day efficiency ratio (net move ÷ the sum of the
             daily moves; 1 = a straight line, 0 = pure chop) at or above ``ER_TREND`` with the sign of the 20-day
             move, else consolidating
  backdrop   "bull" | "bear" | "mixed": the close against its 50-day average and the 50-day against the 200-day
             (100-day while there is less history)
  vol        "high" | "normal" | "low": the 20-day average daily range as a share of price, against its own median
             of the last 250 days (above 1.25× / below 0.8×)
  plus the numbers behind them (er20, ret20, ret60, adr_pct, vol_rel) and the distance from the 250-day high.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ER_TREND = 0.30
VOL_HIGH, VOL_LOW = 1.25, 0.80


def efficiency_ratio(close: pd.Series, n: int = 20) -> pd.Series:
    """|close − close n days ago| ÷ the sum of the absolute daily changes over those n days."""
    net = (close - close.shift(n)).abs()
    path = close.diff().abs().rolling(n).sum()
    return (net / path).where(path > 0)


def daily_regimes(daily: pd.DataFrame) -> pd.DataFrame:
    """One row per trading day (index = the day's bar), every column computed from bars BEFORE that day."""
    c, h, lo = daily["close"], daily["high"], daily["low"]
    er = efficiency_ratio(c, 20)
    ret20, ret60 = c / c.shift(20) - 1, c / c.shift(60) - 1
    ma50 = c.rolling(50, min_periods=30).mean()
    ma200 = c.rolling(200, min_periods=100).mean()
    adr_pct = ((h - lo) / c).rolling(20).mean()
    vol_rel = adr_pct / adr_pct.rolling(250, min_periods=60).median()
    high250 = c.rolling(250, min_periods=60).max()
    f = pd.DataFrame({"er20": er, "ret20": ret20, "ret60": ret60, "adr_pct": adr_pct, "vol_rel": vol_rel,
                      "from_high": c / high250 - 1, "above_ma50": c > ma50, "ma50_above_ma200": ma50 > ma200,
                      "_ma50": ma50, "_ma200": ma200})
    f = f.shift(1)                                           # known at the start of the day: yesterday's values
    state = np.where(f.er20 >= ER_TREND, np.where(f.ret20 > 0, "trending up", "trending down"), "consolidating")
    f["state"] = pd.Series(state, index=f.index).where(f.er20.notna())
    up = (f.above_ma50 == True) & (f.ma50_above_ma200 == True)       # noqa: E712
    down = (f.above_ma50 == False) & (f.ma50_above_ma200 == False)   # noqa: E712
    f["backdrop"] = pd.Series(np.where(up, "bull", np.where(down, "bear", "mixed")), index=f.index).where(f._ma200.notna())
    f["vol"] = pd.Series(np.where(f.vol_rel > VOL_HIGH, "high", np.where(f.vol_rel < VOL_LOW, "low", "normal")),
                         index=f.index).where(f.vol_rel.notna())
    return f.drop(columns=["_ma50", "_ma200"])
