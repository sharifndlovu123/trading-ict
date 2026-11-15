"""Confirmation entries for the engine plan (research/scripts/plan_build.replay_confirm). Sharif 2026-11-16: "we wait for
any PD array action that supports what we are aiming to achieve or against." Hand-built 1m candles grouped as 5m
candles, with known answers: support → a 5m FVG our way, entry at its near edge; against → a 5m close through the zone,
flip on the retest; no flip → no trade; TP1 first → missed. Confirmation is used only from the 5m candle's close."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from plan_build import manage, replay_confirm, wall  # noqa: E402

NY = "America/New_York"
AT = pd.Timestamp("2023-03-15 08:30", tz=NY)


def five(rows):
    """Each (o, h, l, c) 5m candle as five 1m candles: up to the high first, then down to the low, then the close."""
    out = []
    for o, h, l, c in rows:
        out += [(o, h, o, h), (h, h, l, l), (l, max(l, c), l, c), (c, c, c, c), (c, c, c, c)]
    idx = pd.date_range(AT, periods=len(out), freq="1min", tz=NY)
    return pd.DataFrame(out, columns=["open", "high", "low", "close"], index=idx, dtype=float)


# a short from the array 100–102: entry 100 (near edge), stop 105 (fake-out 104.5 + 0.05 ADR), TP1 90, final 85
PLAN = {"side": "short", "entry": 100.0, "stop": 105.0, "tp1": 90.0, "final": 85.0, "rtf": "1h", "adr": 10.0,
        "array": {"bottom": 100.0, "top": 102.0}, "range": {"lo": 90.0, "hi": 104.5}, "pools_against": [110.0, 115.0]}
HEAD = [(97, 99, 96.5, 99),           # B0 below the zone
        (99, 101, 99, 100.5)]         # B1 touches 100 → armed


SUPPORT = HEAD + [(100.5, 101.5, 99.5, 99.8),   # B2
                  (99.8, 99.9, 97, 97.5),       # B3
                  (97.5, 98.5, 95, 95.5),       # B4: high 98.5 < B2 low 99.5 → bear FVG 98.5–99.5 (support)
                  (95.5, 98.6, 95.5, 97),       # B5 retraces to 98.5 → filled
                  (97, 97, 89, 89.5),           # B6 TP1 90
                  (89.5, 89.5, 84, 85)]         # B7 final 85


def test_support_stop_beyond_the_zone_is_the_default():
    r = replay_confirm(five(SUPPORT), AT, PLAN, flip=True)
    assert r["mode"] == "confirm_flip" and r["stage"] == "support" and r["entry"] == 98.5
    assert r["stop"] == pytest.approx(102.5)                      # the zone's far edge 102 + 0.05 ADR (reaction 101.5 inside)
    assert r["confirmed"] == wall(AT + pd.Timedelta(minutes=25))  # B4's close: known only then (no look-ahead)
    assert r["r_tp1"] == pytest.approx(8.5 / 4, abs=0.01)
    assert r["runner_r"] == pytest.approx((8.5 + 13.5) / 8, abs=0.01)


def test_support_stop_beyond_the_reaction_variant():
    r = replay_confirm(five(SUPPORT), AT, PLAN, flip=True, stop_at="reaction")
    assert r["mode"] == "confirm_flip_reaction" and r["entry"] == 98.5
    assert r["stop"] == pytest.approx(101.7)                      # reaction high 101.5 + 0.02 ADR
    assert r["r_tp1"] == pytest.approx(8.5 / 3.2, abs=0.01)
    assert r["runner_r"] == pytest.approx((8.5 + 13.5) / 6.4, abs=0.01)


def test_zone_stop_uses_the_reaction_when_it_wicked_past_the_far_edge():
    rows = HEAD + [(100.5, 102.6, 99.5, 99.8), (99.8, 99.9, 97, 97.5), (97.5, 98.5, 95, 95.5)]   # wick 102.6 > 102, close inside
    r = replay_confirm(five(rows), AT, PLAN)
    assert r["stage"] == "support" and r["stop"] == pytest.approx(103.1)    # 102.6 + 0.05 ADR


def test_bad_stop_at_raises():
    with pytest.raises(ValueError):
        replay_confirm(five(SUPPORT), AT, PLAN, stop_at="nope")


def test_against_close_through_flips_on_the_retest():
    b = five(HEAD + [(100.5, 103, 100.5, 102.8),  # B2 closes 102.8 > 102 (the far edge) → against
                     (102.8, 103, 101.8, 102.5),  # B3 retests 102 → long filled
                     (102.5, 111, 102.5, 110.5)])  # B4 TP1 104.5 (the fake-out) then final 110 (next buyside pool)
    r = replay_confirm(b, AT, PLAN, flip=True)
    assert r["stage"] == "flip" and r["side"] == "long" and r["entry"] == 102.0
    assert r["stop"] == pytest.approx(99.5) and r["tp1"] == 104.5 and r["final"] == 110.0
    assert r["runner_r"] == pytest.approx(0.5 * 2.5 / 2.5 + 0.5 * 8 / 2.5, abs=0.01)


def test_against_without_flip_is_no_trade():
    b = five(HEAD + [(100.5, 103, 100.5, 102.8), (102.8, 103, 101.8, 102.5)])
    r = replay_confirm(b, AT, PLAN, flip=False)
    assert r["stage"] == "against" and r["runner_r"] == 0.0 and "entry" not in r


def test_tp1_before_the_zone_is_missed_and_nothing_is_chased():
    b = five([(97, 97, 89, 89.5), (89.5, 101, 89.5, 100.5)])
    r = replay_confirm(b, AT, PLAN)
    assert r["outcome"].startswith("missed") and r["runner_r"] == 0.0


def test_a_wick_through_the_far_edge_is_not_against():
    b = five(HEAD + [(100.5, 103, 100.5, 101.5),  # wick to 103, close 101.5 inside the zone
                     (101.5, 101.6, 99.6, 99.8), (99.8, 99.9, 97, 97.5), (97.5, 99.5, 95, 95.5)])
    r = replay_confirm(b, AT, PLAN)
    assert r["stage"] in ("support", "armed") and r["stage"] != "flip"


def test_manage_stop_first_on_the_same_bar():
    idx = pd.date_range(AT, periods=1, freq="1min", tz=NY)
    bar = pd.DataFrame([(100, 106, 89, 95)], columns=["open", "high", "low", "close"], index=idx, dtype=float)
    assert manage(bar, 100, 105, 90, 85, long=False)["runner_r"] == -1.0
