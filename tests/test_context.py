from datetime import date, datetime, time, timedelta

import pandas as pd
import pytest

from ict_engine.concepts.context import build_context, daily_bias, pricing

NY = "America/New_York"


def session(day: date, low: float, high: float, open_: float, close: float) -> pd.DataFrame:
    """One trading day of 1m bars (18:00 prev evening → 16:59) moving open→low→high→close."""
    start = pd.Timestamp(datetime.combine(day - timedelta(days=1), time(18)), tz=NY)
    idx = pd.date_range(start, start + pd.Timedelta(hours=23) - pd.Timedelta(minutes=1), freq="1min")
    n = len(idx)
    path = pd.Series([open_] * n, index=idx, dtype=float)
    q = n // 4
    path.iloc[q:2 * q] = low
    path.iloc[2 * q:3 * q] = high
    path.iloc[3 * q:] = close
    return pd.DataFrame({"open": path, "high": path, "low": path, "close": path})


def week(days):
    return pd.concat([session(*d) for d in days])


# Mon 8 Jan, Tue 9 Jan 2024 (Tue context uses Mon as previous day)
MON = (date(2024, 1, 8), 95.0, 110.0, 100.0, 105.0)
TUE = (date(2024, 1, 9), 101.0, 112.0, 104.0, 111.0)


def test_pricing_zone_and_quadrant():
    p = pricing(110, 100, 150)
    assert p.zone == "discount" and p.quadrant == 1 and p.fraction == 0.2
    assert pricing(112.5, 100, 150).quadrant == 2      # a quadrant includes its lower edge
    assert pricing(140, 100, 150).zone == "premium" and pricing(140, 100, 150).quadrant == 4
    assert pricing(125, 100, 150, eq_band=0.02).zone == "equilibrium"
    with pytest.raises(ValueError):
        pricing(1, 5, 5)


def test_context_levels_use_previous_day_only():
    bars = week([MON, TUE])
    ctx = build_context(bars, date(2024, 1, 9))
    assert ctx.levels["pdh"] == 110 and ctx.levels["pdl"] == 95
    # Asia 20:00–00:00 Mon evening: Tue's synthetic path sits at 104, then drops to its low 101 at 23:45
    assert ctx.levels["asia_high"] == 104 and ctx.levels["asia_low"] == 101


def test_context_has_no_lookahead():
    bars = week([MON, TUE])
    ctx = build_context(bars, date(2024, 1, 9))
    # Tuesday's own high (112) must not appear anywhere
    assert 112 not in ctx.levels.values()
    assert all(hi <= 110 for _, hi in ctx.ranges.values())


def test_ndog_from_1659_close_to_1800_open():
    bars = week([MON, TUE])
    ctx = build_context(bars, date(2024, 1, 9))
    (ndog,) = [g for g in ctx.gaps if g.name == "ndog"]
    assert (ndog.close, ndog.open) == (105, 104)


def test_liquidity_levels_for_sweeps():
    ctx = build_context(week([MON, TUE]), date(2024, 1, 9))
    names = {lv.name: lv.side for lv in ctx.liquidity}
    assert names["pdh"] == "high" and names["pdl"] == "low" and names["asia_low"] == "low"


def test_daily_bias_rules():
    def d(rows):
        return pd.DataFrame(rows, columns=["high", "low"])
    assert daily_bias(d([(110, 100), (108, 98)]))[0] == "bear"
    assert daily_bias(d([(110, 100), (112, 102)]))[0] == "bull"
    assert daily_bias(d([(110, 100), (112, 98)])) == ("neutral", "outside day (both sides taken)")
    assert daily_bias(d([(110, 100), (108, 102)])) == ("neutral", "inside day")


# --- named bias rules -----------------------------------------------------------

from ict_engine.concepts.context import BIAS_RULES, bias_draw, bias_draw_htf, bias_htf20  # noqa: E402


def dly(rows):
    """Daily bars from (high, low, close) rows, oldest first."""
    return pd.DataFrame(rows, columns=["high", "low", "close"])


def trend(n, start, step):
    """n days stepping by ``step`` (range 10 wide, close mid-range)."""
    return [(start + i * step + 5, start + i * step - 5, start + i * step) for i in range(n)]


def test_bias_rule_registry():
    assert set(BIAS_RULES) == {"prev_day", "htf20", "draw", "draw_htf"}
    assert BIAS_RULES["prev_day"] is daily_bias


def test_htf20_equilibrium():
    up = dly(trend(20, 100, 1))           # range 95..124, eq 109.5, last close 119
    assert bias_htf20(up)[0] == "bull"
    down = dly(trend(20, 200, -1))        # last close 181, eq (205+176)/2 = 190.5
    assert bias_htf20(down)[0] == "bear"
    assert bias_htf20(dly(trend(19, 100, 1)))[0] == "neutral"   # not enough history
    # only the last 20 days count: an old extreme low 21 days back is ignored
    rows = [(1000, 0, 500)] + [(110, 100, 104)] * 20             # eq 105, close 104
    assert bias_htf20(dly(rows))[0] == "bear"


def test_draw_one_sided_and_inside_days():
    assert bias_draw(dly([(110, 100, 105), (112, 101, 111)]))[0] == "bull"    # ran high only
    assert bias_draw(dly([(110, 100, 105), (108, 98, 99)]))[0] == "bear"      # ran low only
    assert bias_draw(dly([(110, 100, 105), (108, 102, 104)])) == ("neutral", "inside day")
    assert bias_draw(dly([(110, 100, 105)]))[0] == "neutral"


def test_draw_outside_day_exceptions():
    bull_htf = trend(20, 100, 1)          # HTF bullish
    last = bull_htf[-1]                   # (124, 114, 119)
    out_down = (last[0] + 2, last[1] - 2, last[1])          # outside day, lower-half close
    rows = bull_htf + [out_down]
    assert bias_htf20(dly(rows))[0] == "bull"
    assert bias_draw(dly(rows))[0] == "bull"
    out_up = (last[0] + 2, last[1] - 2, last[0] + 1)        # outside day, upper-half close, HTF bull
    assert bias_draw(dly(bull_htf + [out_up])) == ("neutral", "outside day (both sides taken)")

    bear_htf = trend(20, 200, -1)
    last = bear_htf[-1]                   # (186, 176, 181)
    out_up = (last[0] + 2, last[1] - 2, last[0] + 1)
    rows = bear_htf + [out_up]
    assert bias_htf20(dly(rows))[0] == "bear"
    assert bias_draw(dly(rows))[0] == "bear"
    out_down = (last[0] + 2, last[1] - 2, last[1] - 1)
    assert bias_draw(dly(bear_htf + [out_down]))[0] == "neutral"
    # outside day without enough HTF history stays neutral
    assert bias_draw(dly([(110, 100, 105), (112, 98, 99)]))[0] == "neutral"


def test_draw_htf_falls_back_to_htf20():
    inside = trend(20, 100, 1) + [(123, 115, 118)]          # inside the prior (124, 114) day
    assert bias_draw(dly(inside))[0] == "neutral"
    b, why = bias_draw_htf(dly(inside))
    assert b == "bull" and "fallback" in why
    assert bias_draw_htf(dly([(110, 100, 105), (108, 98, 99)]))[0] == "bear"   # draw wins


def test_context_biases_use_completed_days_only():
    # Mon 95-110, Tue 101-112 (ran Mon high only) → Wed context: prev_day & draw bull
    wed = (date(2024, 1, 10), 90.0, 130.0, 111.0, 92.0)   # Wed's own huge range must not count
    bars = week([MON, TUE, wed])
    ctx = build_context(bars, date(2024, 1, 10))
    assert set(ctx.biases) == set(BIAS_RULES)
    assert ctx.biases["prev_day"][0] == "bull" and ctx.biases["draw"][0] == "bull"
    assert ctx.biases["htf20"][0] == "neutral"            # < 20 days of history
    assert (ctx.bias, ctx.bias_reason) == ctx.biases["prev_day"]
    # Wed's bars (from Tue 18:00) changing does not change any call
    bars2 = week([MON, TUE, (date(2024, 1, 10), 50.0, 60.0, 55.0, 51.0)])
    assert build_context(bars2, date(2024, 1, 10)).biases == ctx.biases
