"""Sanity checks on the golden cases — a bad reference makes every score wrong."""

from pathlib import Path

import pytest

from ict_engine.eval import compare, load_cases

CASES = load_cases(Path(__file__).parent / "cases" / "ict_live_exec.yaml")


def test_ids_unique_and_weekdays():
    assert len({c.id for c in CASES}) == len(CASES)
    assert all(c.trade.day.weekday() < 5 for c in CASES)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_levels_on_the_correct_side(case):
    t = case.trade
    sign = 1 if t.side == "long" else -1
    if t.entry_price is not None and t.stop is not None:
        assert sign * (t.entry_price - t.stop) > 0, "stop on wrong side of entry"
    if t.entry_price is not None and t.tp1 is not None:
        assert sign * (t.tp1 - t.entry_price) > 0, "TP1 on wrong side of entry"
    if t.tp1 is not None and t.final_target is not None:
        assert sign * (t.final_target - t.tp1) >= 0, "final target before TP1"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_each_case_matches_itself(case):
    c = compare(case.trade, case.trade, **case.compare_kwargs())
    assert c.verdict == "match" and c.score == 1.0
