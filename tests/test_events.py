"""Event detectors on hand-built candles where the right answer is known."""

from dataclasses import replace

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


# --- order blocks, breakers, mitigation blocks (ICT Bible pp.16-26) -------------------

from ict_engine.concepts.events import breaker_blocks, order_blocks  # noqa: E402


def test_bullish_ob_is_last_down_candles_validated_by_close_above_their_high():
    # up, down, down (the OB: 99.0-101.5), then a close above 101.5 validates it; a FVG forms in the move
    df = candles([(100, 101, 99.5, 100.8), (100.8, 101.5, 99.6, 100.0), (100.0, 100.2, 99.0, 99.4),
                  (99.4, 101.0, 99.3, 100.9), (100.9, 103.0, 100.8, 102.8), (102.8, 104.0, 102.5, 103.8)])
    obs = [e for e in order_blocks(df, "1m") if e.direction == "bull"]
    assert len(obs) == 1
    ob = obs[0]
    assert (ob.top, ob.bottom) == (101.5, 99.0) and ob.origin_ts == t(1)
    assert ob.ts == t(4)                      # bar 3 closes 100.9 < 101.5; bar 4 closes above → known then
    assert ob.meta["candles"] == 2 and ob.meta["fvg"]   # bar 4 low 100.8 > bar 2 high 100.2


def test_ob_needs_the_close_within_max_wait_and_mirrors_for_bears():
    rows = [(100, 100.5, 99, 99.2)] + [(99.2, 99.4, 99.0, 99.2)] * 6 + [(99.2, 101, 99.1, 100.8)]
    assert not [e for e in order_blocks(candles(rows), "1m", max_wait=3) if e.direction == "bull"]
    bear = candles([(100, 100.5, 99.5, 100.4), (100.4, 100.6, 99.0, 99.1), (99.1, 99.2, 97.0, 97.2)])
    obs = [e for e in order_blocks(bear, "1m") if e.direction == "bear"]
    assert len(obs) == 1 and (obs[0].top, obs[0].bottom) == (100.5, 99.5) and obs[0].ts == t(1)


def _three_swings(second_low):
    """L1 at 95 (bar 1) → H 103 (bar 4, up-close candles bars 3-4) → L2 at ``second_low`` (bar 7) → close above 103."""
    return candles([(98, 98, 96, 97), (97, 97, 95, 96), (96, 98, 96, 97.5), (97.5, 101, 97, 100.5),
                    (100.5, 103, 100, 102), (102, 102, 99, 99.5), (99.5, 99.5, second_low + 1, 98),
                    (98, 98.5, second_low, 98.2), (98.2, 101, 98, 100.5), (100.5, 104, 100, 103.6),
                    (103.6, 104.5, 103, 104)])


def test_bullish_breaker_after_lower_low_and_mitigation_after_higher_low():
    br = [e for e in breaker_blocks(_three_swings(94.0), "1m") if e.direction == "bull"]
    assert [e.kind for e in br] == ["breaker"] and br[0].meta["swept"]
    b = br[0]
    assert b.origin_ts == t(2) and (b.top, b.bottom) == (103.0, 96.0)  # up-close candles bars 2-4 in the high
    assert b.ts == t(9)                                                  # bar 9 closes 103.6 > 103
    mb = [e for e in breaker_blocks(_three_swings(96.5), "1m") if e.direction == "bull"]
    assert [e.kind for e in mb] == ["mitigation"]


def _lower_high_in_the_leg():
    """As ``_three_swings`` but with a minor lower high (bar 6, 102.5) inside the leg down and no swing low before
    it: swings read low (1) / high (4) / high (6) / low (8)."""
    return candles([(98, 98, 96, 97), (97, 97, 95, 96), (96, 98, 96, 97.5), (97.5, 101, 97, 100.5),
                    (100.5, 103, 100, 102), (102, 102.2, 99.5, 99.8), (99.8, 102.5, 99.2, 99.4),
                    (99.4, 99.5, 95, 95.5), (95.5, 98.5, 94, 98.2), (98.2, 101, 98, 100.5),
                    (100.5, 104, 100, 103.6), (103.6, 104.5, 103, 104)])


def test_merge_finds_the_breaker_behind_a_minor_lower_high():
    df = _lower_high_in_the_leg()
    assert not [e for e in breaker_blocks(df, "1m") if e.direction == "bull"]          # strict order: hidden
    br = [e for e in breaker_blocks(df, "1m", merge=True) if e.direction == "bull"]
    assert [e.kind for e in br] == ["breaker"]
    assert br[0].origin_ts == t(2) and (br[0].top, br[0].bottom) == (103.0, 96.0) and br[0].ts == t(10)
    for n in range(6, len(df)):                                                        # nothing known early
        assert all(e.ts <= df.index[n - 1] for e in breaker_blocks(df.iloc[:n], "1m", merge=True))
    base = _three_swings(94.0)                                                         # merge only adds
    assert breaker_blocks(base, "1m", merge=True) == breaker_blocks(base, "1m")


def test_blocks_retire_on_a_body_close_beyond_their_50pct():
    ob = Event("ob", "1m", "bull", t(0), t(0), 102.0, 100.0)
    after = candles([(103, 103, 101.5, 102.5), (102.5, 102.6, 100.8, 101.2), (101.2, 101.3, 100.5, 100.7)],
                    start="2024-01-09 10:01")
    st = gap_lifecycle(ob, after)
    assert st.touched == t(1) and st.retired == t(3) and st.inverted is None
    assert st.valid_at(t(2)) and not st.valid_at(t(3))


def test_blocks_have_no_lookahead():
    df = _three_swings(94.0)
    full = breaker_blocks(df, "1m") + order_blocks(df, "1m")
    for e in full:
        cut = df[df.index <= e.ts]
        again = breaker_blocks(cut, "1m") + order_blocks(cut, "1m")
        assert any((x.kind, x.direction, x.top, x.bottom, x.ts) == (e.kind, e.direction, e.top, e.bottom, e.ts)
                   for x in again), e


def test_order_block_open_confirmation_validates_earlier_and_keeps_the_body():
    # Sharif's Apr 2024 daily NQ: green OB, next candle closes below its open (not its low), then a close below its low
    from ict_engine.concepts.events import order_blocks, quadrants
    idx = pd.date_range("2024-04-10", periods=4, freq="D", tz="America/New_York")
    df = pd.DataFrame({"open": [18190.0, 18184.0, 18486.25, 18151.0], "high": [18200.0, 18518.75, 18507.75, 18350.75],
                       "low": [18150.0, 18088.0, 18120.25, 17841.5], "close": [18160.0, 18485.5, 18172.5, 17875.0]}, index=idx)
    ext = [e for e in order_blocks(df, "1d") if e.direction == "bear"]
    opn = [e for e in order_blocks(df, "1d", confirm="open") if e.direction == "bear"]
    assert ext[0].ts == idx[3] and opn[0].ts == idx[2]                    # open rule knows it one day earlier
    assert opn[0].origin_ts == idx[1] and opn[0].meta["body"] == (18485.5, 18184.0)
    q = quadrants(*opn[0].meta["body"])
    assert q["50%"] == pytest.approx(18334.75) and q["0%"] == 18184.0


def _bars(highs, lows, start="2024-01-09 09:30"):
    idx = pd.date_range(start, periods=len(highs), freq="1min", tz="America/New_York")
    return pd.DataFrame({"open": lows, "high": highs, "low": lows, "close": highs}, index=idx)


def test_equal_highs_need_two_swings_within_tolerance_and_nothing_through_them():
    from ict_engine.concepts.events import equal_levels, swings
    #          0    1    2    3    4    5    6    7    8    9   10
    highs = [100, 105, 101, 102, 105.5, 101, 103, 104, 108, 103, 102]
    lows = [h - 1 for h in highs]
    b = _bars(highs, lows)
    eq = [lv for lv in equal_levels(b, swings(b, "1m"), tol=1.0) if lv.side == "high"]
    assert len(eq) == 1 and eq[0].price == 105.5 and eq[0].name.startswith("1m_eqh@")
    assert eq[0].valid_from == b.index[5]                        # 2nd swing (bar 4) is confirmed when bar 5 closes
    # the 108 high (bar 8) is no partner: too far; and it trades through 105.5, so later highs can't join that cluster
    assert all(lv.valid_from <= b.index[5] for lv in eq)


def test_equal_lows_broken_in_between_do_not_count():
    from ict_engine.concepts.events import equal_levels, swings
    lows = [100, 95, 99, 90, 99, 95.2, 99]                      # 95 … 90 (trades through) … 95.2
    highs = [l + 1 for l in lows]
    b = _bars(highs, lows)
    assert [lv for lv in equal_levels(b, swings(b, "1m"), tol=0.5) if lv.side == "low"] == []


def test_liquidity_pools_merge_nearby_levels_and_score_them():
    from ict_engine.concepts.events import Level, liquidity_pools
    t = pd.Timestamp("2024-01-09 09:30", tz="America/New_York")
    lv = [Level("pdh", 18010.0, "high", t), Level("15m_eqh@01-08 10:00", 18006.0, "high", t),
          Level("pwh", 18100.0, "high", t), Level("pdl", 17900.0, "low", t)]
    pools = {(p.side, p.price): p for p in liquidity_pools(lv, tol=5.0)}
    p = pools[("high", 18010.0)]
    assert p.inner == 18006.0 and set(p.members) == {"pdh", "15m_eqh@01-08 10:00"} and p.strength == 3
    assert pools[("high", 18100.0)].strength == 1 and pools[("low", 17900.0)].members == ("pdl",)


def test_pool_strength_counts_one_price_once():
    from ict_engine.concepts.events import Level, liquidity_pools
    t = pd.Timestamp("2024-01-09 09:30", tz="America/New_York")
    lv = [Level("pwh", 18518.75, "high", t), Level("1d_swing_high@04-10 18:00", 18518.75, "high", t),
          Level("4h_eqh3@04-05 10:00", 18515.0, "high", t)]
    (p,) = liquidity_pools(lv, tol=5.0)
    assert p.strength == 1 + 3


def _tf_bars(rows):
    """Higher-timeframe bars: (first ts, close ts, close)."""
    idx = pd.DatetimeIndex([pd.Timestamp(a, tz=NY) for a, _, _ in rows])
    return pd.DataFrame({"open": [c for *_, c in rows], "high": [c for *_, c in rows], "low": [c for *_, c in rows],
                         "close": [c for *_, c in rows],
                         "close_ts": [pd.Timestamp(b, tz=NY) for _, b, _ in rows]}, index=idx)


def test_htf_fvg_inverts_on_its_own_timeframe_close_not_the_first_1m_close():
    """A daily bull FVG 105–110: on day 1 a 1m candle closes at 104 but the day closes back at 106 (no
    inversion on the daily); day 2 closes at 103 → the IFVG is known at day 2's close, not earlier."""
    gap = Event("fvg", "1d", "bull", pd.Timestamp("2024-01-08 16:59", tz=NY), pd.Timestamp("2024-01-07 18:00", tz=NY),
                top=110.0, bottom=105.0)
    m1 = candles([(107, 107, 104, 104)] + [(106, 106, 106, 106)] * 3, start="2024-01-09 10:00")
    days = _tf_bars([("2024-01-08 18:00", "2024-01-09 16:59", 106.0), ("2024-01-09 18:00", "2024-01-10 16:59", 103.0)])
    (one_min,) = inversions([gap], m1)
    (own_tf,) = inversions([gap], m1, tf_bars={"1d": days})
    assert one_min.ts == pd.Timestamp("2024-01-09 10:00", tz=NY)
    assert own_tf.ts == pd.Timestamp("2024-01-10 16:59", tz=NY) and own_tf.direction == "bear"
    # no look-ahead: with only day 1 known there is no IFVG yet
    assert inversions([gap], m1, tf_bars={"1d": days.iloc[:1]}) == []
    # a FVG of a timeframe not in tf_bars keeps the 1m rule
    assert inversions([replace(gap, tf="4h")], m1, tf_bars={"1d": days})[0].ts == one_min.ts
