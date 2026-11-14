"""Order-flow data (CME via Databento) — pipeline stage 0 for the order-flow tests.

    uv run python -m ict_engine.data.orderflow quote 2024-01-01 2025-01-01 [--schema trades]   # price (free)
    uv run python -m ict_engine.data.orderflow fetch 2024-01-01 2025-01-01      # trades, 01:30–16:30 NY, monthly files
    uv run python -m ict_engine.data.orderflow bars 2024-01-01 2026-01-01       # CME 1m OHLCV (cheap, all hours)
    uv run python -m ict_engine.data.orderflow sidecheck 2024-03-05             # one day of TBBO → aggressor-side check

Data: GLBX.MDP3. Schema ``trades`` = every trade with its aggressor side (``tbbo`` adds the best bid/offer before
it and costs ~1.7×; bought for one day only, for the side check). Symbol ``NQ.v.0`` = continuous front month by
volume. Trades are bought only inside ``SESSION`` (NY time, weekdays): every model decision and exit in the
2022–24 trade store falls inside it (checked 2026-11-14), and it keeps one year under the $125 credit. The API key is read from ``.env`` (DATABENTO_API_KEY, git-ignored) or the
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
DATASET, SCHEMA, SYMBOL = "GLBX.MDP3", "trades", "NQ.v.0"
BARS = "ohlcv-1m"
SESSION = ("01:30", "16:30")
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


def quote(start: date, end: date, symbol: str = SYMBOL, schema: str = SCHEMA) -> float:
    """Price of the full [start, end) range. Windowed downloads cost less, so this is an upper bound."""
    c = client()
    return float(c.metadata.get_cost(dataset=DATASET, symbols=[symbol], stype_in="continuous", schema=schema,
                                     start=str(start), end=str(end)))


def path_for(symbol: str, schema: str, month: str, root: Path = OUT) -> Path:
    return root / f"{symbol.split('.')[0]}-{schema}-{month}.parquet"


def _get(c, symbol, schema, a, b) -> pd.DataFrame:
    data = c.timeseries.get_range(dataset=DATASET, symbols=[symbol], stype_in="continuous", schema=schema,
                                  start=a, end=b)
    return data.to_df()


def fetch(start: date, end: date, symbol: str = SYMBOL, out: Path = OUT, max_usd: float = 125.0,
          session: tuple[str, str] | None = SESSION) -> list[Path]:
    """Trades for [start, end), month by month, only inside ``session`` (NY, weekdays). Refuses before spending
    more than ``max_usd`` (checked on the full-range quote, an upper bound). Months already on disk are skipped."""
    total = quote(start, end, symbol)
    if total > max_usd:
        raise SystemExit(f"quote ${total:.2f} exceeds the ${max_usd:.2f} cap; nothing downloaded")
    c = client()
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for a, b in months(start, end):
        p = path_for(symbol, SCHEMA, a[:7], out)
        if not p.exists():
            spans = day_windows(date.fromisoformat(a), date.fromisoformat(b), session) if session else [(a, b)]
            parts = [_get(c, symbol, SCHEMA, x, y) for x, y in spans]
            df = pd.concat([x for x in parts if len(x)]) if any(len(x) for x in parts) else pd.DataFrame()
            tidy(df).to_parquet(p)
            print(p.name, len(df), flush=True)
        paths.append(p)
    return paths


def fetch_bars(start: date, end: date, symbol: str = SYMBOL, out: Path = OUT) -> list[Path]:
    """CME 1m OHLCV bars (built by the exchange feed from trades), all hours, monthly files."""
    c = client()
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for a, b in months(start, end):
        p = path_for(symbol, BARS, a[:7], out)
        if not p.exists():
            tidy_bars(_get(c, symbol, BARS, a, b)).to_parquet(p)
            print(p.name, flush=True)
        paths.append(p)
    return paths


def fetch_tbbo_day(day: date, symbol: str = SYMBOL, out: Path = OUT) -> Path:
    """One NY session of TBBO (trades + quote) for the aggressor-side check."""
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{symbol.split('.')[0]}-tbbo-day-{day}.parquet"
    if not p.exists():
        (a, b), = day_windows(day, day + pd.Timedelta(days=1), SESSION)
        tidy(_get(client(), symbol, "tbbo", a, b)).to_parquet(p)
    return p


# --- pure pieces (unit-tested) --------------------------------------------------------------------------

def day_windows(start: date, end: date, session: tuple[str, str] = SESSION) -> list[tuple[str, str]]:
    """One (UTC start, UTC end) ISO pair per weekday in [start, end): ``session`` in NY local time (DST-aware)."""
    out = []
    for d in pd.bdate_range(start, pd.Timestamp(end) - pd.Timedelta(days=1)):
        a, b = (pd.Timestamp(f"{d.date()} {t}", tz=NY).tz_convert("UTC").isoformat() for t in session)
        out.append((a, b))
    return out


def tidy_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Databento OHLCV frame → open/high/low/close/volume indexed by the bar's NY start minute."""
    idx = pd.to_datetime(df["ts_event"] if "ts_event" in df else df.index, utc=True)
    out = df[["open", "high", "low", "close", "volume"]].astype(float).copy()
    out.index = pd.DatetimeIndex(idx).tz_convert(NY)
    out.index.name = "ts"
    return out.sort_index()


def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Databento TBBO frame → trades indexed by NY event time, only the columns we use."""
    if df.empty:
        return pd.DataFrame(columns=KEEP, index=pd.DatetimeIndex([], tz=NY, name="ts"))
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


def load(start: date, end: date, symbol: str = SYMBOL, root: Path = OUT, schema: str = SCHEMA) -> pd.DataFrame:
    """Cached trades (or ``schema=BARS`` bars) for [start, end) (NY dates)."""
    # files are split at UTC month starts, so a NY evening at month end sits in the next month's file
    ms = [a[:7] for a, _ in months(start, end)] + [(pd.Timestamp(end) + pd.offsets.MonthBegin(0)).strftime("%Y-%m")]
    parts = [pd.read_parquet(f) for f in dict.fromkeys(path_for(symbol, schema, m, root) for m in ms) if f.exists()]
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts)
    df = df[~df.index.duplicated()].sort_index()
    lo, hi = pd.Timestamp(start, tz=NY), pd.Timestamp(end, tz=NY)
    return df[(df.index >= lo) & (df.index < hi)]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.data.orderflow")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("quote", "fetch", "bars"):
        x = sub.add_parser(name)
        x.add_argument("start", type=date.fromisoformat)
        x.add_argument("end", type=date.fromisoformat)
        x.add_argument("--symbol", default=SYMBOL)
        x.add_argument("--schema", default=SCHEMA)
        x.add_argument("--max-usd", type=float, default=125.0)
    c = sub.add_parser("sidecheck")
    c.add_argument("day", type=date.fromisoformat)
    a = ap.parse_args(argv)
    if a.cmd == "quote":
        print(f"{a.symbol} {a.schema} {a.start} → {a.end}: ${quote(a.start, a.end, a.symbol, a.schema):.2f}")
    elif a.cmd == "fetch":
        fetch(a.start, a.end, a.symbol, max_usd=a.max_usd)
    elif a.cmd == "bars":
        fetch_bars(a.start, a.end, a.symbol)
    else:
        print(side_check(pd.read_parquet(fetch_tbbo_day(a.day))))


if __name__ == "__main__":
    main()
