"""Higher-timeframe draw after a BOS (ict_engine.concepts.htf_draw) and the OB's dealing-range place + higher-TF draw
(ict_engine.concepts.ob_context). Sharif 2026-11-16 (gold): the monthly FVG became the target only because the
monthly BOS left equal lows — "once that happened we were interested in lower levels"; the daily OB after the equal-highs
sweep was the entry. Hand-built bars with known answers + his gold sell on real data, with no look-ahead."""
from datetime import date

import pandas as pd
import pytest

from ict_engine.concepts.htf_draw import bos_draw
from ict_engine.concepts.ob_context import ob_reads, period_bars

NY = "America/New_York"
#        open high low close
ROWS = [(30, 40, 25, 38),      # 0
        (38, 55, 37, 54),      # 1
        (54, 70, 50, 68),      # 2  bull FVG 40–50 (bar0 high 40 → bar2 low 50)
        (68, 100, 66, 98),     # 3
        (100, 120, 98, 115),   # 4
        (115, 125, 80, 85),    # 5  swing low 80 (98 > 80 < 84)
        (85, 110, 84, 105),    # 6
        (105, 108, 70, 72),    # 7  closes 72 < 80 → BOS down
        (72, 90, 60, 88),      # 8  low 60
        (88, 95, 61, 90),      # 9  low 61 ≈ 60 → equal lows (tol ≈ 3)
        (90, 92, 75, 80),      # 10
        (80, 82, 55, 58)]      # 11 takes the equal lows, closes 58 < 60: delivery, not a new BOS


def bars(rows):
    idx = pd.date_range("2025-01-01", periods=len(rows), freq="MS", tz=NY)
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    df["close_ts"] = idx + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=16)
    return df


def test_bos_then_equal_lows_then_the_fvg_beyond():
    b = bars(ROWS[:11])
    r = bos_draw(b, "1M", b.close_ts.iloc[-1])
    assert r["bos"]["direction"] == "bear" and r["bos"]["level"] == 80 and r["bos"]["candle"] == b.index[7]
    assert r["equal"]["prices"] == [60, 61] and r["equal"]["level"] == 60 and r["equal"]["taken"] is None
    assert r["draw"]["fvg"] == (40, 50) and r["draw"]["edge"] == 50 and not r["draw"]["reached"]


def test_taking_the_equal_lows_is_delivery_not_a_new_break():
    b = bars(ROWS)
    r = bos_draw(b, "1M", b.close_ts.iloc[-1])
    assert r["bos"]["candle"] == b.index[7]                       # still the June-style BOS, not bar 11
    assert r["equal"]["taken"] == {"candle": b.index[11], "extreme": 55}
    assert r["draw"]["fvg"] == (40, 50)                           # the draw beyond is unchanged


def test_no_look_ahead_the_bos_exists_only_after_its_close():
    b = bars(ROWS)
    assert bos_draw(b, "1M", b.close_ts.iloc[7] - pd.Timedelta(minutes=1)) is None
    assert bos_draw(b, "1M", b.close_ts.iloc[7])["bos"]["candle"] == b.index[7]


def test_a_wick_through_is_not_a_break():
    rows = ROWS[:7] + [(105, 108, 70, 82)]                        # wick to 70, close 82 above the swing low 80
    b = bars(rows)
    assert bos_draw(b, "1M", b.close_ts.iloc[-1]) is None


def test_ob_place_is_premium_of_the_dealing_range_bible():
    # Bible pp.27–29: sellstops run to a new low (80 < 90), then buystops run to a new high (the OB candle, 118 > 115)
    rows = [(100, 110, 95, 105),
            (105, 108, 90, 92),     # 1 swing low 90
            (92, 115, 93, 112),     # 2 swing high 115
            (112, 113, 80, 82),     # 3 swing low 80: ran the sellstops under 90
            (82, 100, 84, 98),
            (98, 118, 96, 116),     # 5 the OB candle (last up-close): runs the buystops above 115, body 98–116
            (116, 117, 88, 90)]     # 6 closes 90 < its low 96 → a valid bearish OB (Bible p.16 step 3)
    b = bars(rows)
    r = [x for x in ob_reads(b, "1M", b.close_ts.iloc[-1]) if x["direction"] == "bear"][-1]
    assert r["candle"] == b.index[5] and r["known"] == b.close_ts.iloc[6] and r["validation"] == "closed beyond its low"
    assert r["place"]["basis"] == "dealing range" and r["place"]["range"] == (80, 118)
    assert r["place"]["fraction"] == pytest.approx((107 - 80) / 38, abs=0.01) and r["place"]["fits"]
    assert r["event"]["what"] == "swing high" and r["event"]["price"] == 115


def test_ob_validation_stages_ruling_23():
    base = [(100, 110, 95, 105), (105, 108, 90, 92), (92, 115, 93, 112), (112, 113, 80, 82), (82, 100, 84, 98),
            (98, 118, 96, 116)]                                   # bar 5: the up-close OB candle, open 98, low 96
    def at(last):
        b = bars(base + [last])
        r = [x for x in ob_reads(b, "1M", b.close_ts.iloc[-1]) if x["candle"] == b.index[5]]
        return r[0]["validation"] if r else None
    assert at((116, 117, 99, 99.5)) is None                       # open 98 not crossed by a close: no OB yet
    assert at((116, 117, 97, 97.5)) == "open crossed only"         # ICT 2023: the change in the state of delivery
    assert at((116, 117, 95, 97.5)) == "traded through its low"    # ICT Core Content: trades through (wick)
    assert at((116, 117, 88, 90)) == "closed beyond its low"       # ICT Bible: close below its low


@pytest.fixture(scope="module")
def gold():
    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.context import completed_daily
    from ict_engine.data import dukascopy
    try:
        b = dukascopy.load("XAUUSD", date(2024, 1, 1), date(2026, 11, 16))
    except Exception:
        pytest.skip("XAUUSD data to 2026-11 not fetched")
    if b.index.max() < pd.Timestamp("2026-11-13", tz=NY):
        pytest.skip("XAUUSD data to 2026-11 not fetched")

    def at(t):
        a = pd.Timestamp(t, tz=NY)
        past = b[b.index < a]
        d = completed_daily(resample(past, "1d"), a.date())
        return d, period_bars(d, "M", a), period_bars(d, "W", a), resample(past, "1h"), a
    return at


def test_regression_sharif_gold_monthly_chain(gold):
    d, m, w, h, a = gold("2026-11-11 01:00")                      # before his fill (11 Nov 02:25)
    r = bos_draw(m, "1M", a)
    assert r["bos"]["direction"] == "bear" and r["bos"]["candle"].month == 6        # June closed below the March low
    assert r["bos"]["level"] == pytest.approx(4098.3, abs=1)
    assert r["equal"]["prices"] == pytest.approx([3928.5, 3941.5, 3959.5], abs=1)  # Nov 2025, Jun, Jul 2026
    assert r["equal"]["taken"]["candle"].month == 10                               # October took them
    assert r["draw"]["fvg"] == pytest.approx((3453.6, 3819.1), abs=1) and not r["draw"]["reached"]
    _, m0, _, _, a0 = gold("2026-06-29 12:00")                    # June not closed yet → no June BOS
    r0 = bos_draw(m0, "1M", a0)
    assert r0 is None or r0["bos"]["candle"].month != 6


def test_regression_sharif_gold_daily_ob_entry(gold):
    d, m, w, h, a = gold("2026-11-11 01:00")
    r = [x for x in ob_reads(d, "1d", a, last=2, fine=h, htf=[(m, "1M"), (w, "1w")]) if x["direction"] == "bear"][-1]
    assert r["body"] == pytest.approx((4064.9, 4140.1), abs=1)      # his entry 4,066.27 at the body's low
    assert r["event"]["what"] == "equal highs" and r["event"]["extreme"] == pytest.approx(4148.6, abs=1)
    assert r["place"]["basis"] == "dealing range" and r["place"]["fits"]           # premium of the leg
    assert r["place"]["lookback"]["fraction"] < 0.5                                # the 40-day window said discount
    assert r["draw"]["tf"] == "1M" and r["draw"]["fvg"] == pytest.approx((3453.6, 3819.1), abs=1)  # his target's FVG
    d0, *_, h0, a0 = gold("2026-11-10 12:00")                     # before the engulfing close: no such OB yet
    assert not [x for x in ob_reads(d0, "1d", a0, last=3, fine=h0) if x["direction"] == "bear"
                and x["body"][0] == pytest.approx(4064.9, abs=1)]


def test_regression_gold_daily_ob_strength(gold):
    d, m, w, h, a = gold("2026-11-11 01:00")
    r = [x for x in ob_reads(d, "1d", a, last=2, fine=h, htf=[(m, "1M"), (w, "1w")]) if x["direction"] == "bear"][-1]
    assert r["strength"]["ok"] and r["strength"]["push_mean"] == pytest.approx(2.11, abs=0.05)
