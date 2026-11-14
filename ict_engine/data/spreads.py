"""Measured spreads: Dukascopy ask − bid, per minute → hourly medians → an expected spread per trade.

    uv run python -m ict_engine.data.spreads build all 2021-10-01 2026-11-12   (needs bid AND ask bars)
    → data/spreads/<dukascopy_id>.parquet (git-ignored, re-buildable)

Bars are bid prices. A long buys at the ask and sells at the bid, so one round trip costs about one
spread. The cost of a trade decided at time t is the **expected** spread: the median spread in the
same NY half-hour of the day over the previous ``lookback`` trading days. Half-hours, because index
spreads step at the 09:30 cash open (US100 ~3.45 before, ~1.45 after). That uses no data from the trade's
own day (no look-ahead), follows the time-of-day pattern (wide overnight, tight after 09:30), and
scales with the price level (gold's spread grows as gold rises).
"""

from __future__ import annotations

import argparse
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "data"
NY = "America/New_York"


def minute_spreads(bid: pd.DataFrame, ask: pd.DataFrame) -> pd.Series:
    """ask.close − bid.close on the minutes both sides have; crossed quotes count as 0."""
    s = (ask.close - bid.close).dropna()
    return s.clip(lower=0.0)


def hourly_table(spreads: pd.Series) -> pd.DataFrame:
    """Median / 90th percentile / count of the minute spreads per NY half-hour (index = bucket start)."""
    g = spreads.groupby(spreads.index.floor("30min"))
    return pd.DataFrame({"median": g.median(), "p90": g.quantile(0.9), "n": g.size()})


def expected_table(hourly: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """Per (date, half-hour slot): median of that slot's medians over the previous ``lookback`` trading days.
    ``hour`` holds the slot as hour + 0.5 for the :30 half (09:30 → 9.5)."""
    h = hourly.copy()
    h["date"], h["hour"] = h.index.date, h.index.hour + (h.index.minute >= 30) * 0.5
    out = []
    for hour, g in h.groupby("hour"):
        g = g.sort_index()
        prev = g["median"].shift(1).rolling(lookback, min_periods=1).median()
        out.append(pd.DataFrame({"date": g.date, "hour": hour, "expected": prev.to_numpy()}, index=g.index))
    t = pd.concat(out).dropna(subset=["expected"]).sort_index()
    return t[["date", "hour", "expected"]]


class SpreadBook:
    """Expected round-trip spread for (asset, time); None when there's no measurement."""

    def __init__(self, tables: dict[str, pd.DataFrame]):
        self._by = {a: {(d, h): float(v) for d, h, v in zip(t.date, t.hour, t.expected)} for a, t in tables.items()}

    def spread(self, asset: str, ts: pd.Timestamp) -> float | None:
        return self._by.get(asset, {}).get((ts.date(), ts.hour + (0.5 if ts.minute >= 30 else 0.0)))

    @classmethod
    def load(cls, root: Path = ROOT) -> "SpreadBook":
        from ict_engine.data.instruments import ASSETS
        tables = {}
        for name, a in ASSETS.items():
            p = Path(root) / "spreads" / f"{a.dukascopy_id}.parquet"
            if p.exists():
                t = pd.read_parquet(p)
                t["date"] = pd.to_datetime(t.date).dt.date
                tables[name] = t
        return cls(tables)


@lru_cache(maxsize=1)
def book() -> SpreadBook:
    return SpreadBook.load()


def save(asset_name: str, table: pd.DataFrame, root: Path = ROOT) -> Path:
    from ict_engine.data.instruments import get
    p = Path(root) / "spreads" / f"{get(asset_name).dukascopy_id}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    table.assign(date=pd.to_datetime(table.date)).to_parquet(p)
    return p


def build(asset_name: str, start: date, end: date, lookback: int = 5) -> Path:
    from ict_engine.data.dukascopy import load
    bid = load(asset_name, start, end, price="bid")
    ask = load(asset_name, start, end, price="ask")
    hourly = hourly_table(minute_spreads(bid, ask))
    return save(asset_name, expected_table(hourly, lookback))


def main(argv=None):
    from ict_engine.data.instruments import COST_BPS
    ap = argparse.ArgumentParser(prog="ict_engine.data.spreads")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("asset", help="asset name or 'all' (the traded set)")
    b.add_argument("start", type=date.fromisoformat)
    b.add_argument("end", type=date.fromisoformat)
    b.add_argument("--lookback", type=int, default=5)
    a = ap.parse_args(argv)
    for name in (list(COST_BPS) if a.asset == "all" else [a.asset]):
        print(name, build(name, a.start, a.end, a.lookback))


if __name__ == "__main__":
    main()
