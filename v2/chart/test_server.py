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
