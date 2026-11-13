from dataclasses import replace
from datetime import date, time

from ict_engine.eval import TradeSnapshot, compare, match_day

REF = TradeSnapshot(
    day=date(2024, 1, 9), market="NQ", side="long",
    entry_time=time(11, 4), entry_price=16745.0, stop=16727.5,   # risk 17.5
    tp1=16796.0, pd_array="ifvg", pd_array_tf="1m",
    liquidity_taken=frozenset({"ssl"}), model="macro",
)


def test_identical_trade_is_a_perfect_match():
    c = compare(REF, REF)
    assert c.score == 1.0 and c.verdict == "match" and c.coverage == 1.0


def test_opposite_side_or_other_day_is_different():
    assert compare(replace(REF, side="short"), REF).score == 0.0
    assert compare(replace(REF, day=date(2024, 1, 10)), REF).verdict == "different"


def test_snowflake_close_but_not_equal_is_still_similar():
    # 6 min later, entry 0.3R higher, FVG instead of IFVG, 5m instead of 1m.
    cand = replace(REF, entry_time=time(11, 10), entry_price=16745.0 + 0.3 * 17.5,
                   stop=16725.0, pd_array="fvg", pd_array_tf="5m")
    c = compare(cand, REF)
    assert c.verdict in {"match", "similar"}, c
    assert 0.6 < c.score < 1.0


def test_far_away_trade_is_different():
    cand = replace(REF, entry_time=time(14, 30), entry_price=16900.0,
                   stop=16850.0, pd_array="ob", pd_array_tf="1h", model="silver_bullet",
                   liquidity_taken=frozenset({"bsl"}))
    assert compare(cand, REF).verdict == "different"


def test_missing_traits_are_dropped_not_penalised():
    ref_no_stop = replace(REF, stop=None)   # ICT's stop not drawn
    c = compare(REF, ref_no_stop, price_tol=10.0)
    assert c.score == 1.0
    assert c.coverage < 1.0                 # risk and tp1 could not be compared
    assert any("not comparable" in d for d in c.differences)


def test_price_offset_removes_feed_basis():
    cfd = replace(REF, entry_price=REF.entry_price + 40, stop=REF.stop + 40, tp1=REF.tp1 + 40)
    assert compare(cfd, REF).traits["entry"] < 0.01
    assert compare(cfd, REF, price_offset=40).traits["entry"] == 1.0


def test_entry_window_counts_any_time_inside():
    ref = replace(REF, entry_time=None, entry_window=(time(9, 33), time(9, 50)))
    assert compare(replace(REF, entry_time=time(9, 41)), ref).traits["time"] == 1.0


def test_match_day_picks_the_closest_candidate_and_lists_extras():
    near = replace(REF, entry_time=time(11, 6))
    other = replace(REF, entry_time=time(14, 5), entry_price=16900.0, stop=16880.0, tp1=16950.0)
    report = match_day([other, near], [("ref", REF, {})])
    idx, comp = report.best["ref"]
    assert idx == 1 and comp.verdict == "match"
    assert report.found() == ["ref"]
    assert report.unmatched_candidates == [0]
