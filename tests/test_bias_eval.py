from datetime import date, datetime, time, timedelta

import pandas as pd
import pytest

from ict_engine.concepts.context import BIAS_RULES, build_context
from ict_engine.data.dukascopy import DATA_DIR
from ict_engine.eval.bias import (DayRecord, base_rate, day_outcome, label_days, report, score,
                                  wilson)

NY = "America/New_York"


def _ts(d, t):
    return pd.Timestamp(datetime.combine(d, t), tz=NY)


def path_day(day: date, prices: list[float]) -> pd.DataFrame:
    """1m bars from 18:00 the evening before ``day`` to 16:59, stepping through ``prices`` in
    equal segments (each bar's OHLC = the segment price)."""
    start = _ts(day - timedelta(days=1), time(18))
    idx = pd.date_range(start, start + pd.Timedelta(hours=23) - pd.Timedelta(minutes=1), freq="1min")
    seg = len(idx) // len(prices) + 1
    vals = [prices[i // seg] for i in range(len(idx))]
    s = pd.Series(vals, index=idx, dtype=float)
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s})


D = date(2024, 1, 10)


def test_wilson_known_values():
    assert wilson(0, 0) == (0.0, 1.0)
    lo, hi = wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-4) and hi == pytest.approx(0.7634, abs=1e-4)
    lo, hi = wilson(10, 10)
    assert hi == 1.0 and lo == pytest.approx(0.7225, abs=1e-4)
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and hi == pytest.approx(0.2775, abs=1e-4)


def test_outcome_labels():
    assert day_outcome(path_day(D, [100, 111, 89]), D, 110, 90) == "bull_hit"   # PDH first
    assert day_outcome(path_day(D, [100, 89, 111]), D, 110, 90) == "bear_hit"   # PDL first
    assert day_outcome(path_day(D, [100, 105, 111]), D, 110, 90) == "bull_hit"  # PDH, never PDL
    assert day_outcome(path_day(D, [100, 105, 95]), D, 110, 90) == "none"
    bars = path_day(D, [100])
    bars.iloc[300, bars.columns.get_loc("high")] = 111
    bars.iloc[300, bars.columns.get_loc("low")] = 89
    assert day_outcome(bars, D, 110, 90) == "ambiguous"


def test_outcome_window_ends_at_1600():
    bars = path_day(D, [100])
    bars.loc[_ts(D, time(16, 30)), ["high", "low"]] = [111, 111]   # after 16:00: ignored
    assert day_outcome(bars, D, 110, 90) == "none"
    bars.loc[_ts(D, time(15, 59)), ["high", "low"]] = [111, 111]
    assert day_outcome(bars, D, 110, 90) == "bull_hit"
    early = path_day(D, [100])
    early.loc[_ts(D - timedelta(days=1), time(17, 30))] = [89, 89, 89, 89]   # before 18:00: ignored
    assert day_outcome(early, D, 110, 90) == "none"


def days(n, start=date(2024, 1, 2)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def synthetic(n=25):
    """Rising market: each day trades low → high, a little higher every day."""
    return pd.concat([path_day(d, [100 + i, 95 + i, 106 + i, 103 + i]) for i, d in enumerate(days(n))])


def test_label_days_matches_build_context_and_has_no_lookahead():
    bars = synthetic()
    recs = label_days(bars, min_history=2)
    assert recs and recs[0].day == days(25)[2]
    for r in recs:
        ctx = build_context(bars, r.day)
        assert r.calls == {k: v[0] for k, v in ctx.biases.items()}
    # changing the last day's bars (all at/after its 18:00 start) leaves its calls unchanged
    last = days(25)[-1]
    cut = _ts(last - timedelta(days=1), time(18))
    bars2 = bars.copy()
    bars2.loc[bars2.index >= cut, ["open", "high", "low", "close"]] = 1.0
    r1, r2 = label_days(bars, 2)[-1], label_days(bars2, 2)[-1]
    assert r1.day == r2.day == last and r1.calls == r2.calls
    assert r1.outcome == "bull_hit" and r2.outcome == "bear_hit"


def test_score_counts_and_base_rate():
    rule = next(iter(BIAS_RULES))
    other = {k: "neutral" for k in BIAS_RULES if k != rule}
    recs = [
        DayRecord(date(2024, 1, 8), "bull_hit", {rule: "bull", **other}),    # Mon correct
        DayRecord(date(2024, 1, 9), "bear_hit", {rule: "bull", **other}),    # Tue wrong
        DayRecord(date(2024, 1, 10), "bear_hit", {rule: "bear", **other}),   # Wed correct
        DayRecord(date(2024, 1, 11), "none", {rule: "bull", **other}),       # no outcome
        DayRecord(date(2024, 1, 12), "bull_hit", {rule: "neutral", **other}),
    ]
    s = score(recs, rule)
    assert (s.calls, s.correct, s.bull_calls, s.bear_calls, s.neutral, s.no_outcome) == (3, 2, 2, 1, 1, 1)
    assert s.by_weekday["Mon"] == [1, 1] and s.by_weekday["Tue"] == [0, 1] and s.by_weekday["Fri"] == [0, 0]
    assert base_rate(recs) == (2, 4)
    assert s.expected(0.5) == pytest.approx(0.5)
    assert s.expected(0.75) == pytest.approx((2 * 0.75 + 0.25) / 3)
    text = report(recs, "t")
    assert "always_bull" in text and rule in text


@pytest.mark.skipif(not (DATA_DIR / "bars" / "usatechidxusd" / "2023-12-bid.parquet").exists(),
                    reason="US100 2023-11..2023-12 not fetched")
def test_real_data_us100_labels():
    from ict_engine.data.dukascopy import load
    bars = load("US100", date(2023, 11, 1), date(2023, 12, 31))
    recs = label_days(bars)
    assert len(recs) >= 15
    k, n = base_rate(recs)
    assert 0 < k < n
    assert {r.outcome for r in recs} <= {"bull_hit", "bear_hit", "none", "ambiguous"}
    # spot-check the eval's calls equal build_context's for a few days
    for r in recs[::7]:
        assert r.calls == {k: v[0] for k, v in build_context(bars, r.day).biases.items()}
