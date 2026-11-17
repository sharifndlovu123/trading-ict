"""Market activity (ict_engine.concepts.activity) on hand-built 1m candles with known answers: the last hour's range
against the same clock window on earlier weekdays, only bars before the moment, and the min_activity gate (off by
default in every model)."""
import pandas as pd
import pytest

from ict_engine.concepts.activity import gate, relative_activity

NY = "America/New_York"
DAYS = pd.bdate_range("2024-01-01", periods=12, tz=NY)


def bars(last_high=110.0, extra=None):
    parts = []
    for i, d in enumerate(DAYS):
        idx = pd.date_range(d + pd.Timedelta(hours=9), periods=60, freq="1min")
        hi = last_high if i == len(DAYS) - 1 else 102.0             # earlier days: range 2 in 09:00–10:00
        parts.append(pd.DataFrame({"open": 100.0, "high": hi, "low": 100.0, "close": 101.0}, index=idx))
    if extra is not None:
        parts.append(extra)
    return pd.concat(parts).sort_index()


AT = DAYS[-1] + pd.Timedelta(hours=10)


def test_busy_normal_quiet():
    a = relative_activity(bars(110.0), AT)
    assert a["range"] == 10 and a["median"] == 2 and a["relative"] == 5 and a["state"] == "busy"
    assert relative_activity(bars(102.0), AT)["state"] == "normal"
    assert relative_activity(bars(101.0), AT)["state"] == "quiet"      # range 1 = 0.5 × normal


def test_no_look_ahead():
    future = pd.DataFrame({"open": 100.0, "high": 500.0, "low": 100.0, "close": 101.0},
                          index=pd.date_range(AT, periods=30, freq="1min"))
    assert relative_activity(bars(102.0, future), AT) == relative_activity(bars(102.0), AT)


def test_gate_blocks_quiet_and_passes_without_history():
    ok, why = gate(bars(101.0), AT, 0.6)
    assert not ok and "0.50×" in why
    assert gate(bars(102.0), AT, 0.6)[0]
    early = DAYS[2] + pd.Timedelta(hours=10)                           # only two earlier days: cannot judge → pass
    ok, why = gate(bars(101.0), early, 0.6)
    assert ok and "unknown" in why


def test_gate_is_off_by_default_and_labelled_when_on():
    from dataclasses import replace
    from ict_engine.models import model_2022, model_mmxm, model_sb
    for m in (model_2022, model_mmxm, model_sb):
        p = m.Params()
        assert p.min_activity is None and "activity" not in p.variant
        assert "activity" in replace(p, min_activity=0.6).variant


def test_fill_time_mode_is_labelled_and_a_bad_mode_raises():
    from dataclasses import replace
    from datetime import date
    from ict_engine.models import model_2022, model_mmxm, model_sb
    from ict_engine.sim.run import run_day
    for m in (model_2022, model_mmxm, model_sb):
        p = replace(m.Params(), min_activity=0.6, min_activity_at="fill")
        assert "fill" in p.variant and m.Params().min_activity_at == "decision"
    assert "@" not in replace(model_2022.Params(), min_activity=0.6).variant


def test_same_clock_window_across_a_dst_change():
    """The baseline is the same NY clock window on earlier weekdays, also across a DST change (found by the
    microstructure study 2026-11-16: stepping back in 24-hour days lands an hour off for weeks after the change)."""
    days = pd.bdate_range("2024-02-26", "2024-03-12", tz=NY)          # DST starts Sunday 2024-03-10
    parts = []
    for d in days:
        idx = pd.date_range(d + pd.Timedelta(hours=9), periods=60, freq="1min")     # bars only 09:00–10:00 NY
        parts.append(pd.DataFrame({"open": 100.0, "high": 102.0, "low": 100.0, "close": 101.0}, index=idx))
    b = pd.concat(parts)
    at = pd.Timestamp("2024-03-12 10:00", tz=NY)
    a = relative_activity(b, at)
    assert a["median"] == 2 and a["relative"] == 1.0                   # every earlier weekday counted, before and after DST
