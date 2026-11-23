"""The tables: counts are right, a share is only of calls that resolved, and the nearer split is kept."""
import json

import pandas as pd

import pytest

from tables import add_review, call_marks, check, count, nearer_side, pick, picture, reviews, stories, tables


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


# ---- the short list he goes through on the chart, and what he says about each call
def merged_row(i, **kw):
    return row(id=f"m{i}", kind="merged", asset="US100", tf="1D", moment=1000 + i * 30 * 86400, merge="into area", outcome="undone", played="ended",
               own_side="bear", above="bull", what="sellside", whose_tf="1D") | kw


def bias_row(i, **kw):
    return row(id=f"b{i}", kind="bias", asset="US100", tf="1D", moment=1000 + i * 30 * 86400, story="flipped", zones=1, zones_failed=1,
               zones_reached=1, story_hours=5.0, story_events="[]", above="bull") | kw


def test_the_check_list_is_short_a_mix_of_how_biases_went_and_only_what_he_trades():
    kinds = ("straight", "deeper", "flipped, areas left", "flipped")
    rows = [bias_row(i, asset=a, story=s) for i, (a, s) in enumerate((a, s) for _ in range(8) for a in ("US100", "US500", "US30", "ELSE") for s in kinds)]
    got = check(frame(*rows, row()))
    assert len(got) == 10 and {c["story"] for c in got} == set(kinds)
    assert "ELSE" not in {c["asset"] for c in got} and len({c["asset"] for c in got}) == 3
    assert check(frame(*rows)) == got                                    # the same list every time it is asked for
    assert check(frame(*[bias_row(i, zones=0) for i in range(5)])) == []  # a bias with no zone to trade from is not shown


def test_the_check_list_does_not_show_one_stretch_of_market_twice_and_is_empty_without_stories():
    close_together = [bias_row(i, moment=1000 + i * 86400) for i in range(8)]
    assert len(check(frame(*close_together))) == 1
    assert check(frame(row(), row())) == [] and check(pd.DataFrame()) == []


def test_biases_are_counted_by_how_they_went_and_not_as_hit_or_miss():
    rows = [bias_row(1, story="straight", zones_failed=0), bias_row(2, story="deeper"), bias_row(3, story="deeper"),
            bias_row(4, story="flipped"), bias_row(5, story="open", story_hours=None), bias_row(6, story=None)]
    got = stories(frame(*rows), ["tf"])[0]
    assert (got["biases"], got["straight"], got["deeper"], got["flipped"], got["open"]) == (5, 1, 2, 1, 1)
    assert got["zone_failed"] == 4 and stories(frame(row()), ["tf"]) == []


def test_what_he_says_about_a_call_is_added_and_the_latest_is_what_shows(tmp_path):
    f = tmp_path / "reviews.jsonl"
    assert reviews(f) == {}
    add_review(f, "m1", "wrong", "it missed the weekly", 10.0)
    add_review(f, "m2", "right", "", 11.0)
    add_review(f, "m1", "not sure", "looking again", 12.0)
    assert reviews(f)["m1"]["verdict"] == "not sure" and reviews(f)["m2"]["verdict"] == "right"
    assert len(f.read_text().splitlines()) == 3                          # nothing he said is ever overwritten
    with pytest.raises(ValueError):
        add_review(f, "m1", "maybe", "", 13.0)


# ---- a call shows what EVERY timeframe was reading, not only its own ("we don't see it, we just see the smaller portion")
def a_ladder():
    high = {"side": "bull", "behind": 60.0, "ahead": 150.0, "buyside": 130.0, "sellside": 80.0, "imbalance_above": None,
            "imbalance_below": (84.0, 88.0, "BISI"), "inside": None,
            "when": {"behind": 100, "ahead": 200, "buyside": 300, "sellside": 400, "imbalance_above": None, "imbalance_below": 500, "inside": None}}
    low = {"side": "bear", "behind": 110.0, "ahead": 80.0, "buyside": 110.0, "sellside": 95.0, "imbalance_above": (105.0, 107.0, "BISI"),
           "imbalance_below": None, "inside": (99.0, 101.0, "SIBI"),
           "when": {"behind": 700, "ahead": 710, "buyside": 720, "sellside": 730, "imbalance_above": 740, "imbalance_below": None, "inside": 750}}
    return {"t3": high, "t2": None, "t1": low}


def test_a_call_draws_and_says_what_every_timeframe_was_reading():
    got = call_marks(merged_row(1, tf="t1", side="bear", target=95.0, moment=1000), a_ladder())
    assert got["bias"] == {"t3": "bull", "t1": "bear"}                   # every timeframe that has a bias, not only the call's
    upper = {(m["kind"], m.get("price", m.get("top"))) for m in got["marks"] if m["tf"] == "t3"}
    assert upper == {("level behind", 60.0), ("level ahead", 150.0), ("buyside", 130.0), ("sellside", 80.0), ("BISI", 88.0)}
    assert [line.split(":")[0] for line in got["ladder"]] == ["t3", "t2", "t1"]         # highest first
    assert "bull" in got["ladder"][0] and "[BISI t3]" in got["ladder"][0] and "no bias" in got["ladder"][1]
    assert "inside an imbalance" in got["ladder"][2] and any("top to bottom" in s for s in got["interesting"])


def test_every_mark_of_a_call_starts_at_the_candle_that_made_it_and_ends_at_the_moment():
    """Nothing floats: a gap is drawn from its own candle, a level from the candle that made the high or low."""
    got = call_marks(merged_row(1, tf="t1", side="bear", target=95.0, moment=1000), a_ladder())
    spans = {(m["kind"], m["tf"]): (m["t0"], m["t1"]) for m in got["marks"] if m["shape"] != "vline"}
    assert spans[("BISI", "t3")] == (500, 1000) and spans[("buyside", "t3")] == (300, 1000) and spans[("level behind", "t1")] == (700, 1000)
    assert spans[("SIBI", "t1")] == (750, 1000) and spans[("BISI", "t1")] == (740, 1000)
    keys = [(m["kind"], m["tf"], m.get("price"), m.get("top")) for m in got["marks"]]
    assert len(keys) == len(set(keys))                                   # and nothing is drawn twice


def test_a_call_without_the_other_timeframes_is_drawn_as_before():
    alone = call_marks(merged_row(1, tf="t1", side="bear", target=95.0))
    assert alone["bias"] == {"t1": "bear"} and alone["ladder"] == [] and any(m["kind"] == "sellside" for m in alone["marks"])


def test_the_share_whose_bias_played_out_is_counted_beside_the_exact_count():
    """His way of judging a call is kept apart from the exact-target count; a call still open is in neither share."""
    df = frame(row(id="a", outcome="undone", played="true"), row(id="b", outcome="undone", played="true"),
               row(id="c", outcome="true", played="ended"), row(id="d", outcome="undone", played="open"))
    got = count(df, ["tf"])[0]
    assert (got["played"], got["played_n"], got["played_share"]) == (2, 3, 0.667)
    assert got["true_share"] == 0.25
    assert count(frame(row(id="a")), ["tf"])[0]["played_share"] is None      # results from before this count existed
