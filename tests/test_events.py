"""Event detectors on hand-built candles where the right answer is known."""

import pandas as pd
import pytest

from ict_engine.concepts.events import (
    Event, Level, displacement_mask, fvgs, gap_lifecycle, inversions, structure, sweeps,
    swings, volume_imbalances,
)

NY = "America/New_York"


def candles(rows, start="2024-01-09 10:00"):
    """rows: list of (open, high, low, close) as 1m bars."""
    idx = pd.date_range(start, periods=len(rows), freq="1min", tz=NY)
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    df["close_ts"] = df.index
    return df


def t(minute, start="2024-01-09 10:00"):
    return pd.Timestamp(start, tz=NY) + pd.Timedelta(minutes=minute)


# --- swings ---------------------------------------------------------------------

def test_swing_high_and_low_with_confirmation_time():
    df = candles([(10, 11, 9, 10), (10, 13, 9, 12), (12, 12, 8, 9), (9, 10, 7, 8), (8, 11, 8, 10)])
    ev = swings(df, "1m", strength=1)
    hi = [e for e in ev if e.kind == "swing_high"]
    lo = [e for e in ev if e.kind == "swing_low"]
    assert [(e.origin_ts, e.top, e.ts) for e in hi] == [(t(1), 13, t(2))]   # known one bar later
    assert [(e.origin_ts, e.bottom, e.ts) for e in lo] == [(t(3), 7, t(4))]


def test_equal_highs_are_not_swings():
    df = candles([(10, 11, 9, 10), (10, 13, 9, 12), (12, 13, 9, 11), (11, 12, 9, 10)])
    assert [e for e in swings(df, "1m") if e.kind == "swing_high"] == []


def test_swing_needs_strength_bars_each_side():
    df = candles([(10, 11, 9, 10), (10, 12, 9, 11), (11, 15, 9, 14), (14, 14, 9, 10), (10, 13, 9, 11)])
    assert any(e.kind == "swing_high" for e in swings(df, "1m", strength=1))
    assert [e.top for e in swings(df, "1m", strength=2) if e.kind == "swing_high"] == [15]


# --- displacement / FVG ----------------------------------------------------------

def _quiet(n, price=100.0):
    return [(price, price + 0.6, price - 0.6, price + 0.2)] * n   # small bodies (0.2)


def test_displacement_needs_big_body_vs_recent_average():
    rows = _quiet(20) + [(100, 104.1, 99.9, 104)]   # body 4 vs avg 0.2, body/range 0.95
    assert displacement_mask(candles(rows), k=1.5, lookback=20)[-1]
    rows = _quiet(20) + [(100, 104, 96, 100.5)]       # big range, small body → not displacement
    assert not displacement_mask(candles(rows), k=1.5, lookback=20)[-1]


def test_bullish_fvg_zone_ce_and_displacement_flag():
    rows = _quiet(20) + [(100, 100.6, 99.5, 100.2), (100.2, 104.1, 100.1, 104), (104, 105, 102, 104.5)]
    gaps = [g for g in fvgs(candles(rows), "1m") if g.direction == "bull"]
    assert len(gaps) == 1
    g = gaps[0]
    assert (g.bottom, g.top, g.ce) == (100.6, 102, 101.3)
    assert g.origin_ts == t(21) and g.ts == t(22)       # middle candle; known when candle 3 closes
    assert g.meta["displacement"] is True


def test_bearish_fvg_and_min_size():
    rows = [(110, 110.5, 108, 108.5), (108.5, 108.6, 104, 104.2), (104.2, 106, 103, 103.5)]
    g = [x for x in fvgs(candles(rows), "1m") if x.direction == "bear"]
    assert len(g) == 1 and (g[0].top, g[0].bottom) == (108, 106)
    assert fvgs(candles(rows), "1m", min_size=5) == []


def test_volume_imbalance_bodies_gap_wicks_overlap():
    rows = [(100, 101.5, 99.5, 101), (101.5, 103, 100.8, 102.5)]   # body gap 101→101.5, wicks overlap
    vi = volume_imbalances(candles(rows), "1m")
    assert len(vi) == 1 and vi[0].direction == "bull" and (vi[0].bottom, vi[0].top) == (101, 101.5)


# --- gap lifecycle (framework §9) -------------------------------------------------

def _bull_gap():
    return Event("fvg", "1m", "bull", t(2), t(1), top=102.0, bottom=100.0)


def test_lifecycle_touch_ce_fill_then_inversion():
    bars = candles([
        (103, 103.5, 102.5, 103),   # 10:00 (before gap known → ignored)
        (103, 104, 103, 103.5),     # 10:01
        (103.5, 104, 103, 103.5),   # 10:02 gap known at 10:02 → scan starts 10:03
        (103.5, 103.6, 101.8, 102.5),  # 10:03 touch
        (102.5, 102.6, 100.9, 101.5),  # 10:04 reaches CE (101), body closes 101.5 > CE
        (101.5, 101.6, 99.8, 100.2),   # 10:05 trades through 100 (filled) but body closes 100.2 above far edge
        (100.2, 100.3, 98.5, 99.0),    # 10:06 body closes below 100 → inverted
    ])
    st = gap_lifecycle(_bull_gap(), bars)
    assert (st.touched, st.ce, st.filled, st.inverted) == (t(3), t(4), t(5), t(6))
    assert st.body_beyond_ce == t(5)
    assert st.valid_at(t(5)) and not st.valid_at(t(6))


def test_wick_only_does_not_invert():
    bars = candles([(103, 103, 103, 103)] * 3 + [(103, 103, 99, 101)])   # wick to 99, close 101
    st = gap_lifecycle(_bull_gap(), bars)
    assert st.filled == t(3) and st.inverted is None and st.valid_at(t(3))


def test_inversion_creates_opposite_ifvg():
    bars = candles([(103, 103, 103, 103)] * 3 + [(101, 101, 98, 98.5)])
    (ifvg,) = inversions([_bull_gap()], bars)
    assert ifvg.kind == "ifvg" and ifvg.direction == "bear" and ifvg.ts == t(3)


def test_vi_retires_instead_of_inverting():
    vi = Event("vi", "1m", "bull", t(2), t(1), top=101.5, bottom=101.0)
    bars = candles([(103, 103, 103, 103)] * 3 + [(102, 102, 100, 100.5)])
    st = gap_lifecycle(vi, bars)
    assert st.retired == t(3) and st.inverted is None and not st.valid_at(t(3))


# --- sweeps -----------------------------------------------------------------------

def test_sweep_of_low_closes_back_inside():
    bars = candles([(101, 102, 100.5, 101.5), (101.5, 101.6, 99.0, 100.8), (100.8, 102, 100.6, 101.8)])
    (ev,) = sweeps(bars, [Level("asia_low", 100.0, "low", t(0))])
    assert ev.kind == "sweep" and ev.direction == "bull" and ev.origin_ts == t(1)
    assert ev.bottom == 99.0 and ev.ts == t(1) and ev.meta["level"] == "asia_low"


def test_run_through_high_without_reclaim():
    bars = candles([(99, 99.5, 98, 99), (99, 101, 99, 100.8), (100.8, 102, 100.5, 101.9), (102, 103, 101.5, 102.8)])
    (ev,) = sweeps(bars, [Level("pdh", 100.0, "high", t(0))], reclaim=3)
    assert ev.kind == "run" and ev.direction == "bull"


def test_sweep_ignores_bars_before_level_exists():
    bars = candles([(101, 101, 99, 100.5), (101, 102, 100.5, 101.5)])
    assert sweeps(bars, [Level("x", 100.0, "low", t(1))]) == []


# --- structure ----------------------------------------------------------------------

def test_bos_then_mss_on_close_beyond_swing():
    rows = [
        (100, 101, 99, 100),     # 0
        (100, 103, 99.5, 102),   # 1 swing high 103 (confirmed at 2)
        (102, 102.5, 98, 98.5),  # 2
        (98.5, 99, 96, 97),      # 3 swing low 96 (confirmed at 4)
        (97, 100, 96.5, 99.5),   # 4
        (99.5, 103.5, 99, 103.2),  # 5 close > 103 → bullish BOS (no prior trend)
        (103.2, 103.4, 97, 97.2),  # 6
        (97.2, 97.5, 95, 95.5),    # 7 close < 96 → bearish MSS (flips bull)
    ]
    ev = structure(candles(rows), "1m")
    assert [(e.kind, e.direction, e.origin_ts) for e in ev] == [("bos", "bull", t(5)), ("mss", "bear", t(7))]


def test_wick_beyond_swing_is_not_a_break():
    rows = [(100, 101, 99, 100), (100, 103, 99.5, 102), (102, 102.5, 98, 98.5), (98.5, 104, 98, 102.9)]
    assert structure(candles(rows), "1m") == []


def test_swing_levels_exist_only_after_confirmation():
    from ict_engine.concepts.events import swing_levels
    df = candles([(10, 11, 9, 10), (10, 13, 9, 12), (12, 12, 8, 9), (9, 10, 7, 8), (8, 11, 8, 10)])
    lv = {l.side: l for l in swing_levels(swings(df, "1m"))}
    assert lv["high"].price == 13 and lv["high"].valid_from == t(2)
    assert lv["low"].price == 7 and lv["low"].valid_from == t(4)


def test_ifvg_inherits_gap_lifecycle_and_min_size():
    bars = candles([(103, 103, 103, 103)] * 3 + [(101, 101, 98, 98.5)] + [(98.5, 103, 98.5, 102.8)])
    (ifvg,) = inversions([_bull_gap()], bars)
    # bearish IFVG 100–102 is invalidated by a body close back above 102
    st = gap_lifecycle(ifvg, bars)
    assert st.inverted == t(4) and not st.valid_at(t(4))
    assert inversions([_bull_gap()], bars, min_size=5) == []
