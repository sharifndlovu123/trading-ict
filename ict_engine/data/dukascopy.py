"""Download and load Dukascopy 1-minute bars (pipeline stage 0).

Raw CSV is fetched month by month with the pinned ``dukascopy-node`` CLI (UTC
timestamps), then cached as Parquet. ``load`` returns bars indexed by
**America/New_York** time (DST-aware) — every later stage works in NY time.

CLI:
    uv run python -m ict_engine.data.dukascopy fetch US100 2023-11-01 2024-01-31
    uv run python -m ict_engine.data.dukascopy check US100 2023-11-01 2024-01-31
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from ict_engine.data.instruments import Asset, get

NY = "America/New_York"
DUKASCOPY_NODE = "dukascopy-node@1.51.1"   # pinned
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# --- months -------------------------------------------------------------------

def months(start: date, end: date) -> list[date]:
    """First day of every month touching [start, end]."""
    m, out = start.replace(day=1), []
    while m <= end:
        out.append(m)
        m = (m.replace(day=28) + timedelta(days=4)).replace(day=1)
    return out


def _month_end(m: date) -> date:
    return (m.replace(day=28) + timedelta(days=4)).replace(day=1)


def _parquet_path(asset: Asset, m: date, price: str, root: Path) -> Path:
    return root / "bars" / asset.dukascopy_id / f"{m:%Y-%m}-{price}.parquet"


# --- download -----------------------------------------------------------------

def _download_month(asset: Asset, m: date, price: str) -> pd.DataFrame:
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "npx", "-y", DUKASCOPY_NODE,
            "-i", asset.dukascopy_id,
            "-from", m.isoformat(), "-to", _month_end(m).isoformat(),
            "-t", "m1", "-p", price, "-v", "true", "-f", "csv",
            "-r", "3", "-dir", tmp, "-s",   # no -re: weekends are legitimately empty
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            tail = (res.stdout + res.stderr).strip().splitlines()[-3:]
            raise RuntimeError(f"dukascopy-node failed for {asset.name} {m:%Y-%m}: " + " | ".join(tail))
        files = list(Path(tmp).glob("*.csv"))
        if not files:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        return parse_csv(files[0])


def parse_csv(path: str | Path) -> pd.DataFrame:
    """dukascopy-node CSV (UTC epoch ms) → DataFrame indexed by UTC timestamp."""
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df.set_index("timestamp").sort_index()


def fetch(asset_name: str, start: date, end: date, *, price: str = "bid",
          root: Path = DATA_DIR, force: bool = False) -> list[Path]:
    """Download missing months to Parquet. The current month is always re-fetched."""
    asset = get(asset_name)
    today = date.today().replace(day=1)
    written = []
    for m in months(start, end):
        path = _parquet_path(asset, m, price, root)
        if path.exists() and not force and m < today:
            continue
        df = _download_month(asset, m, price)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path)
        written.append(path)
    return written


# --- load ---------------------------------------------------------------------

def load(asset_name: str, start: date, end: date, *, price: str = "bid",
         root: Path = DATA_DIR) -> pd.DataFrame:
    """Bars for [start, end] (NY dates, inclusive), indexed by NY time."""
    asset = get(asset_name)
    parts = []
    required = months(start, end)
    # NY is behind UTC, so the last NY day spills into the next UTC day (maybe next month).
    extra = [m for m in months(end + timedelta(days=1), end + timedelta(days=1)) if m not in required]
    for m in required + extra:
        path = _parquet_path(asset, m, price, root)
        if not path.exists():
            if m in extra:
                continue
            raise FileNotFoundError(f"{path} missing — run fetch first")
        parts.append(pd.read_parquet(path))
    df = pd.concat(parts)
    df = df[~df.index.duplicated()].sort_index()
    df.index = df.index.tz_convert(NY)
    df.index.name = "ts"
    lo = pd.Timestamp(start, tz=NY)
    hi = pd.Timestamp(end + timedelta(days=1), tz=NY)
    return df[(df.index >= lo) & (df.index < hi)]


# --- quality ------------------------------------------------------------------

@dataclass
class QualityReport:
    bars: int
    duplicates: int
    bad_ohlc: int                 # high < max(open, close) or low > min(open, close)
    gaps: list[tuple[pd.Timestamp, pd.Timestamp, int]]  # (from, to, missing minutes) inside sessions

    def ok(self) -> bool:
        return self.duplicates == 0 and self.bad_ohlc == 0


def check(df: pd.DataFrame, min_gap_minutes: int = 5) -> QualityReport:
    """Flag duplicates, impossible candles, and gaps ≥ min_gap_minutes on weekdays.

    Weekend closes and the daily 17:00–18:00 futures halt are not counted as gaps.
    """
    idx = df.index
    bad = int(((df["high"] < df[["open", "close"]].max(axis=1)) |
               (df["low"] > df[["open", "close"]].min(axis=1))).sum())
    gaps = []
    deltas = idx.to_series().diff().dt.total_seconds().div(60).iloc[1:]
    for ts, minutes in deltas[deltas > min_gap_minutes].items():
        prev = ts - pd.Timedelta(minutes=minutes)
        if _expected_closure(prev, ts):
            continue
        gaps.append((prev, ts, int(minutes) - 1))
    return QualityReport(len(df), int(idx.duplicated().sum()), bad, gaps)


def _expected_closure(prev: pd.Timestamp, nxt: pd.Timestamp) -> bool:
    prev, nxt = prev.tz_convert(NY), nxt.tz_convert(NY)
    if prev.weekday() >= 4 and nxt.weekday() in (6, 0):   # Fri close → Sun/Mon open
        return True
    # daily halt around 17:00–18:00 NY
    return 16 <= prev.hour <= 17 and 17 <= nxt.hour <= 18 and (nxt - prev) <= pd.Timedelta(hours=2)


# --- CLI ----------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="ict_engine.data.dukascopy")
    p.add_argument("action", choices=["fetch", "check"])
    p.add_argument("asset", help="US100, US500, US30, XAUUSD, XAGUSD, DXY, EURUSD or 'all'")
    p.add_argument("start", type=date.fromisoformat)
    p.add_argument("end", type=date.fromisoformat)
    p.add_argument("--price", default="bid", choices=["bid", "ask"])
    a = p.parse_args(argv)

    if shutil.which("npx") is None and a.action == "fetch":
        raise SystemExit("npx not found — install Node.js")
    from ict_engine.data.instruments import ASSETS
    names = list(ASSETS) if a.asset == "all" else [a.asset]
    for name in names:
        if a.action == "fetch":
            written = fetch(name, a.start, a.end, price=a.price)
            print(f"{name}: {len(written)} month file(s) written")
        else:
            r = check(load(name, a.start, a.end, price=a.price))
            print(f"{name}: {r.bars} bars, dup={r.duplicates}, bad_ohlc={r.bad_ohlc}, gaps={len(r.gaps)}")
            for g in r.gaps[:10]:
                print(f"   gap {g[0]:%Y-%m-%d %H:%M} → {g[1]:%H:%M} ({g[2]} min)")


if __name__ == "__main__":
    main()
