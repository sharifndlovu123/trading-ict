"""The chart server's own logic (who may look, reading the password, the marks file). No network."""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server  # noqa: E402


def basic(password, user="anyone"):
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def test_this_machine_never_needs_a_password():
    assert server.allowed("127.0.0.1", None, "secret") and server.allowed("::1", None, None)


def test_another_device_needs_the_password_and_any_user_name_will_do():
    assert server.allowed("192.168.1.20", basic("secret", user="phone"), "secret")
    assert not server.allowed("192.168.1.20", basic("wrong"), "secret")
    assert not server.allowed("192.168.1.20", None, "secret")
    assert not server.allowed("192.168.1.20", "Basic not-base64!!", "secret")
    assert not server.allowed("192.168.1.20", basic("anything"), None)           # no password set: nobody outside gets in


def test_the_password_is_read_from_the_environment_or_a_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('OTHER=1\nPAGE_PW="from-file"\n')
    monkeypatch.delenv("PAGE_PW", raising=False)
    assert server.read_env(env, "PAGE_PW") == "from-file"
    monkeypatch.setenv("PAGE_PW", "from-env")
    assert server.read_env(env, "PAGE_PW") == "from-env"
    assert server.read_env(tmp_path / "missing", "NOT_SET_ANYWHERE") is None


def test_an_instrument_with_no_marks_gets_an_empty_chart(tmp_path, monkeypatch):
    f = tmp_path / "marks.json"
    monkeypatch.setattr(server, "MARKS", f)
    assert server.marks_for("ANY") == {"at": "", "marks": [], "read": []}
    f.write_text(json.dumps({"at": "now", "ANY": {"marks": [{"shape": "level", "price": 1}], "read": ["one line"]}}))
    got = server.marks_for("ANY")
    assert got["at"] == "now" and got["marks"][0]["price"] == 1 and got["read"] == ["one line"]
    assert server.marks_for("OTHER")["marks"] == []


def test_the_page_is_only_served_under_an_address_or_localhost():
    assert server.host_ok("127.0.0.1:8776") and server.host_ok("192.168.1.20:8776") and server.host_ok("localhost:8776") and server.host_ok("[::1]:8776")
    assert not server.host_ok("evil.example:8776") and not server.host_ok(None) and not server.host_ok("")
    assert server.host_ok("desk.local:8776", extra=("desk.local",))               # a name he allowed when starting it


def test_a_save_must_come_from_the_page_itself():
    assert server.same_origin(None, "127.0.0.1:8776")                              # not a cross-site browser request
    assert server.same_origin("http://127.0.0.1:8776", "127.0.0.1:8776")
    assert server.same_origin("http://192.168.1.20:8776", "192.168.1.20:8776")
    assert not server.same_origin("https://evil.example", "127.0.0.1:8776")
    assert not server.same_origin("http://127.0.0.1:9999", "127.0.0.1:8776")       # another page on this machine
    assert not server.same_origin("null", "127.0.0.1:8776")


def test_his_notes_are_kept_newest_first_with_what_the_chart_showed(tmp_path):
    f = tmp_path / "notes.jsonl"
    assert server.list_notes(f) == []
    a = server.add_note(f, {"kind": "learn", "text": "  first note  ", "asset": "ANY", "tf": "1D", "chart_time": 123}, now=1000.0)
    b = server.add_note(f, {"kind": "hunt", "text": "second note", "asset": "ANY", "tf": "1h"}, now=2000.0)
    assert a["text"] == "first note" and a["kind"] == "learn" and a["chart_time"] == 123 and b["chart_time"] is None
    assert [n["text"] for n in server.list_notes(f)] == ["second note", "first note"]
    assert server.add_note(f, {"kind": "something else", "text": "x"}, now=3000.0)["kind"] == "learn"      # only learn or hunt


def test_an_empty_note_is_refused_and_a_removed_note_is_not_listed(tmp_path):
    import pytest
    f = tmp_path / "notes.jsonl"
    with pytest.raises(ValueError):
        server.add_note(f, {"kind": "hunt", "text": "   "}, now=1.0)
    a = server.add_note(f, {"kind": "hunt", "text": "keep"}, now=1.0)
    b = server.add_note(f, {"kind": "hunt", "text": "drop"}, now=2.0)
    server.remove_note(f, b["id"], now=3.0)
    assert [n["id"] for n in server.list_notes(f)] == [a["id"]]
    assert len(f.read_text().splitlines()) == 3                                     # nothing is rewritten: the removal is one more line


def test_the_mode_is_learn_hunt_or_nothing_and_says_who_set_it(tmp_path):
    import pytest
    f = tmp_path / "mode.json"
    assert server.get_mode(f) == {"mode": "", "by": "", "at": 0}                    # no file: no session
    assert server.set_mode(f, "learn", "Claude", now=50.0) == {"mode": "learn", "by": "Claude", "at": 50}
    assert server.get_mode(f)["mode"] == "learn"
    server.set_mode(f, "hunt", "Sharif", now=60.0)
    assert server.get_mode(f) == {"mode": "hunt", "by": "Sharif", "at": 60}
    server.set_mode(f, "", "Sharif", now=70.0)
    assert server.get_mode(f)["mode"] == ""
    with pytest.raises(ValueError):
        server.set_mode(f, "backtest", "Claude", now=80.0)
    f.write_text("not json")
    assert server.get_mode(f)["mode"] == ""                                         # a broken file never shows a wrong mode


def test_live_downloads_only_while_switched_on_and_a_page_is_asking():
    st = {"on": False, "assets": [], "beat": 0.0, "fetched": {}, "added": {}, "error": ""}
    assert server.live_due(st, now=1000.0) == []                                    # off: nothing is downloaded
    got = server.live_set(st, True, ["UK100", "DE40", "UK100", "NOT-AN-INSTRUMENT"], now=1000.0)
    assert got["on"] and got["assets"] == ["UK100", "DE40"]                         # no repeats, only instruments we have
    assert server.live_due(st, now=1001.0) == ["UK100", "DE40"]                     # never fetched: both are due
    st["fetched"] = {"UK100": 1001.0, "DE40": 1001.0}
    assert server.live_due(st, now=1030.0) == []                                    # fetched half a minute ago: not yet
    assert server.live_due(st, now=1001.0 + server.LIVE_EVERY) == ["UK100", "DE40"]
    assert server.live_due(st, now=1000.0 + server.LIVE_IDLE + 1) == []             # the page went away: stop on its own
    assert server.live_status(st, now=1000.0 + server.LIVE_IDLE + 1)["on"] is False
    server.live_set(st, False, [], now=2000.0)
    assert server.live_due(st, now=2001.0) == [] and st["assets"] == []


def test_the_equal_slider_uses_only_what_is_on_screen_or_to_its_left():
    def c(t, h, lo):
        return {"time": t, "open": lo + 1, "high": h, "low": lo, "close": h - 1}
    cs = [c(0, 104, 99), c(1, 110, 102), c(2, 107, 100), c(3, 110.3, 100), c(4, 105, 99), c(5, 140, 99), c(6, 120, 110)]
    seen = server.equal_in_view(cs, 0, 4, share=0.05)                              # the screen ends before the candle that ate the set
    assert [(g["side"], g["count"]) for g in seen["sets"]] == [("high", 2)] and seen["near"] > 0
    assert server.equal_in_view(cs, 0, 6, share=0.05)["sets"] == []                # with that candle on screen the set is gone
    assert server.equal_in_view(cs, 0, 4, share=0.0)["sets"] == []                 # a perfectly sharp eye sees no two highs as equal here
    assert server.equal_in_view(cs, 50, 60, share=0.05) == {"near": 0.0, "sets": []}   # nothing on screen
