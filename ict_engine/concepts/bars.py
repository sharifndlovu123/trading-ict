"""Resample 1-minute NY bars to higher timeframes (framework.md §2).

Every timeframe is built from the 1m base so an H1 POI and an M1 entry share
exact boundaries. Bins are computed on **NY wall-clock time**, so they stay
aligned across DST changes:

    m/h timeframes  floor of wall-clock time (H4 bins start 18,22,02,06,10,14)
    1d              trading day: 18:00 → 17:00 next day (futures convention)
    1w              trading week: Sunday 18:00 → Friday 17:00

Each output bar's index is the timestamp of its **first** 1m bar, and
``close_ts`` is the timestamp of its last 1m bar — events detected on a HTF bar
may only be used after ``close_ts`` (no look-ahead).
"""

from __future__ import annotations

import pandas as pd

from ict_engine.concepts.clock import trading_day

TIMEFRAMES = ("1m", "2m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w")


def _bin_keys(index: pd.DatetimeIndex, tf: str) -> pd.Index:
    naive = index.tz_localize(None)
    if tf == "1d":
        return pd.Index(pd.to_datetime(trading_day(index)), name="bin")
    if tf == "1w":
        days = pd.to_datetime(trading_day(index))
        return pd.Index(days - pd.to_timedelta(days.day_of_week, unit="D"), name="bin")  # Monday of the week
    if tf == "4h":
        return pd.Index((naive - pd.Timedelta(hours=2)).floor("4h") + pd.Timedelta(hours=2), name="bin")
    freq = tf.replace("m", "min")
    return pd.Index(naive.floor(freq), name="bin")


def resample(bars: pd.DataFrame, tf: str) -> pd.DataFrame:
    """OHLCV bars at timeframe ``tf`` from NY-indexed 1m bars."""
    if tf not in TIMEFRAMES:
        raise ValueError(f"timeframe {tf!r} not in {TIMEFRAMES}")
    if tf == "1m":
        out = bars.copy()
        out["close_ts"] = out.index
        return out
    df = bars.copy()
    df["_ts"] = df.index
    g = df.groupby(_bin_keys(bars.index, tf), sort=True)
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "_ts": ["first", "last"]}
    if "volume" in df:
        agg["volume"] = "sum"
    out = g.agg(agg)
    out.columns = ["open", "high", "low", "close", "first_ts", "close_ts"] + (["volume"] if "volume" in df else [])
    out = out.set_index("first_ts")
    out.index.name = "ts"
    return out[["open", "high", "low", "close"] + (["volume"] if "volume" in df else []) + ["close_ts"]]
