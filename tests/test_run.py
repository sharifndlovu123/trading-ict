"""Day runner: one active order at a time, trade cap per day or per window."""

from datetime import date

import pandas as pd

from ict_engine.models import model_2022
from ict_engine.models.base import Setup, TradePlan
from ict_engine.sim import run
from tests.test_model_2022 import DAY as MODEL_DAY, bars

SYNTHETIC_PRICES = True                  # conftest: no costs on the ~100-price synthetic day

DAY = date(2024, 1, 9)
NY = "America/New_York"


def ts(hm):
    return pd.Timestamp(f"2024-01-09 {hm}", tz=NY)


def fake(decided, window, entry, stop, tp1):
    s = Setup("2022_model", "v", "US100", "day", DAY, "long", ts(decided), {}, tags={"window": window})
    s.plan = TradePlan("long", ts(decided), ts(decided) + pd.Timedelta(minutes=30), entry, stop, tp1, tp1)
    return s


def frame(rows):
    """rows: (HH:MM, open, high, low, close); fills the rest of the day flat at the last close."""
    idx = pd.date_range(ts("00:00"), ts("16:30"), freq="1min")
    df = pd.DataFrame(index=idx, columns=["open", "high", "low", "close"], dtype=float)
    last = 100.0
    for t in idx:
        df.loc[t] = last
        for hm, o, h, l, c in rows:
            if t == ts(hm):
                df.loc[t] = (o, h, l, c)
                last = c
    return df


def patched(monkeypatch, setups):
    monkeypatch.setattr(run, "build_context", lambda b, d: None)
    monkeypatch.setattr(model_2022, "find_setups", lambda *a, **k: setups)


# 09:00 AM-window setup loses; 13:30 PM-window setup would win.
ROWS = [("09:01", 100, 100, 98.5, 99), ("09:02", 99, 99, 97, 97),          # fill 99, stop 98
        ("13:31", 97, 97, 95.5, 96), ("13:35", 96, 99.5, 96, 99.2)]          # fill 96, TP1 99


def test_daily_cap_blocks_the_second_trade(monkeypatch):
    setups = [fake("09:00", "ny_am_kz", 99, 98, 101), fake("13:30", "ny_pm_kz", 96, 95, 99)]
    patched(monkeypatch, setups)
    out = run.run_day(frame(ROWS), DAY, "US100", max_trades=1, cap_scope="day")
    assert out[0].result.exit_reason == "stop"
    assert out[1].result is None and out[1].gates[-1].name == "cap"


def test_window_cap_allows_one_trade_per_window(monkeypatch):
    setups = [fake("09:00", "ny_am_kz", 99, 98, 101), fake("09:10", "ny_am_kz", 97, 96, 99),
              fake("13:30", "ny_pm_kz", 96, 95, 99)]
    patched(monkeypatch, setups)
    out = run.run_day(frame(ROWS), DAY, "US100", max_trades=1, cap_scope="window")
    assert out[0].result.exit_reason == "stop"
    assert out[1].result is None and "ny_am_kz" in out[1].gates[-1].detail     # same window → capped
    assert out[2].result.vote                                                  # new window → traded


def test_real_model_runs_with_window_scope():
    setups = run.run_day(bars(), MODEL_DAY, "US100", cap_scope="window")
    assert isinstance(setups, list)


def test_newer_setup_cancels_a_stale_unfilled_order(monkeypatch):
    # 09:00 order at 95 never fills; 09:30 setup replaces it and wins.
    stale = fake("09:00", "ny_am_kz", 95, 94, 101)
    stale.plan = TradePlan("long", ts("09:00"), ts("11:00"), 95, 94, 103, 103)
    fresh = fake("09:30", "ny_am_kz", 99, 98, 101)
    patched(monkeypatch, [stale, fresh])
    rows = [("09:31", 100, 100, 98.8, 99.2), ("09:40", 99.2, 101.5, 99, 101.2)]
    out = run.run_day(frame(rows), DAY, "US100")
    assert out[0].result.exit_reason == "cancelled" and out[0].result.exit_at == ts("09:30")
    assert out[1].result.vote


def test_filled_trade_is_not_cancelled_by_a_newer_setup(monkeypatch):
    first, second = fake("09:00", "ny_am_kz", 99, 98, 101), fake("09:05", "ny_am_kz", 99.5, 98, 101)
    patched(monkeypatch, [first, second])
    rows = [("09:01", 100, 100, 98.8, 99.2), ("09:40", 99.2, 101.5, 99, 101.2)]
    out = run.run_day(frame(rows), DAY, "US100")
    assert out[0].result.vote and out[1].gates[-1].name == "cap"
