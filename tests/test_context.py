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
