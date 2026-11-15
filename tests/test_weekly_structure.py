"""Bias rule ``weekly_structure`` (research/preregistered-weekly-structure-2026-11-16.md): last two weekly swing highs and
lows both lower → bear, both higher → bull, else neutral; completed weeks only, a swing needs the next week closed."""
import pandas as pd

from ict_engine.concepts.context import BIAS_RULES, bias_weekly_structure, weekly_swings

NY = "America/New_York"
# (high, low) per week: swing highs w1 110, w3 108 (lower); swing lows w2 85, w4 80 (lower) → bear
BEAR = [(100, 90), (110, 95), (105, 85), (108, 88), (100, 80), (104, 84)]


def daily(weeks, last_day=4):
    """Five daily bars per week (Mon–Fri, 16:00 NY) carrying that week's high/low; the final week ends on ``last_day``."""
    rows, idx = [], []
    start = pd.Timestamp("2024-01-08 16:00", tz=NY)                    # a Monday
    for w, (h, lo) in enumerate(weeks):
        days = 5 if w < len(weeks) - 1 else last_day + 1
        for d in range(days):
            idx.append(start + pd.Timedelta(days=7 * w + d))
            rows.append((h, lo, (h + lo) / 2))
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx), columns=["high", "low", "close"], dtype=float)


def test_registered():
    assert BIAS_RULES["weekly_structure"] is bias_weekly_structure


def test_lower_highs_and_lower_lows_is_bear_and_mirror_is_bull():
    assert bias_weekly_structure(daily(BEAR))[0] == "bear"
    bull = [(-lo, -h) for h, lo in BEAR]
    assert bias_weekly_structure(daily(bull))[0] == "bull"


def test_mixed_structure_is_neutral():
    mixed = list(BEAR)
    mixed[3] = (115, 88)                                                 # higher high, lower low
    b, why = bias_weekly_structure(daily(mixed))
    assert b == "neutral" and "mixed" in why


def test_unfinished_week_is_dropped_and_a_swing_waits_for_the_next_week():
    # last week only Mon–Wed: it is dropped, so w4's low (80) is not yet a confirmed swing → one swing low → neutral
    b, why = bias_weekly_structure(daily(BEAR, last_day=2))
    assert b == "neutral" and "fewer than two" in why
    done, sh, sl = weekly_swings(daily(BEAR, last_day=2))
    assert len(done) == len(BEAR) - 1 and [p for _, p in sl] == [85.0]


def test_swings_found():
    _, sh, sl = weekly_swings(daily(BEAR))
    assert [p for _, p in sh] == [110.0, 108.0] and [p for _, p in sl] == [85.0, 80.0]
