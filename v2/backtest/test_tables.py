"""The tables: counts are right, a share is only of calls that resolved, and the nearer split is kept."""
import json

import pandas as pd

from tables import call_marks, count, nearer_side, pick, picture, tables


def row(**kw):
    base = {"id": "x", "asset": "A", "tf": "t1", "kind": "liquidity", "moment": 1000, "year": 2001, "made_in": "london", "side": "bull",
            "with_above": True, "nearer": "target", "outcome": "true", "hours": 4.0, "resolved_hour": 9, "buyside": 110.0, "sellside": 95.0,
            "behind": 90.0, "ahead": 120.0, "imbalance": json.dumps([105.0, 107.0, "BISI"])}
    return base | kw


def frame(*rows):
    return pd.DataFrame(list(rows))


def test_a_share_is_of_the_calls_that_resolved_and_the_rest_are_counted_beside_it():
    df = frame(row(), row(), row(outcome="undone"), row(outcome="unresolved"), row(outcome="same candle"))
    (r,) = count(df, ["kind"])
    assert (r["calls"], r["true"], r["undone"], r["other"]) == (5, 2, 1, 2) and r["true_share"] == round(2 / 3, 3)


def test_no_share_is_given_when_nothing_resolved():
    (r,) = count(frame(row(outcome="open"), row(outcome="unresolved")), ["kind"])
    assert r["true_share"] is None and r["calls"] == 2


def test_results_are_split_by_which_was_nearer():
    df = frame(row(nearer="target"), row(nearer="target"), row(nearer="undo", outcome="undone"))
    got = {r["nearer"]: r for r in count(df, ["kind", "nearer"])}
    assert got["target"]["true_share"] == 1.0 and got["undo"]["true_share"] == 0.0


def test_what_the_bias_adds_is_the_nearer_side_going_first_for_it_and_against_it():
    """The nearer side goes first 3 times in 4 when it is the bias's side, and 2 times in 4 when it is the other side."""
    df = frame(*[row(nearer="target", outcome=o) for o in ("true", "true", "true", "undone")],
               *[row(nearer="undo", outcome=o) for o in ("undone", "undone", "true", "true")])
    (r,) = nearer_side(df)
    assert (r["nearer_was_bias_side"], r["nearer_went_first_share"]) == (4, 0.75)
    assert (r["nearer_was_other_side"], r["nearer_went_first_share_other"]) == (4, 0.5)


def test_calls_can_be_picked_to_look_at_newest_first():
    df = frame(row(id="old", moment=1), row(id="new", moment=9), row(id="other", moment=5, tf="t2"))
    assert [c["id"] for c in pick(df, tf="t1")] == ["new", "old"]


def test_a_call_becomes_marks_dated_at_its_own_moment_and_never_after():
    m = call_marks(row())
    assert m["moment"] == 1000 and all(x["t0"] <= 1000 for x in m["marks"])
    assert {x["kind"] for x in m["marks"]} >= {"level behind", "level ahead", "buyside", "sellside", "BISI"}


def test_the_whole_set_of_tables_is_made_and_an_empty_run_is_not_an_error():
    assert tables(pd.DataFrame()) == {"calls": 0}
    t = tables(frame(row(), row(outcome="undone", nearer="undo")))
    assert t["calls"] == 2 and t["by_kind"] and t["by_year"] and t["by_instrument"]


def test_the_picture_lists_the_timeframes_highest_first_with_what_the_bias_adds_on_each():
    """On the higher timeframe here the nearer side goes first 4 in 4 for the bias and 1 in 2 against it; on the lower
    one it is 1 in 2 both ways, so the bias adds a half above and nothing below."""
    hi = [row(tf="up", nearer="target") for _ in range(4)] + [row(tf="up", nearer="undo", outcome=o) for o in ("undone", "true")]
    lo = [row(tf="down", nearer="target", outcome=o) for o in ("true", "undone")] + [row(tf="down", nearer="undo", outcome=o) for o in ("undone", "true")]
    got = picture(frame(*lo, *hi), ["up", "down", "not there"])
    assert [r["tf"] for r in got] == ["up", "down"]
    assert got[0]["bias_adds"] == 0.5 and got[1]["bias_adds"] == 0.0
    assert got[0]["liquidity_target"] == 1.0 and got[0]["liquidity_target_n"] == 4
