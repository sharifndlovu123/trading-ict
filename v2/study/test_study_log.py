"""The study log records what he saved and what changed between saves. Hand-built saves, no real chart."""
import json

from study_log import build, changes, entries, name, page, where


def mark(uid, **kw):
    return {"uid": uid, "shape": "level", "kind": "BOS", "tf": "t1", "price": 10.0, "t0": 3600, "t1": None, "by": "S"} | kw


def save(at, asset, marks, tf="t1", **kw):
    return {"saved": at, "asset": asset, "tf": tf, "marks": marks, "notes": [], "note": "", "chart_time": None} | kw


def test_a_change_is_told_as_added_removed_or_changed_by_the_marks_id():
    a, b, c = mark("a"), mark("b", price=20.0), mark("c", price=30.0)
    got = changes([a, b], [mark("a"), mark("b", price=21.0), c])
    assert got["added"] == [c] and got["removed"] == []
    assert got["changed"] == [(b, mark("b", price=21.0))]
    assert changes([a, b], [a]) == {"added": [], "removed": [b], "changed": []}
    assert changes([a], [dict(a)]) == {"added": [], "removed": [], "changed": []}          # the same mark saved again is no change
    assert changes([mark("a")], [mark("a", kind="level behind")])["changed"]              # renamed is a change


def test_each_instrument_has_its_own_log_in_order_and_the_first_save_is_all_added():
    saves = [save(100, "AAA", [mark("a")]), save(200, "BBB", [mark("x")]), save(300, "AAA", [mark("a"), mark("b", price=5.0)])]
    got = entries(saves, [{"saved": 250, "asset": "AAA", "tf": "t1", "text": "watching this", "kind": "learn"}])
    assert set(got) == {"AAA", "BBB"} and [e["kind"] for e in got["AAA"]] == ["save", "note", "save"]
    assert got["AAA"][0]["added"] == [mark("a")] and got["AAA"][2]["added"] == [mark("b", price=5.0)]
    assert got["BBB"][0]["added"] == [mark("x")]                                           # one instrument's marks never show as another's change


def test_a_study_started_later_compares_its_first_save_with_what_was_there_before():
    saves = [save(100, "AAA", [mark("a")]), save(300, "AAA", [mark("a"), mark("b", price=5.0)])]
    got = entries(saves, [{"saved": 50, "asset": "AAA", "tf": "t1", "text": "old", "kind": "learn"}], since=200)
    assert len(got["AAA"]) == 1 and got["AAA"][0]["added"] == [mark("b", price=5.0)]
    assert entries(saves, [], since=1000) == {}


def test_only_his_marks_are_logged():
    got = entries([save(100, "AAA", [mark("a"), mark("c", by="C")])], [])
    assert got["AAA"][0]["marks"] == [mark("a")]


def test_a_mark_is_named_and_placed_in_words_at_any_price_scale():
    assert name(mark("a", kind="BISI", tf="1W")) == "[BISI 1W]"
    assert where(mark("a", price=1.09545)) == "level at 1.09545, from 01 Jan 1970 01:00"
    assert where(mark("a", shape="zone", bottom=26000.0, top=26250.5, t1=7200)) == "zone 26,000 to 26,250.5, from 01 Jan 1970 01:00 to 01 Jan 1970 02:00"


def test_the_log_is_written_per_instrument_with_an_index_and_rebuilding_gives_the_same(tmp_path):
    s, n, out = tmp_path / "saves.jsonl", tmp_path / "notes.jsonl", tmp_path / "logs"
    s.write_text("\n".join(json.dumps(x) for x in [save(100, "AAA", [mark("a")]), save(90000, "AAA", [mark("a", price=11.0)]), save(200, "BBB", [])]) + "\n")
    assert build(s, n, out) == {"AAA": 2, "BBB": 1}
    text = (out / "AAA.md").read_text()
    assert "added [BOS t1]: level at 10" in text and "changed [BOS t1]: level at 10" in text and "level at 11" in text
    assert text.count("## ") == 2                                                          # two days, two headings
    assert "nothing changed" not in text and "| [AAA](AAA.md) | 2 |" in (out / "README.md").read_text()
    first = {f.name: f.read_text() for f in out.iterdir()}
    build(s, n, out)
    assert {f.name: f.read_text() for f in out.iterdir()} == first
    assert page("ZZZ", []).startswith("# ZZZ: study log")
