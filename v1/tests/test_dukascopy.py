"""Data layer tests — no network: a tiny CSV in dukascopy-node's format."""

from datetime import date

import pandas as pd

from ict_engine.data import dukascopy as dk
from ict_engine.data.instruments import get

CSV = """timestamp,open,high,low,close,volume
1700487180000,15800.0,15802.0,15799.0,15801.0,0.1
1700487240000,15801.0,15803.0,15800.0,15802.0,0.1
1700487600000,15802.0,15801.0,15800.0,15802.5,0.1
"""
# 1700487180000 = 2023-11-20 13:33 UTC = 08:33 NY. Third bar is 6 minutes later and
# has high < close (bad OHLC).


def _write(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text(CSV)
    return p


def test_parse_csv_is_utc(tmp_path):
    df = dk.parse_csv(_write(tmp_path))
    assert str(df.index.tz) == "UTC" and df.index[0].hour == 13


def test_load_converts_to_new_york(tmp_path):
    df = dk.parse_csv(_write(tmp_path))
    asset = get("NQ")
    for m in dk.months(date(2023, 10, 31), date(2023, 12, 1)):
        path = dk._parquet_path(asset, m, "bid", tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        (df if m.month == 11 else df.iloc[0:0]).to_parquet(path)
    bars = dk.load("US100", date(2023, 11, 20), date(2023, 11, 20), root=tmp_path)
    assert "New_York" in str(bars.index.tz)
    assert bars.index[0].strftime("%H:%M") == "08:33"


def test_quality_check_flags_gap_and_bad_candle(tmp_path):
    df = dk.parse_csv(_write(tmp_path))
    r = dk.check(df.tz_convert("America/New_York"))
    assert r.bad_ohlc == 1 and r.duplicates == 0
    assert len(r.gaps) == 1 and r.gaps[0][2] == 5


def test_weekend_is_not_a_gap():
    idx = pd.DatetimeIndex([pd.Timestamp("2023-11-17 16:59", tz="America/New_York"),
                            pd.Timestamp("2023-11-19 18:00", tz="America/New_York")])
    df = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0}, index=idx)
    assert dk.check(df).gaps == []


def test_months_cover_range():
    assert dk.months(date(2023, 11, 20), date(2024, 1, 10)) == [
        date(2023, 11, 1), date(2023, 12, 1), date(2024, 1, 1)]


def test_asset_lookup_by_name_or_futures_root():
    assert get("NQ").dukascopy_id == "usatechidxusd"
    assert get("us500").futures_root == "ES"
