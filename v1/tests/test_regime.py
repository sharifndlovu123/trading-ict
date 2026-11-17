"""Market conditions (ict_engine.concepts.regime) on hand-built daily bars with known answers: a straight trend, a
chop, the backdrop from the averages, the volatility state, and nothing from the day itself or later."""
import numpy as np
import pandas as pd
import pytest

from ict_engine.concepts.regime import daily_regimes, efficiency_ratio


def daily(close):
    idx = pd.bdate_range("2020-01-01", periods=len(close))
    c = pd.Series(close, index=idx, dtype=float)
    return pd.DataFrame({"open": c.shift(1).fillna(c.iloc[0]), "high": c + 1, "low": c - 1, "close": c})


def test_efficiency_ratio_line_and_chop():
    line = pd.Series(np.arange(100, 160, 1.0))
    assert efficiency_ratio(line).iloc[-1] == pytest.approx(1.0)
    chop = pd.Series([100 + (i % 2) for i in range(60)], dtype=float)
    assert efficiency_ratio(chop).iloc[-1] == pytest.approx(0.0)


def test_states_and_backdrop():
    up = daily_regimes(daily(np.linspace(100, 400, 300)))
    assert up.state.iloc[-1] == "trending up" and up.backdrop.iloc[-1] == "bull"
    down = daily_regimes(daily(np.linspace(400, 100, 300)))
    assert down.state.iloc[-1] == "trending down" and down.backdrop.iloc[-1] == "bear"
    flat = daily_regimes(daily([200 + 3 * ((i % 4) - 1.5) for i in range(300)]))
    assert flat.state.iloc[-1] == "consolidating"


def test_volatility_state():
    c = np.r_[np.full(280, 100.0), np.full(40, 100.0)]
    d = daily(c)
    d.loc[d.index[-40:], "high"] += 4                      # the last 40 days: a much wider daily range
    d.loc[d.index[-40:], "low"] -= 4
    r = daily_regimes(d)
    assert r.vol.iloc[-1] == "high" and r.vol.iloc[200] == "normal"


def test_only_bars_before_the_day_are_used():
    c = np.linspace(100, 400, 300)
    a = daily_regimes(daily(c))
    c2 = c.copy(); c2[-1] = 1.0                            # today collapses
    b = daily_regimes(daily(c2))
    assert a.iloc[-1].state == b.iloc[-1].state and a.iloc[-1].er20 == pytest.approx(b.iloc[-1].er20)
    c3 = c.copy(); c3[-2] = 1.0                            # yesterday collapses: today's reading must change
    assert daily_regimes(daily(c3)).iloc[-1].ret20 != pytest.approx(a.iloc[-1].ret20)
