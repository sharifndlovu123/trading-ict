"""The model-free watcher (research/scripts/hunt_watch.py): events fire once, only at what was marked."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import hunt_watch as hw  # noqa: E402


def doc(last, bars, adr=100.0):
    c = [{"time": 300 * i, "open": o, "high": h, "low": lo, "close": cl} for i, (o, h, lo, cl) in enumerate(bars)]
    return {"assets": {"US100": {"last": last, "adr": adr, "candles": {"5m": c}}}}


OV = {"at": "prep 1", "US100": {"marks": [
    {"kind": "Asia high", "price": 110.0}, {"kind": "FVG", "tf": "1h", "top": 108.0, "bottom": 106.0},
    {"kind": "displacement", "p0": 120.0, "p1": 100.0}]}}


def test_a_level_fires_once_when_price_trades_through_it_and_a_zone_when_entered():
    st = {}
    assert hw.events(doc(104.0, [(103, 104.5, 103, 104), (104, 104.5, 103.5, 104)]), OV, st) == []     # below both
    e = hw.events(doc(106.5, [(104, 104.5, 103.5, 104), (104, 106.8, 104, 106.5)]), OV, st)
    assert len(e) == 1 and "entered 1h FVG 106.0–108.0" in e[0]
    assert hw.events(doc(107.0, [(104, 106.8, 104, 106.5), (106.5, 107.2, 106.4, 107)]), OV, st) == []  # the zone fires once
    e = hw.events(doc(109.5, [(106.5, 107.2, 106.4, 107), (107, 110.2, 107, 109.5)]), OV, st)           # a wick through 110
    assert len(e) == 1 and "traded through Asia high 110.0 (from below; a wick so far" in e[0]
    assert hw.events(doc(111.0, [(107, 110.2, 107, 109.5), (109.5, 111.2, 109.4, 111)]), OV, st) == []   # that candle closed back under: still only a wick
    e = hw.events(doc(111.5, [(109.5, 111.2, 109.4, 111), (111, 111.6, 110.9, 111.5)]), OV, st)          # now a 5m candle has closed above it
    assert len(e) == 1 and "CLOSED above Asia high 110.0" in e[0] and "a body" in e[0]
    assert hw.events(doc(111.6, [(109.5, 111.2, 109.4, 111), (111, 111.7, 110.9, 111.6)]), OV, st) == []   # said once


def test_a_hard_push_is_reported_once_and_a_new_prep_resets_everything():
    st = {}
    bars = [(100, 100.5, 91, 91.5), (91.5, 92, 91, 91.8)]                    # the closed candle fell 8.5 = 0.085 ADR
    e = hw.events(doc(91.8, bars), {"at": "p", "US100": {"marks": []}}, st)
    assert len(e) == 1 and "hard 5m push down" in e[0]
    assert hw.events(doc(91.9, bars), {"at": "p", "US100": {"marks": []}}, st) == []
    quiet = [(100, 100.5, 99, 99.5), (99.5, 100, 99.2, 99.8)]                # 0.5 = 0.005 ADR: nothing
    assert hw.events(doc(99.8, quiet), {"at": "p", "US100": {"marks": []}}, st) == []
    st2 = {}
    hw.events(doc(109.5, [(107, 110.2, 107, 109.5), (109.5, 109.8, 109.2, 109.5)]), OV, st2)             # starts below 110
    hw.events(doc(110.5, [(109.5, 109.8, 109.2, 109.5), (109.5, 110.6, 109.4, 110.5)]), OV, st2)
    again = hw.events(doc(109.0, [(109.5, 110.6, 109.4, 110.5), (110.5, 110.6, 108.9, 109)]), {**OV, "at": "prep 2"}, st2)
    assert any("Asia high" in x for x in again) is False and any("FVG" in x for x in again) is False     # new prep, 109 is between them
    back = hw.events(doc(110.4, [(110.5, 110.6, 108.9, 109), (109, 110.5, 108.9, 110.4)]), {**OV, "at": "prep 2"}, st2)
    assert any("traded through Asia high" in x for x in back)                                           # fires again after the reset


def test_the_checker_summary_and_its_reply():
    d = doc(104.0, [(103, 104.5, 103, 104), (104, 104.5, 103.5, 104)])
    d["now"] = "Tue 2026-11-17 02:30"
    d["assets"]["US100"]["candles"].update({"15m": d["assets"]["US100"]["candles"]["5m"], "1h": []})
    text = hw.summary(d, {**OV, "US100": {**OV["US100"], "read": ["Sell on a raid of the Asia high."]}})
    assert "## US100: last 104.0" in text and "Asia high 110.0" in text and "FVG (106.0, 108.0)" in text
    assert "displacement" not in text and "Sell on a raid" in text and "00:05 o104" in text
    assert hw.parse_checker("OK") == [] and hw.parse_checker("ok\n") == []
    assert hw.parse_checker("ESCALATE: US500: two lows at 7,394\nOK") == ["ESCALATE: US500: two lows at 7,394"]


def test_a_requested_5m_order_block_is_reported_once_with_its_grade():
    ov = {"at": "p", "US100": {"marks": [], "watch_ob": {"side": "sell", "below": 110.0, "min_body": 50}}}
    # an up candle 100 → 102 (range 99.8–102.2: body 83%), engulfed by the next closed candle (close 99.5 < 100), then a forming bar
    bars = [(100, 102.2, 99.8, 102), (102, 102.1, 99.4, 99.5), (99.5, 99.7, 99.3, 99.6)]
    st = {}
    e = hw.events(doc(99.6, bars, adr=1000.0), ov, st)
    assert len(e) == 1 and "5m sell order block formed (clean, body 83%): 100–102" in e[0]
    assert hw.events(doc(99.6, bars, adr=1000.0), ov, st) == []
    wick = [(100, 104, 96, 100.5), (100.5, 100.6, 99, 99.5), (99.5, 99.7, 99.3, 99.6)]            # body 6%: dim
    assert "(dim, body 6%)" in hw.events(doc(99.6, wick, adr=1000.0), ov, {})[0]
    high = [(111, 113.2, 110.8, 113), (113, 113.1, 110.4, 110.5), (110.5, 110.7, 110.3, 110.6)]  # above the limit: not asked for
    assert hw.events(doc(110.6, high, adr=1000.0), ov, {}) == []


def test_conditions_tell_a_clean_move_from_chop():
    up = [{"open": 100 + i, "close": 101 + i, "high": 101 + i, "low": 100 + i} for i in range(30)]
    chop = [{"open": 100 + (i % 2), "close": 101 - (i % 2), "high": 101, "low": 100} for i in range(30)]
    assert hw.conditions(up)["label"] == "clean" and hw.conditions(up)["score"] == 1.0
    assert hw.conditions(chop)["label"] == "choppy"
    assert hw.conditions(up[:3])["label"] == "unknown"


def test_pools_keep_only_equal_highs_that_were_not_taken():
    def bar(t, hi, lo):
        return {"time": t, "open": lo, "close": hi, "high": hi, "low": lo}
    c = [bar(0, 10, 5), bar(1, 20, 6), bar(2, 12, 7), bar(3, 20.1, 8), bar(4, 13, 9), bar(5, 14, 9.5)]
    assert hw.pools(c, adr=100)["highs"] == [{"from": 20, "to": 20.1, "count": 2}]
    assert hw.pools(c + [bar(6, 25, 10)], adr=100)["highs"] == []          # a later candle traded beyond them: eaten


def test_checker_state_lines_are_kept_apart_from_escalations():
    reply = "STATE: US100: choppy; eaten: the equal lows; created: none\nSTATE US30: clean; eaten: none; created: none\nOK"
    assert hw.parse_state(reply) == ["US100: choppy; eaten: the equal lows; created: none", "US30: clean; eaten: none; created: none"]
    assert hw.parse_checker(reply) == []


def _idea_doc(last, m1):
    c1 = [{"time": 60 * i, "open": o, "high": h, "low": lo, "close": cl} for i, (o, h, lo, cl) in enumerate(m1)]
    return {"assets": {"US100": {"last": last, "adr": 100.0, "candles": {"5m": [{"time": 0, "open": last, "high": last, "low": last, "close": last}], "1m": c1}}}}


IDEA = {"at": "p", "US100": {"marks": [], "idea": {"side": "sell", "goal_name": "London low", "goal": 90.0, "entry": [104.0, 106.0], "stop": 108.0, "cancel": 95.0}}}


def test_the_idea_is_cancelled_by_a_close_not_by_a_wick():
    st = {}
    e = hw.events(_idea_doc(96.0, [(100, 100, 97, 97.5), (97.5, 97.5, 94.5, 96.0)]), IDEA, st)          # the forming candle wicks under 95
    assert len(e) == 1 and "a wick beyond the cancel level 95.0, no close" in e[0]
    e = hw.events(_idea_doc(96.2, [(97.5, 97.5, 94.5, 96.0), (96.0, 96.5, 95.8, 96.2)]), IDEA, st)      # it closed back above: nothing new
    assert e == []
    e = hw.events(_idea_doc(94.0, [(96.0, 96.5, 94.2, 94.4), (94.4, 94.6, 93.9, 94.0)]), IDEA, st)      # a 1m candle closed below 95
    assert len(e) == 1 and "CLOSED beyond the cancel level 95.0" in e[0]
    assert hw.events(_idea_doc(94.1, [(96.0, 96.5, 94.2, 94.4), (94.4, 94.6, 93.9, 94.1)]), IDEA, st) == []


def test_the_idea_reports_the_entry_and_the_goal_closing_through():
    st = {}
    e = hw.events(_idea_doc(104.5, [(100, 101, 99, 100.5), (100.5, 104.6, 100.4, 104.5)]), IDEA, st)
    assert len(e) == 1 and "price is at the entry" in e[0]
    e = hw.events(_idea_doc(89.0, [(92, 92, 89.5, 89.6), (89.6, 89.8, 88.9, 89.0)]), IDEA, st)
    assert any("goal is closed through" in x for x in e)


def test_time_is_named_against_his_windows():
    assert hw.window("09:42") == "inside the 09:20–10:00 window"
    assert hw.window("07:10").startswith("between windows (next 08:20)")
    assert hw.window("15:00") == "after the last window"
