"""Gap sweep: path stats and labels on hand-built 1m paths with known answers."""

import pandas as pd
import pytest

from ict_engine.eval import gaps
from tests.test_events import candles, t

END = t(60)


def bars(rows):
    return candles(rows)


def test_path_stats_mfe_and_tp1_after_the_stop():
    # long 100, stop 99, TP1 102. Fill bar 0; +0.8R at bar 1; stopped bar 2; TP1 trades at bar 4 (after the stop)
    b = bars([(100, 100.2, 99.9, 100.1), (100.1, 100.8, 100.0, 100.5), (100.5, 100.5, 98.9, 99.0),
              (99.0, 101.0, 99.0, 100.9), (100.9, 102.1, 100.8, 102.0)])
    st = gaps.path_stats(b, "long", 100, 99, 102, t(0), t(2), END)
    assert st["mfe_r"] == pytest.approx(0.8) and st["mfe_frac"] == pytest.approx(0.4)
    assert st["tp1_after"] and st["mins_held"] == 2
    assert gaps.label("traded", "stop", False, st) == "stop_then_tp1"


def test_path_stats_short_mirror_and_no_tp1_after_session_end():
    b = bars([(100, 100.1, 99.8, 99.9), (99.9, 101.2, 99.9, 101.1), (101.1, 101.1, 97.0, 97.5)])
    st = gaps.path_stats(b, "short", 100, 101, 98, t(0), t(1), t(2))      # session ends before bar 2
    assert st["mfe_r"] == pytest.approx(0.2) and not st["tp1_after"]
    assert gaps.label("traded", "stop", False, st) == "fast_loss"


@pytest.mark.parametrize("status,exit_reason,vote,st,want", [
    ("missed", None, None, {}, "missed"),
    ("not_filled", None, None, {}, "not_filled"),
    ("traded", "tp1", True, {}, "win"),
    ("traded", "time_exit", False, {"mfe_frac": 0.9}, "time_exit"),
    ("traded", "stop", False, {"mfe_frac": 0.85, "mfe_r": 1.7, "tp1_after": False}, "near_miss"),
    ("traded", "stop", False, {"mfe_frac": 0.4, "mfe_r": 0.8, "tp1_after": False}, "slow_loss"),
    ("traded", "stop", False, {"mfe_frac": 0.1, "mfe_r": 0.2, "tp1_after": False}, "fast_loss"),
])
def test_labels(status, exit_reason, vote, st, want):
    assert gaps.label(status, exit_reason, vote, st) == want


def test_every_gap_has_an_orderflow_hypothesis():
    assert set(gaps.LABELS) - {"win"} <= set(gaps.ORDERFLOW)
