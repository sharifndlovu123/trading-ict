"""The context check's own tests: concept folders made up in a temporary directory, never a real lesson."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("context_check", Path(__file__).resolve().parents[2] / ".claude/skills/context-check/check.py")
cc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cc)

LESSON = '''# Thing

Taught by Sharif on 3 Jan 2031.

- "This is the first thing he said about it, in his own words."
- "This is the second thing he said about it, also his words."
- "And a third sentence of his, so the lesson carries his voice."

Mine, not his: the wording of the tool.
'''
HEAD = "\n## Links\n\n| Comes to mind when | Then look for | Status |\n|---|---|---|\n"
GOOD = "| liquidity is swept and displacement follows | an imbalance left by that displacement, in an interesting area | stated by Sharif, 3 Jan 2031 |\n"


def concept(tmp_path, lesson=LESSON, rows=None):
    f = tmp_path / "09_thing"
    f.mkdir()
    (f / "lesson.md").write_text(lesson + (HEAD + "".join(rows) if rows is not None else ""))
    return f


def run(folder):
    return cc.check(folder, migration_text="| 09 | Thing | [x] |")


def test_a_link_in_his_words_with_a_status_passes(tmp_path):
    fail, judge, ok = run(concept(tmp_path, rows=[GOOD]))
    assert fail == [] and any("1 link" in x for x in ok)


def test_a_lesson_with_no_links_is_reported_not_failed(tmp_path):
    fail, judge, ok = run(concept(tmp_path))
    assert fail == [] and any("no links yet" in x for x in judge + ok)


@pytest.mark.parametrize("copied", [
    "| price sweeps the low at 8:21 | an imbalance | stated by Sharif, 3 Jan 2031 |\n",                 # a clock time
    "| price sweeps 26,010 | an imbalance | stated by Sharif, 3 Jan 2031 |\n",                          # a price
    "| liquidity is swept on the 5m | an imbalance | stated by Sharif, 3 Jan 2031 |\n",                 # a named timeframe
    "| liquidity is swept on the DAX | an imbalance | stated by Sharif, 3 Jan 2031 |\n",                # an instrument
])
def test_a_link_that_carries_the_example_fails(tmp_path, copied):
    fail, _, _ = run(concept(tmp_path, rows=[copied]))
    assert len(fail) == 1 and "link" in fail[0]


def test_a_link_must_say_whether_he_stated_it_or_claude_noticed_it(tmp_path):
    fail, _, _ = run(concept(tmp_path, rows=["| liquidity is swept | an imbalance | confirmed |\n"]))
    assert len(fail) == 1 and "status" in fail[0]
    mine = "| liquidity is swept twice | a deeper imbalance | noticed by Claude, unconfirmed |\n"
    (tmp_path / "b").mkdir()
    fail, judge, _ = run(concept(tmp_path / "b", rows=[GOOD, mine]))
    assert fail == [] and any("unconfirmed" in x for x in judge)        # allowed, but pointed out: not to be used yet


def test_a_flat_statement_about_price_is_flagged_in_a_lesson_and_fails_in_a_link(tmp_path):
    flat = LESSON + "\nPrice is selling into the low.\n"
    fail, judge, _ = run(concept(tmp_path, lesson=flat))
    assert fail == [] and any("price is selling" in x.lower() for x in judge)
    (tmp_path / "c").mkdir()
    fail, _, _ = run(concept(tmp_path / "c", rows=["| price is buying | an imbalance | stated by Sharif, 3 Jan 2031 |\n"]))
    assert len(fail) == 1 and "fixed statement" in fail[0]


def test_his_own_quote_is_never_flagged(tmp_path):
    quoted = LESSON + '\n- "Don\'t ever say price is buying nor selling."\n'
    fail, judge, _ = run(concept(tmp_path, lesson=quoted))
    assert fail == [] and not any("price is buying" in x.lower() for x in judge)


def test_reading_the_links_table():
    rows = cc.links(LESSON + HEAD + GOOD)
    assert rows == [{"when": "liquidity is swept and displacement follows", "then": "an imbalance left by that displacement, in an interesting area",
                     "status": "stated by Sharif, 3 Jan 2031"}]
    assert cc.links(LESSON) is None                                     # no Links section at all
    assert cc.links(LESSON + HEAD) == []                                # a section with nothing in it yet


def test_hunt_notes_are_scanned_for_flat_statements(tmp_path):
    n = tmp_path / "2031-01-03.md"
    n.write_text('# Hunt notes\n\n- He: "this is missing, look at the low again."\n- I said the market is buying here.\n')
    assert any("is buying" in x.lower() for x in cc.check_notes(n))
    n.write_text('# Hunt notes\n\n- He: "this is missing, look at the low again."\n- An interesting low sits under the hourly range.\n')
    assert cc.check_notes(n) == []


CLOCK_TOOL = "def window(minute):\n    return 60 <= minute < 120\n"
PRICE_TOOL = "def top(c):\n    return max(x['high'] for x in c)\n"
FIVE = "".join(f"def test_{i}():\n    assert True\n" for i in range(5))
SEASONS = "def test_the_clock_in_summer_and_in_winter():\n    assert True\n"


def with_tool(tmp_path, tool, tests):
    f = concept(tmp_path)
    (f / "thing.py").write_text(tool)
    (f / "test_thing.py").write_text(tests)
    return f


def test_a_tool_that_reads_only_the_clock_needs_a_summer_and_winter_test_not_price_scales(tmp_path):
    fail, _, ok = run(with_tool(tmp_path, CLOCK_TOOL, FIVE + SEASONS))
    assert fail == [] and any("clock only" in x for x in ok)


def test_a_clock_tool_without_a_summer_and_winter_test_fails(tmp_path):
    fail, _, _ = run(with_tool(tmp_path, CLOCK_TOOL, FIVE))
    assert any("summer and in winter" in x for x in fail)


def test_a_tool_that_reads_prices_still_needs_price_scales_and_no_look_ahead(tmp_path):
    """The clock exception must not become a way round the candle tests."""
    fail, _, _ = run(with_tool(tmp_path, PRICE_TOOL, FIVE + SEASONS))
    assert any("price scales" in x for x in fail) and any("no-look-ahead" in x for x in fail)
