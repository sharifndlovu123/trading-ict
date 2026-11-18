"""Candles for the v2 chart: read the 1-minute files in `data/bars/` and build every timeframe from them.

This is plumbing for a display. It holds no trading idea: no levels, no patterns, no rules. Times are New York clock
times written as epoch seconds, so a candle marked 09:30 is 09:30 in New York whatever the season.

The higher timeframes follow the trading clock: a trading day runs from 6 p.m. to 5 p.m. the next day, so Sunday
evening already belongs to Monday; 4-hour candles start at 6 p.m.; a week is Monday's trading day to Friday's.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data" / "bars"
NY = "America/New_York"
FOLDERS = {"US100": "usatechidxusd", "US500": "usa500idxusd", "US30": "usa30idxusd", "US2000": "ussc2000idxusd",
           "DE40": "deuidxeur", "UK100": "gbridxgbp", "XAUUSD": "xauusd", "XAGUSD": "xagusd", "DXY": "dollaridxusd", "EURUSD": "eurusd"}
TIMEFRAMES = ["1M", "1W", "1D", "4h", "1h", "15m", "5m", "1m"]
MINUTES = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h"}
OHLC = {"open": "first", "high": "max", "low": "min", "close": "last"}


def available(root: Path = DATA) -> list[str]:
    """The instruments that have candle files, in a fixed order."""
    return [name for name, folder in FOLDERS.items() if any((root / folder).glob("*-bid.parquet"))]


def load_1m(asset: str, root: Path = DATA) -> pd.DataFrame:
    """Every 1-minute candle on disk for an instrument, indexed by New York clock time (no timezone attached)."""
    files = sorted((root / FOLDERS[asset]).glob("*-bid.parquet"))
    if not files:
        raise FileNotFoundError(f"no candle files for {asset} in {root / FOLDERS[asset]}")
    df = pd.concat(pd.read_parquet(f, columns=list(OHLC)) for f in files).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df.index = df.index.tz_convert(NY).tz_localize(None)
    return df


def trading_day(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """The trading day each minute belongs to: 6 p.m. starts the next day."""
    return (index + pd.Timedelta(hours=6)).normalize()


def resample(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    """1-minute candles (New York clock index) into one timeframe. The last candle may still be forming."""
    if tf == "1m":
        return df[list(OHLC)]
    if tf in MINUTES:
        offset = "2h" if tf == "4h" else None                      # 4-hour candles start at 6 p.m.: 18, 22, 02, 06, 10, 14
        return df.resample(MINUTES[tf], offset=offset).agg(OHLC).dropna()
    day = trading_day(df.index)
    if tf == "1D":
        key = day
    elif tf == "1W":
        key = day - pd.to_timedelta(day.dayofweek, unit="D")       # the Monday of that trading week
    elif tf == "1M":
        key = day.to_period("M").to_timestamp()
    else:
        raise ValueError(f"unknown timeframe {tf}")
    out = df.groupby(key).agg(OHLC)
    out.index.name = None
    return out


def to_candles(df: pd.DataFrame, last: int | None = None) -> list[dict]:
    """Rows into the dicts the page and the concept tools use: time (epoch seconds of the New York clock), open, high, low, close."""
    if last:
        df = df.tail(last)
    secs = (df.index - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
    return [{"time": int(t), "open": float(o), "high": float(h), "low": float(lo), "close": float(c)}
            for t, o, h, lo, c in zip(secs, df["open"], df["high"], df["low"], df["close"])]
