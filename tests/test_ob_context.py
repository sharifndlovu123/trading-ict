"""Order blocks in their place (ict_engine.concepts.ob_context; ruling §22): single-candle OB, the transitional event
(liquidity traded to / inefficiency revisited), premium-discount place, and the draw = the remaining FVG on the retrace
side with the liquidity at its edge and how price behaves in it. Hand-built bars with known answers + Sharif's US100
monthly case (Sep 2026 OB) on real data."""
from datetime import date

import pandas as pd
import pytest

from ict_engine.concepts.events import order_blocks
from ict_engine.concepts.ob_context import ob_reads, period_bars

NY = "America/New_York"
# bar: (open, high, low, close)
BASE = [(50, 60, 45, 58),      # 0
        (58, 75, 57, 74),      # 1  bull FVG 60–73 (bar0 high → bar2 low), formed at bar1
        (74, 90, 73, 89),      # 2
        (89, 100, 85, 92),     # 3  swing high 100 (90 < 100 > 95)
        (92, 95, 80, 84),      # 4  swing low 80 (85 > 80 < 83)
        (84, 99.5, 83, 97),    # 5  the OB candle: last up-close, its high 99.5 ≈ 100 → equal highs
        (97, 106, 81, 82),     # 6  runs 100 → 106, closes 82 < 84 (the OB's open) → bearish OB known here
        (82, 85, 74, 76)]      # 7  heading down, not yet into the FVG (top 73)


def bars(rows):
    idx = pd.date_range("2025-01-01", periods=len(rows), freq="MS", tz=NY)
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    df["close_ts"] = idx + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=16)
    return df


def ob5(df, as_of):
    return next(r for r in ob_reads(df, "1M", as_of, last=5) if r["candle"] == df.index[5])


def test_single_candle_ob_is_only_the_last_up_close_candle():
    df = bars(BASE)
    run = [e for e in order_blocks(df, "1M", confirm="open") if e.origin_ts == df.index[5]]
    one = [e for e in order_blocks(df, "1M", confirm="open", single=True) if e.origin_ts == df.index[5]]
    assert one and one[0].meta["body"] == (97.0, 84.0) and one[0].ts == df.close_ts.iloc[6]
    assert run and run[0].meta["candles"] == 1          # bar 4 is down-close: the run is bar 5 alone here too


def test_event_place_and_draw():
    df = bars(BASE)
    r = ob5(df, df.close_ts.iloc[7])
    assert r["direction"] == "bear" and r["body"] == (84.0, 97.0) and r["mt"] == 90.5
    assert r["event"] == {"kind": "liquidity", "what": "equal highs", "price": 100.0, "extreme": 106.0}
    assert r["place"]["zone"] == "premium" and r["place"]["fits"] and r["place"]["fraction"] == 0.75
    d = r["draw"]
    assert d["fvg"] == (60.0, 73.0) and d["ce"] == 66.5 and d["liquidity"] == 80.0
    assert d["state"] == "not reached yet"


def test_reaction_in_the_fvg_decides():
    held = bars(BASE + [(76, 77, 66, 70)])              # wick past CE 66.5, body stays above it
    assert ob5(held, held.close_ts.iloc[8])["draw"]["state"].startswith("reached and respected")
    weak = bars(BASE + [(76, 77, 62, 64)])              # a body below the midpoint
    assert ob5(weak, weak.close_ts.iloc[8])["draw"]["state"].startswith("inside, a body past its midpoint")
    gone = bars(BASE + [(76, 77, 55, 58)])              # closes below 60 → IFVG
    assert ob5(gone, gone.close_ts.iloc[8])["draw"]["state"].startswith("closed through")


def test_no_look_ahead_the_ob_exists_only_after_the_engulfing_close():
    df = bars(BASE)
    before = df.close_ts.iloc[6] - pd.Timedelta(minutes=1)
    assert not [r for r in ob_reads(df, "1M", before, last=5) if r["candle"] == df.index[5]]
    assert ob5(df, df.close_ts.iloc[6])["known"] == df.close_ts.iloc[6]


def test_an_ob_without_an_event_in_discount_is_just_a_candle():
    rows = [(100, 101, 90, 92), (92, 93, 80, 81), (81, 82, 70, 71), (71, 75, 69, 74), (74, 74.5, 60, 62)]
    df = bars(rows)                                     # bar 3 up-close in a falling market, bar 4 closes < 71
    r = next(r for r in ob_reads(df, "1M", df.close_ts.iloc[4]) if r["candle"] == df.index[3])
    assert r["event"] is None and r["place"]["zone"] == "discount" and not r["place"]["fits"]


def test_period_bars_group_by_trading_day_and_drop_the_open_period():
    starts = pd.DatetimeIndex(["2026-08-27 18:00", "2026-08-30 18:00", "2026-08-31 18:00", "2026-10-01 18:00"], tz=NY)
    d = pd.DataFrame({"open": [1, 2, 3, 4], "high": [5, 6, 7, 8], "low": [0, 1, 2, 3], "close": [2, 3, 4, 5]},
                     index=starts, dtype=float)
    d["close_ts"] = starts + pd.Timedelta(hours=22, minutes=14)   # next day 16:14
    m = period_bars(d, "M", pd.Timestamp("2026-10-05 10:00", tz=NY))
    assert list(m.index.month) == [8, 9]                # the 31 Aug 18:00 session is 1 Sep; October is unfinished
    assert m.loc[m.index[0], "close"] == 3.0 and m.loc[m.index[1], "open"] == 3.0


@pytest.fixture(scope="module")
def us100_daily():
    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.context import completed_daily
    from ict_engine.data import dukascopy
    at = pd.Timestamp("2026-11-15 18:00", tz=NY)
    try:
        b = dukascopy.load("US100", date(2024, 1, 1), date(2026, 11, 16))
    except Exception:
        pytest.skip("US100 data to 2026-11 not fetched")
    if b.index.max() < pd.Timestamp("2026-11-13", tz=NY):
        pytest.skip("US100 data to 2026-11 not fetched")
    return completed_daily(resample(b[b.index < at], "1d"), at.date()), at


def test_regression_sharif_us100_monthly_september_ob(us100_daily):
    d, at = us100_daily
    m = period_bars(d, "M", at)
    r = [x for x in ob_reads(m, "1M", at, fine=d) if x["direction"] == "bear"][-1]
    assert r["candle"].month == 9 and r["candle"].year == 2026
    assert r["body"] == pytest.approx((29465, 30443), abs=5)
    assert r["known"].month == 10                                         # at October's close, not before
    assert r["event"]["what"] == "equal highs" and r["event"]["price"] == pytest.approx(30760, abs=5)
    assert r["event"]["extreme"] == pytest.approx(31365, abs=5)
    assert r["place"]["zone"] == "premium" and r["place"]["fits"]
    assert r["draw"]["fvg"] == pytest.approx((25208, 27408), abs=5)       # the remaining April FVG
    assert r["draw"]["liquidity"] == pytest.approx(27063, abs=5)          # July-low sellside on its edge
    assert "past its midpoint" in r["draw"]["state"]                      # November: 26,265, CE 26,308
    assert r["state"] == "holding"                                        # no monthly close above its MT 29,954
    jul = [x for x in ob_reads(m, "1M", at, fine=d) if x["direction"] == "bull" and x["candle"].month == 7][-1]
    assert jul["state"].startswith("failed") and not jul["place"]["fits"]   # Oct closed 28,420 < MT 29,253; premium
    early = period_bars(d[d.close_ts < pd.Timestamp("2026-10-30", tz=NY)], "M", pd.Timestamp("2026-10-30", tz=NY))
    assert not [x for x in ob_reads(early, "1M", pd.Timestamp("2026-10-30", tz=NY))
                if x["direction"] == "bear" and x["candle"].month == 9]  # no look-ahead


def test_ob_state_holding_failed_on_a_close_through_mt_and_traded_through():
    df = bars(BASE)                                       # bearish OB body 84–97 (MT 90.5), confirmed at bar 6
    assert ob5(df, df.close_ts.iloc[7])["state"] == "holding"
    up = bars(BASE + [(76, 96, 75, 92)])                  # closes 92 > MT 90.5 (wick 96 inside the body)
    assert ob5(up, up.close_ts.iloc[8])["state"] == "failed: a close through its MT"
    wick = bars(BASE + [(76, 99, 75, 80)])                # wick 99 > body top 97, close 80 below MT
    assert ob5(wick, wick.close_ts.iloc[8])["state"] == "body traded through (no close past MT)"
    both = bars(BASE + [(76, 99, 75, 95)])
    assert ob5(both, both.close_ts.iloc[8])["state"].startswith("failed: closed through its MT, then")
    assert ob5(both, both.close_ts.iloc[7])["state"] == "holding"          # no look-ahead


def test_strength_body_and_aggressive_push_sharif():
    from ict_engine.concepts.ob_context import _strength
    from ict_engine.concepts.events import Event
    idx = pd.date_range("2025-01-01", periods=17, freq="D", tz=NY)
    rows = [(100, 106, 99, 104)] * 14 + [(104, 110, 103, 109),   # 14: up-close, body 5 = range 7 × 0.71, 1.25× mean 4
                                         (109, 110, 99, 100),     # 15: push down, body 9 = 2.25× mean
                                         (100, 101, 97, 98)]
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    ob = Event("ob", "1d", "bear", idx[15], idx[14], 110.0, 103.0, {"body": (109.0, 104.0)})
    s = _strength(df, ob)
    assert s["body_range"] == pytest.approx(0.71, abs=0.01) and s["body_mean"] == 1.25 and s["push_mean"] == 2.25
    assert s["ok"]
    weak = df.copy(); weak.iloc[14] = (104, 110, 98, 105)       # body 1 of range 12: a weak body
    assert not _strength(weak, ob)["strong_body"]
    slow = df.copy(); slow.iloc[15] = (109, 110, 105, 106)      # next candle body 3 = 0.75×: no aggressive push
    s2 = _strength(slow, ob)
    assert s2["strong_body"] and not s2["aggressive_push"] and not s2["ok"]
    assert _strength(df.iloc[:15], ob)["push_mean"] is None    # push candle not there yet: no look-ahead


def test_regression_strength_sharif_us100_sep_ob_and_july_candle(us100_daily):
    d, at = us100_daily
    m = period_bars(d, "M", at)
    reads = ob_reads(m, "1M", at, last=4, fine=d)
    sep = [x for x in reads if x["direction"] == "bear" and x["candle"].month == 9][-1]
    assert sep["strength"]["ok"]                                   # body 0.48 / 0.91, push 1.88 (October)
    jul = [x for x in reads if x["direction"] == "bull" and x["candle"].month == 7][-1]
    assert jul["strength"]["strong_body"] and not jul["strength"]["aggressive_push"]   # August: 0.92×, no push
