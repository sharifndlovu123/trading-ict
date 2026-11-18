"""Fetch 1-minute candles (free Dukascopy data) into `data/bars/`, one file per month, for the v2 chart.

    uv run python v2/chart/fetch.py UK100            # this month
    uv run python v2/chart/fetch.py UK100 DE40 --months 2

Needs Node.js (`npx`). Plumbing only: it downloads candles and writes them; it knows nothing about trading.
"""
from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from candles import DATA, FOLDERS

TOOL = "dukascopy-node@1.51.1"      # pinned


def parse_csv(text: str) -> pd.DataFrame:
    """The downloader's CSV (timestamp in epoch milliseconds, UTC) into candles indexed by UTC time."""
    df = pd.read_csv(io.StringIO(text))
    if df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df.pop("timestamp"), unit="ms", utc=True).rename("timestamp")
    return df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()


def month_starts(today: date, months: int) -> list[date]:
    out, m = [], today.replace(day=1)
    for _ in range(months):
        out.append(m)
        m = (m - timedelta(days=1)).replace(day=1)
    return sorted(out)


def fetch_month(asset: str, start: date, root: Path = DATA) -> int:
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)          # the first of the next month
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["npx", "-y", TOOL, "-i", FOLDERS[asset], "-from", start.isoformat(), "-to", end.isoformat(),
               "-t", "m1", "-p", "bid", "-v", "true", "-f", "csv", "-r", "3", "-dir", tmp, "-s"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"download failed for {asset} {start:%Y-%m}: " + " | ".join((res.stdout + res.stderr).strip().splitlines()[-3:]))
        files = list(Path(tmp).glob("*.csv"))
        df = parse_csv(files[0].read_text()) if files else parse_csv("timestamp,open,high,low,close,volume\n")
    if df.empty:
        return 0
    out = root / FOLDERS[asset] / f"{start:%Y-%m}-bid.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out)
    return len(df)


def fetch_recent(asset: str, days: int = 3, today: date | None = None, timeout: int = 120) -> pd.DataFrame:
    """The last few days of 1-minute candles, up to about a minute ago (the free feed's delay). For the live chart."""
    today = today or date.today()
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["npx", "-y", TOOL, "-i", FOLDERS[asset], "-from", (today - timedelta(days=days)).isoformat(), "-to", (today + timedelta(days=2)).isoformat(),
               "-t", "m1", "-p", "bid", "-v", "true", "-f", "csv", "-r", "2", "-dir", tmp, "-s"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if res.returncode != 0:
            raise RuntimeError(f"live download failed for {asset}: " + " | ".join((res.stdout + res.stderr).strip().splitlines()[-2:]))
        files = list(Path(tmp).glob("*.csv"))
        return parse_csv(files[0].read_text()) if files else parse_csv("timestamp,open,high,low,close,volume\n")


def merge_files(asset: str, fresh: pd.DataFrame, root: Path = DATA) -> int:
    """Fold freshly downloaded candles into the monthly files: new minutes are added, minutes already there are replaced
    by the fresh ones (the newest minute may have been unfinished last time). Returns how many minutes are new."""
    added = 0
    if fresh.empty:
        return added
    for month, part in fresh.groupby(fresh.index.strftime("%Y-%m")):
        out = root / FOLDERS[asset] / f"{month}-bid.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        old = pd.read_parquet(out) if out.exists() else part.iloc[0:0]
        both = pd.concat([old, part])
        both = both[~both.index.duplicated(keep="last")].sort_index()
        if len(both) == len(old) and old.tail(len(part)).equals(both.tail(len(part))):
            continue                                            # nothing changed: leave the file (and what was read from it) alone
        added += len(both) - len(old)
        tmp = out.with_suffix(".tmp")
        both.to_parquet(tmp)
        tmp.replace(out)
    return added


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("assets", nargs="+", choices=sorted(FOLDERS))
    ap.add_argument("--months", type=int, default=1, help="how many months back from this one (default 1 = this month)")
    a = ap.parse_args()
    if shutil.which("npx") is None:
        raise SystemExit("npx not found: install Node.js")
    for asset in a.assets:
        for m in month_starts(date.today(), a.months):
            print(f"{asset} {m:%Y-%m}: {fetch_month(asset, m)} candles", flush=True)


if __name__ == "__main__":
    main()
