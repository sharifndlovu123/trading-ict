"""Bias rule ``weekly_structure`` (research/preregistered-weekly-structure-2026-11-16.md, amendment 1; ruling §21):
intermediate-term swings; bear until a weekly close breaks the protected lower high with displacement (0.25 weekly ATR);
higher highs below it are shifts, not a change; a poke above it without such a close raises it to that high (range top).
Completed weeks only; a swing counts from the week it is known."""
import pandas as pd

from ict_engine.concepts.context import (BIAS_RULES, _term_swings, _weekly_bars, bias_weekly_structure,
                                         weekly_structure_state)

NY = "America/New_York"
# Weekly mids: peak, trough, peak, ... (each week's range = mid ± 5, close = mid; ATR = 10 → a break needs 2.5 beyond).
#   idx 0–15: a downtrend (peaks 300 320 310 300 290 295 285 280, troughs 280 290 270 250 240 245 230 235)
#   idx 16 P290: a higher high (295) still below the protected high 300
#   idx 18 P298: high 303 pokes above 300, close 298 is no break → the guard rises to 303
#   idx 20 P306: close 306 > 303 + 2.5 → the break, bull
# ITH: idx10 (300, known at 13; idx2 is the first short-term high so it can't be intermediate).
# ITL: idx9 (235, known at 12), idx13 (225, known at 16).
MIDS = [300, 280, 320, 290, 310, 270, 300, 250, 290, 240, 295, 245, 285, 230, 280, 235, 290, 260, 298, 270, 306, 285]


def daily(mids, last_day=4):
    rows, idx = [], []
    start = pd.Timestamp("2024-01-08 16:00", tz=NY)                    # a Monday
    for w, m in enumerate(mids):
        for d in range(5 if w < len(mids) - 1 else last_day + 1):
            idx.append(start + pd.Timedelta(days=7 * w + d))
            rows.append((m + 5, m - 5, m))
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx), columns=["high", "low", "close"], dtype=float)


def state(n):
    return weekly_structure_state(_weekly_bars(daily(MIDS[:n])))


def test_registered_and_weeks_built():
    assert BIAS_RULES["weekly_structure"] is bias_weekly_structure
    w = _weekly_bars(daily(MIDS))
    assert len(w) == len(MIDS) and list(w.close[:3]) == [300.0, 280.0, 320.0]


def test_intermediate_swings_and_when_they_are_known():
    ith, itl = _term_swings(_weekly_bars(daily(MIDS)))
    assert ith == [(10, 300.0, 13)]                                  # idx2 is the first short-term high: no earlier
                                                                     # one to compare with → not intermediate-term
    assert (9, 235.0, 12) in itl and (13, 225.0, 16) in itl
    assert all(i < k for i, _, k in ith + itl)                       # never known in its own week


def test_bear_after_breaking_the_intermediate_low_with_the_protected_high():
    s, guard, flips = state(17)                                      # weeks 0–16
    assert s == "bear" and guard == 300.0                            # ITH idx10 guards the lower low idx13
    assert [f[1] for f in flips] == ["bear"]


def test_higher_high_below_the_protected_high_is_not_a_change():
    s, guard, _ = state(18)                                          # idx16 P290: a higher high (295 > 285), still below 300
    assert s == "bear" and guard == 300.0


def test_a_poke_without_a_displacement_close_raises_the_guard_to_the_range_top():
    s, guard, _ = state(19)                                          # idx18: high 303 > 300, close 298 < 302.5
    assert s == "bear" and guard == 303.0


def test_a_displacement_close_through_the_range_top_turns_it_bull():
    s, guard, flips = state(21)                                      # idx20: close 306 > 303 + 2.5
    assert s == "bull" and flips[-1][1] == "bull" and flips[-1][0] == _weekly_bars(daily(MIDS)).index[20]
    assert bias_weekly_structure(daily(MIDS[:21]))[0] == "bull"


def test_unfinished_week_is_dropped():
    w = _weekly_bars(daily(MIDS[:21], last_day=2))                   # week 20 only Mon–Wed
    assert len(w) == 20 and weekly_structure_state(w)[0] == "bear"


def test_neutral_without_history():
    b, why = bias_weekly_structure(daily(MIDS[:6]))
    assert b == "neutral" and "no intermediate-term break" in why
