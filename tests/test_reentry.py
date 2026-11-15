"""Re-entry (research/preregistered-reentry-2026-11-16.md): one extra trade in a window — ``after_stop`` only after the
window's filled trade was stopped and only on the same side; ``any`` after any filled trade. Never more than one extra."""
from dataclasses import replace

import pandas as pd

from ict_engine.models import model_2022
from ict_engine.models.base import Setup, TradePlan
from ict_engine.sim import run
from tests.test_run import DAY, frame, patched, ts

SYNTHETIC_PRICES = True

LOSS = [("09:01", 100, 100, 98.5, 99), ("09:02", 99, 99, 97, 97)]           # long fills 99, stopped at 98
WIN = [("09:01", 100, 100, 98.5, 99), ("09:03", 99, 101.5, 99, 101.2)]      # long fills 99, TP1 101


def setup(decided, side, entry, stop, tp1, window="ny_am_kz"):
    s = Setup("2022_model", "v", "US100", "day", DAY, side, ts(decided), {}, tags={"window": window})
    s.plan = TradePlan(side, ts(decided), ts(decided) + pd.Timedelta(minutes=30), entry, stop, tp1, tp1)
    return s


def day(monkeypatch, rows, setups, mode):
    patched(monkeypatch, setups)
    return run.run_day(frame(rows), DAY, "US100", params=replace(model_2022.Params(), reentry=mode), max_trades=1)


def test_after_stop_admits_one_same_side_retry_in_the_window(monkeypatch):
    first, again, third = setup("09:00", "long", 99, 98, 101), setup("09:10", "long", 97, 96, 99), setup("09:50", "long", 97, 96, 99)
    out = day(monkeypatch, LOSS, [first, again, third], "after_stop")
    assert out[0].result.exit_reason == "stop"
    assert out[1].result is not None and out[1].result.filled_at is not None and out[1].tags.get("reentry")
    assert out[2].result is None and out[2].gates[-1].name == "cap"            # only one extra


def test_after_stop_refuses_the_other_side_and_a_retry_after_a_win(monkeypatch):
    out = day(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), setup("09:10", "short", 97, 98, 95)], "after_stop")
    assert out[1].result is None and out[1].gates[-1].name == "cap"
    out = day(monkeypatch, WIN, [setup("09:00", "long", 99, 98, 101), setup("09:30", "long", 101, 100, 103)], "after_stop")
    assert out[0].result.vote and out[1].result is None and out[1].gates[-1].name == "cap"


def test_any_control_admits_one_extra_after_any_fill_and_off_keeps_the_cap(monkeypatch):
    out = day(monkeypatch, WIN, [setup("09:00", "long", 99, 98, 101), setup("09:30", "short", 101, 102, 99)], "any")
    assert out[1].result is not None and out[1].tags.get("reentry")
    out = day(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), setup("09:10", "long", 97, 96, 99)], None)
    assert out[1].result is None and out[1].gates[-1].name == "cap"


def test_other_window_is_untouched(monkeypatch):
    out = day(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), setup("13:30", "long", 97, 96, 99, "ny_pm_kz")], "after_stop")
    assert out[1].result is not None and not out[1].tags.get("reentry")


def test_a_cancelled_reentry_order_frees_the_slot_and_nothing_crashes(monkeypatch):
    # 09:10 re-entry order at 90 never fills; 09:15 setup replaces it (still the one extra); 09:50 is capped.
    stale = setup("09:10", "long", 90, 89, 99)
    out = day(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), stale, setup("09:15", "long", 97, 96, 99),
                                  setup("09:50", "long", 97, 96, 99)], "after_stop")
    assert out[1].result.exit_reason == "cancelled"
    assert out[2].tags.get("reentry") and out[2].result.filled_at is not None
    assert out[3].result is None and out[3].gates[-1].name == "cap"
