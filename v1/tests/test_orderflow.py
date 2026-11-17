"""Order-flow loader pieces on hand-built trades (no network, no key)."""

from datetime import date

import pandas as pd
import pytest

from ict_engine.data import orderflow as of

NY = "America/New_York"


def trades():
    # 10:00:10 buy 2 @100 (at ask), 10:00:40 sell 1 @99.75 (at bid), 10:01:05 buy 3 @100.25, 10:01:30 unknown 5
    ts = pd.to_datetime(["2024-01-09 15:00:10", "2024-01-09 15:00:40", "2024-01-09 15:01:05", "2024-01-09 15:01:30"],
                        utc=True)
    raw = pd.DataFrame({"ts_event": ts, "price": [100.0, 99.75, 100.25, 100.0], "size": [2, 1, 3, 5],
                        "side": ["B", "A", "B", "N"], "bid_px_00": [99.75, 99.75, 100.0, 99.75],
                        "ask_px_00": [100.0, 100.0, 100.25, 100.0], "bid_sz_00": 1, "ask_sz_00": 1,
                        "action": "T"})
    return of.tidy(raw)


def test_tidy_indexes_by_ny_event_time_and_keeps_only_used_columns():
    t = trades()
    assert str(t.index.tz) == NY and t.index[0] == pd.Timestamp("2024-01-09 10:00:10", tz=NY)
    assert "action" not in t and list(t.columns) == of.KEEP


def test_signed_volume_b_is_buy_aggressor_and_n_is_zero():
    assert list(of.signed(trades())) == [2, -1, 3, 0]


def test_bars_1m_ohlc_volume_and_delta():
    b = of.bars_1m(trades())
    first, second = b.iloc[0], b.iloc[1]
    assert b.index[0] == pd.Timestamp("2024-01-09 10:00", tz=NY)
    assert (first.open, first.high, first.low, first.close, first.volume) == (100.0, 100.0, 99.75, 99.75, 3)
    assert (first.buy, first.sell, first.delta) == (2, 1, 1)
    assert (second.volume, second.buy, second.sell, second.delta) == (8, 3, 0, 3)


def test_imbalance_is_aligned_and_uses_only_bars_up_to_end():
    b = of.bars_1m(trades())
    end = pd.Timestamp("2024-01-09 10:00", tz=NY)
    assert of.imbalance(b, end, 5, "long") == pytest.approx(1 / 3)          # only the 10:00 bar
    assert of.imbalance(b, end, 5, "short") == pytest.approx(-1 / 3)
    assert of.imbalance(b, end + pd.Timedelta(minutes=1), 5, "long") == pytest.approx(4 / 6)
    assert pd.isna(of.imbalance(b, end - pd.Timedelta(minutes=10), 5))


def test_side_check_buy_aggressors_print_at_the_ask():
    r = of.side_check(trades())
    assert r["B"]["at_ask"] == 1.0 and r["A"]["at_bid"] == 1.0


def test_months_split_and_key_never_from_nowhere(tmp_path, monkeypatch):
    assert of.months(date(2024, 1, 15), date(2024, 3, 1)) == [("2024-01-15", "2024-02-01"), ("2024-02-01", "2024-03-01")]
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        of.api_key(tmp_path / ".env")
    (tmp_path / ".env").write_text("OTHER=1\nDATABENTO_API_KEY='abc'\n")
    assert of.api_key(tmp_path / ".env") == "abc"


def test_day_windows_are_weekdays_in_ny_time_across_dst():
    w = of.day_windows(date(2024, 3, 8), date(2024, 3, 12), ("01:30", "16:30"))   # Fri, (weekend), Mon after DST
    assert len(w) == 2
    assert w[0] == ("2024-03-08T06:30:00+00:00", "2024-03-08T21:30:00+00:00")          # EST = UTC−5
    assert w[1] == ("2024-03-11T05:30:00+00:00", "2024-03-11T20:30:00+00:00")          # EDT = UTC−4


def test_tidy_bars_and_empty_tidy():
    raw = pd.DataFrame({"ts_event": pd.to_datetime(["2024-01-09 15:00"], utc=True), "open": [1], "high": [2],
                        "low": [0.5], "close": [1.5], "volume": [10], "rtype": 33})
    b = of.tidy_bars(raw)
    assert b.index[0] == pd.Timestamp("2024-01-09 10:00", tz=NY) and list(b.columns) == ["open", "high", "low", "close", "volume"]
    e = of.tidy(pd.DataFrame())
    assert e.empty and list(e.columns) == of.KEEP


def test_load_reads_the_next_month_file_for_month_end_evenings(tmp_path):
    idx = pd.to_datetime(["2024-01-31 15:00", "2024-01-31 19:30", "2024-02-01 10:00"]).tz_localize(NY)
    bars = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}, index=idx)
    bars.iloc[:1].to_parquet(of.path_for("NQ.v.0", of.BARS, "2024-01", tmp_path))
    bars.iloc[1:].to_parquet(of.path_for("NQ.v.0", of.BARS, "2024-02", tmp_path))       # 19:30 NY = Feb UTC
    got = of.load(date(2024, 1, 1), date(2024, 2, 1), root=tmp_path, schema=of.BARS)
    assert list(got.index) == list(idx[:2])
    assert of.load(date(2023, 1, 1), date(2023, 2, 1), root=tmp_path).empty


def test_nqcme_is_a_cme_asset_and_nq_root_still_means_us100():
    from ict_engine.data.instruments import get, futures_cost
    assert get("NQCME").source == "cme" and get("NQ").name == "US100"
    assert futures_cost("NQCME") == futures_cost("US100")
