"""Order-flow data (CME via Databento) — pipeline stage 0 for the order-flow tests.

    uv run python -m ict_engine.data.orderflow quote 2024-01-01 2026-01-01      # price check (free), no download
    uv run python -m ict_engine.data.orderflow fetch 2024-01-01 2026-01-01      # monthly TBBO files → data/orderflow/
    uv run python -m ict_engine.data.orderflow check 2024-01                    # aggressor-side sanity check

Data: GLBX.MDP3, schema ``tbbo`` = every trade plus the best bid/offer just before it. Symbol ``NQ.v.0`` =
continuous front month by volume. The API key is read from ``.env`` (DATABENTO_API_KEY, git-ignored) or the
environment, and is never printed. Pre-registration: research/preregistered-orderflow-NQ-2024-2025.md.

Side convention (Databento): a trade's ``side`` is the initiating (aggressor) side: B = buy, A = sell, N = none.
``check`` confirms it on real data: buy-aggressor trades should print at the ask.
"""

from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "orderflow"
NY = "America/New_York"
DATASET, SCHEMA, SYMBOL = "GLBX.MDP3", "tbbo", "NQ.v.0"
KEEP = ["price", "size", "side", "bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00"]
SIGN = {"B": 1, "A": -1}


def api_key(env_file: Path = ROOT / ".env") -> str:
    key = os.environ.get("DATABENTO_API_KEY")
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "DATABENTO_API_KEY":
                key = v.strip().strip("'\"")
    if not key:
        raise SystemExit("DATABENTO_API_KEY not set (.env or environment)")
    return key


def client():
    import databento as db                       # optional dependency (uv add databento)
    return db.Historical(api_key())


def months(start: date, end: date) -> list[tuple[str, str]]:
    """[start, end) split into calendar months as ISO dates."""
    edges = pd.date_range(pd.Timestamp(start).to_period("M").to_timestamp(), pd.Timestamp(end), freq="MS")
    pts = sorted({pd.Timestamp(start), *[e for e in edges if e > pd.Timestamp(start)], pd.Timestamp(end)})
    return [(a.date().isoformat(), b.date().isoformat()) for a, b in zip(pts, pts[1:])]


def quote(start: date, end: date, symbol: str = SYMBOL) -> float:
    c = client()
    return float(c.metadata.get_cost(dataset=DATASET, symbols=[symbol], stype_in="continuous", schema=SCHEMA,
                                     start=str(start), end=str(end)))


def fetch(start: date, end: date, symbol: str = SYMBOL, out: Path = OUT, max_usd: float = 125.0) -> list[Path]:
    """Download month by month after a total quote. Stops before spending more than ``max_usd``."""
    total = quote(start, end, symbol)
    if total > max_usd:
        raise SystemExit(f"quote ${total:.2f} exceeds the ${max_usd:.2f} cap; nothing downloaded")
    c = client()
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for a, b in months(start, end):
        p = out / f"{symbol.split('.')[0]}-{SCHEMA}-{a[:7]}.parquet"
        if p.exists():
            paths.append(p)
            continue
        data = c.timeseries.get_range(dataset=DATASET, symbols=[symbol], stype_in="continuous", schema=SCHEMA,
                                      start=a, end=b)
        df = data.to_df()
        tidy(df).to_parquet(p)
        paths.append(p)
        print(p.name, len(df))
    return paths


# --- pure pieces (unit-tested) --------------------------------------------------------------------------

def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Databento TBBO frame → trades indexed by NY event time, only the columns we use."""
    idx = pd.to_datetime(df["ts_event"] if "ts_event" in df else df.index, utc=True)
    out = df[[c for c in KEEP if c in df]].copy()
    out.index = pd.DatetimeIndex(idx).tz_convert(NY)
    out.index.name = "ts"
    return out.sort_index()


def signed(trades: pd.DataFrame) -> pd.Series:
    """+size for buy-aggressor trades, −size for sell-aggressor, 0 when the side is unknown."""
    return trades["size"] * trades["side"].map(SIGN).fillna(0)


def bars_1m(trades: pd.DataFrame) -> pd.DataFrame:
    """1m OHLC + volume, buy/sell aggressor volume and delta, indexed at the bar's start minute (like Dukascopy)."""
    s = signed(trades)
    g = trades.assign(buy=s.clip(lower=0), sell=(-s).clip(lower=0)).groupby(trades.index.floor("1min"))
    out = pd.DataFrame({"open": g.price.first(), "high": g.price.max(), "low": g.price.min(),
                        "close": g.price.last(), "volume": g["size"].sum(), "buy": g.buy.sum(), "sell": g.sell.sum()})
    out["delta"] = out.buy - out.sell
    out.index.name = "ts"
    return out


def imbalance(bars: pd.DataFrame, end: pd.Timestamp, minutes: int = 5, side: str = "long") -> float:
    """Aligned imbalance over the ``minutes`` bars ending at ``end`` (inclusive): (buy − sell)/(buy + sell),
    sign-flipped for shorts so > 0 means flow in the trade's direction. NaN when nothing traded."""
    w = bars[(bars.index > end - pd.Timedelta(minutes=minutes)) & (bars.index <= end)]
    tot = float(w.buy.sum() + w.sell.sum())
    if tot == 0:
        return float("nan")
    i = float(w.buy.sum() - w.sell.sum()) / tot
    return i if side == "long" else -i


def side_check(trades: pd.DataFrame) -> dict:
    """Where buy/sell-aggressor trades print relative to the quote: share at/above the ask, at/below the bid."""
    t = trades.dropna(subset=["bid_px_00", "ask_px_00"])
    res = {}
    for s in ("B", "A"):
        x = t[t.side == s]
        res[s] = {"n": len(x), "at_ask": float((x.price >= x.ask_px_00).mean()) if len(x) else np.nan,
                  "at_bid": float((x.price <= x.bid_px_00).mean()) if len(x) else np.nan}
    return res


def load(start: date, end: date, symbol: str = SYMBOL, root: Path = OUT) -> pd.DataFrame:
    """Cached trades for [start, end) (NY dates)."""
    files = [root / f"{symbol.split('.')[0]}-{SCHEMA}-{a[:7]}.parquet" for a, _ in months(start, end)]
    df = pd.concat([pd.read_parquet(f) for f in files if f.exists()])
    lo, hi = pd.Timestamp(start, tz=NY), pd.Timestamp(end, tz=NY)
    return df[(df.index >= lo) & (df.index < hi)]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.data.orderflow")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("quote", "fetch"):
        x = sub.add_parser(name)
        x.add_argument("start", type=date.fromisoformat)
        x.add_argument("end", type=date.fromisoformat)
        x.add_argument("--symbol", default=SYMBOL)
        x.add_argument("--max-usd", type=float, default=125.0)
    c = sub.add_parser("check")
    c.add_argument("month", help="YYYY-MM")
    a = ap.parse_args(argv)
    if a.cmd == "quote":
        print(f"{a.symbol} {SCHEMA} {a.start} → {a.end}: ${quote(a.start, a.end, a.symbol):.2f}")
    elif a.cmd == "fetch":
        fetch(a.start, a.end, a.symbol, max_usd=a.max_usd)
    else:
        print(side_check(pd.read_parquet(OUT / f"{SYMBOL.split('.')[0]}-{SCHEMA}-{a.month}.parquet")))


if __name__ == "__main__":
    main()
