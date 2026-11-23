"""The v2 chart: one small page that shows candles and marks.

    uv run python v2/chart/server.py                                              # this machine only
    uv run python v2/chart/server.py --host 0.0.0.0 --password-env LIVE_PAGE_PASSWORD   # other devices, with a password

Then http://127.0.0.1:8776/?asset=UK100&tf=1D

A display and nothing else. Claude's marks are read from `marks.json` beside this file; what Sharif draws and saves
is appended to `saves.jsonl`, and the notes he writes in the side panel to `notes.jsonl`. `mode.json` says whether a
learn session or a hunt is running; the page shows it across the top. Candles come from `data/bars/` (refresh them with `fetch.py`).
"""
from __future__ import annotations

import argparse
import base64
import hmac
import ipaddress
import json
import os
import sys
import threading
import time

import pandas as pd
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candles as cd  # noqa: E402
import fetch  # noqa: E402

sys.path.insert(0, str(HERE.parent / "concepts" / "02_liquidity"))
import liquidity  # noqa: E402     the concept's own tool: the chart only shows what it finds

sys.path.insert(0, str(HERE.parent / "study"))
import study_log  # noqa: E402     the study log is rebuilt whenever he saves or writes a note

sys.path.insert(0, str(HERE.parent / "backtest"))
import run as backtest_run  # noqa: E402    the runner: used here only to read every timeframe at the moment of one call
import tables as backtest  # noqa: E402     the tools backtest: its tables, and one call as marks for replay

MARKS, SAVES, PAGE, NOTES, MODE = HERE / "marks.json", HERE / "saves.jsonl", HERE / "page.html", HERE / "notes.jsonl", HERE / "mode.json"
REPLIES = HERE / "replies.jsonl"          # Claude's answers to his notes: Claude's file, so his notes file is never touched
MODES = ("learn", "hunt", "")          # "" = no session
STATIC = {"/marks.js": ("marks.js", "text/javascript; charset=utf-8")}
BACKTEST_PAGE = HERE.parent / "backtest" / "page.html"
CHECK_PAGE = HERE.parent / "backtest" / "check.html"
_calls: dict = {"stamp": None, "df": None}
_ladders: dict = {}
LAST = {"1m": 1500, "5m": 1500, "15m": 1500, "1h": 2000, "4h": 2000}      # how many candles of the small timeframes are sent
LOCAL = ("127.0.0.1", "::1", "::ffff:127.0.0.1")
_cache: dict[str, tuple] = {}


def read_env(path: Path, name: str) -> str | None:
    """A value from the environment, or from a KEY=VALUE file. Never printed."""
    if os.environ.get(name):
        return os.environ[name]
    if path.exists():
        for line in path.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name and v.strip():
                return v.strip().strip('"').strip("'")
    return None


def allowed(client: str, header: str | None, password: str | None) -> bool:
    """This machine always may. Another device must give the password (any user name) when one is set."""
    if client in LOCAL:
        return True
    if not password or not header or not header.startswith("Basic "):
        return False
    try:
        given = base64.b64decode(header[6:]).decode().partition(":")[2]
    except Exception:
        return False
    return hmac.compare_digest(given, password)


def host_ok(host: str | None, extra: tuple[str, ...] = ()) -> bool:
    """The page is reached by an address (127.0.0.1, 192.168.x.x) or as localhost. Any other name in the Host header
    is refused, so a web site cannot point its own name at this machine and talk to the page (DNS rebinding)."""
    if not host:
        return False
    name = host.rsplit(":", 1)[0] if host.count(":") == 1 else host.strip("[]").split("]")[0]
    if name.lower() in ("localhost",) + tuple(x.lower() for x in extra):
        return True
    try:
        ipaddress.ip_address(name)
        return True
    except ValueError:
        return False


def same_origin(origin: str | None, host: str | None) -> bool:
    """A save must come from the page itself. A browser sends Origin with a cross-site request; if it is there, it
    must be this page's own address. (No Origin: not a cross-site browser request.)"""
    if not origin:
        return True
    u = urlparse(origin)
    return u.scheme in ("http", "https") and u.netloc.lower() == (host or "").lower()


MAX_SAVE = 512 * 1024      # bytes: a save is a handful of marks and a note


def get_mode(path: Path) -> dict:
    """Which session is running: {"mode": "learn" | "hunt" | "", "by": who set it, "at": when}. The page shows it so
    it is always clear whether this is learning or a hunt. Claude sets it when a pipeline starts; Sharif can set it
    on the page."""
    try:
        d = json.loads(path.read_text())
        if d.get("mode") in MODES:
            return {"mode": d["mode"], "by": str(d.get("by", "")), "at": int(d.get("at", 0))}
    except Exception:
        pass
    return {"mode": "", "by": "", "at": 0}


def set_mode(path: Path, mode: str, by: str, now: float) -> dict:
    if mode not in MODES:
        raise ValueError("the mode is learn, hunt or nothing")
    d = {"mode": mode, "by": by[:20], "at": int(now)}
    path.write_text(json.dumps(d))
    return d


def add_note(path: Path, body: dict, now: float) -> dict:
    """Append one of Sharif's notes from the side panel: {"kind": "learn" | "hunt", "text", "asset", "tf", "chart_time"}.
    Returns the stored row. A note is never edited; removing one appends {"delete": id}."""
    text = str(body.get("text", "")).strip()
    if not text:
        raise ValueError("an empty note")
    kind = body.get("kind") if body.get("kind") in ("learn", "hunt") else "learn"
    row = {"id": f"{int(now * 1000):x}", "saved": int(now), "kind": kind, "text": text[:20000], "asset": str(body.get("asset", ""))[:20],
           "tf": str(body.get("tf", ""))[:4], "chart_time": body.get("chart_time") if isinstance(body.get("chart_time"), int) else None}
    with path.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def remove_note(path: Path, note_id: str, now: float) -> None:
    with path.open("a") as f:
        f.write(json.dumps({"delete": str(note_id)[:40], "saved": int(now)}) + "\n")


def add_reply(path: Path, note_id: str, text: str, now: float) -> dict:
    """Claude marks one of his notes as read and, with ``text``, answers it. Kept in Claude's own file."""
    row = {"note": str(note_id)[:40], "saved": int(now), "text": str(text).strip()[:20000]}
    with path.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def replies_by_note(path: Path | None) -> dict:
    """Per note id: when Claude first read it, and Claude's answers in the order they were written."""
    out: dict = {}
    if path is None or not path.exists():
        return out
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            o = out.setdefault(r["note"], {"seen": r["saved"], "replies": []})
            if r.get("text"):
                o["replies"].append({"saved": r["saved"], "text": r["text"]})
    return out


def list_notes(path: Path, last: int = 200, replies: Path | None = None) -> list[dict]:
    """His notes, newest first, without the removed ones. With ``replies``, each note also says whether Claude has
    read it (``seen``: when, or None) and carries Claude's answers (``replies``)."""
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    gone = {r["delete"] for r in rows if "delete" in r}
    notes = [r for r in rows if "delete" not in r and r["id"] not in gone][::-1][:last]
    if replies is not None:
        by = replies_by_note(replies)
        notes = [{**n, "seen": by.get(n["id"], {}).get("seen"), "replies": by.get(n["id"], {}).get("replies", [])} for n in notes]
    return notes


# ---- live: while it is switched on, the instruments on the page are refreshed from the free feed about once a minute
LIVE = {"on": False, "assets": [], "beat": 0.0, "fetched": {}, "added": {}, "error": ""}
LIVE_EVERY, LIVE_IDLE = 55, 180          # seconds between downloads of one instrument; stop when no page has asked for this long


def live_set(state: dict, on: bool, assets: list, now: float) -> dict:
    """The page switches live on or off and says which instruments it is showing. Each call is also a heartbeat."""
    state["on"] = bool(on)
    state["assets"] = [a for a in dict.fromkeys(assets) if a in cd.FOLDERS][:12] if on else []
    state["beat"] = now
    if not on:
        state["error"] = ""
    return live_status(state, now)


def live_due(state: dict, now: float) -> list[str]:
    """Which instruments should be downloaded now: live is on, a page asked recently, and their last download is old enough."""
    if not state["on"] or now - state["beat"] > LIVE_IDLE:
        return []
    return [a for a in state["assets"] if now - state["fetched"].get(a, 0) >= LIVE_EVERY]


def live_status(state: dict, now: float) -> dict:
    return {"on": state["on"] and now - state["beat"] <= LIVE_IDLE, "assets": state["assets"], "error": state["error"],
            "ago": {a: int(now - t) for a, t in state["fetched"].items() if a in state["assets"]}}


def live_loop() -> None:
    while True:
        for asset in live_due(LIVE, time.time()):
            try:
                LIVE["added"][asset] = fetch.merge_files(asset, fetch.fetch_recent(asset))
                LIVE["error"] = ""
            except Exception as e:                               # the feed is free and sometimes fails: say so on the page and try again next round
                LIVE["error"] = f"{asset}: {str(e)[:160]}"
            LIVE["fetched"][asset] = time.time()
        time.sleep(3)


def frames(asset: str):
    """The instrument's 1-minute candles, re-read only when a file changed."""
    files = sorted((cd.DATA / cd.FOLDERS[asset]).glob("*-bid.parquet"))
    sig = tuple((f.name, f.stat().st_mtime_ns) for f in files[-2:]) + (len(files),)
    if asset not in _cache or _cache[asset][0] != sig:
        _cache[asset] = (sig, cd.load_1m(asset), {})
    return _cache[asset]


def candles(asset: str, tf: str, until: int | None = None) -> dict:
    """{"candles": [...], "last": time of the newest minute on file, "end": True when ``until`` is at or past it}.
    With ``until`` (New York clock, epoch seconds) the chart is taken back to that minute: nothing later is sent."""
    _, df, done = frames(asset)
    if tf not in done:
        done[tf] = cd.resample(df, tf)
    newest = int((df.index[-1] - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1))
    if until is None or until >= newest:
        return {"candles": cd.to_candles(done[tf], LAST.get(tf)), "last": newest, "end": True}
    at = pd.Timestamp(until, unit="s")
    return {"candles": cd.to_candles(cd.cut(df, done[tf], tf, at), LAST.get(tf)), "last": newest, "end": False}


def equal_in_view(cs: list[dict], t_from: int, t_to: int, share: float) -> dict:
    """For the "how close is equal" slider: the equal highs and lows still resting, where "very close" is ``share`` of
    the height of the stretch on screen (``t_from`` to ``t_to``). Only sets that touch that stretch are returned."""
    view = [x for x in cs if t_from <= x["time"] <= t_to]
    near = liquidity.near_from_view(view, max(0.0, min(share, 0.2)))
    known = [x for x in cs if x["time"] <= t_to]                       # nothing to the right of the screen is used
    sets = [{k: g[k] for k in ("side", "top", "bottom", "count", "t0", "t1")} for g in liquidity.equal_sets(known, near)] if view else []
    return {"near": near, "sets": [g for g in sets if g["t1"] >= t_from]}


def backtest_calls():
    """The calls of the last backtest run, read again only when the files have changed."""
    stamp = tuple(sorted((f.name, f.stat().st_mtime) for f in backtest.OUT.glob("calls-*.parquet")))
    if _calls["stamp"] != stamp:
        _calls.update(stamp=stamp, df=backtest.load())
    return _calls["df"]


def backtest_call(call_id: str) -> dict | None:
    df = backtest_calls()
    hit = df[df["id"] == call_id] if len(df) else df
    if not len(hit):
        return None
    row = hit.iloc[0].to_dict()
    try:                                        # every timeframe's read at that moment, so the higher ones are seen too
        if row["asset"] not in _ladders:
            _ladders.clear()                    # one instrument's candles are kept at a time: they are large
            _ladders[row["asset"]] = backtest_run.prepare(row["asset"])
        ladder = {tf: r for tf, (_, r) in backtest_run.reads_at(_ladders[row["asset"]], int(row["moment"])).items()}
    except Exception:
        ladder = None
    return backtest.call_marks(row, ladder)


def marks_for(asset: str) -> dict:
    doc = json.loads(MARKS.read_text()) if MARKS.exists() else {}
    return {"at": doc.get("at", ""), **{"marks": [], "read": []}, **doc.get(asset, {})}


class Handler(BaseHTTPRequestHandler):
    password: str | None = None
    hosts: tuple[str, ...] = ()

    def log_message(self, *a):                                   # quiet
        pass

    def _send(self, code: int, body: bytes, kind: str = "application/json"):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if code == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="chart"')
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj).encode())

    def _ok(self) -> bool:
        if not host_ok(self.headers.get("Host"), self.hosts):
            self._send(403, b"unexpected host name", "text/plain")
            return False
        if allowed(self.client_address[0], self.headers.get("Authorization"), self.password):
            return True
        self._send(401, b"password needed", "text/plain")
        return False

    def do_GET(self):
        if not self._ok():
            return
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif u.path in STATIC:
                self._send(200, (HERE / STATIC[u.path][0]).read_bytes(), STATIC[u.path][1])
            elif u.path == "/api/assets":
                self._json({"assets": cd.available(), "timeframes": cd.TIMEFRAMES})
            elif u.path == "/api/candles":
                if q.get("asset") not in cd.FOLDERS or q.get("tf") not in cd.TIMEFRAMES:
                    return self._json({"error": "unknown instrument or timeframe"}, 400)
                until = int(q["until"]) if q.get("until", "").lstrip("-").isdigit() else None
                self._json(candles(q["asset"], q["tf"], until))
            elif u.path == "/api/equal":
                if q.get("asset") not in cd.FOLDERS or q.get("tf") not in cd.TIMEFRAMES:
                    return self._json({"error": "unknown instrument or timeframe"}, 400)
                until = int(q["until"]) if q.get("until", "").lstrip("-").isdigit() else None
                cs = candles(q["asset"], q["tf"], until)["candles"]
                self._json(equal_in_view(cs, int(float(q.get("from", 0))), int(float(q.get("to", 0))), float(q.get("share", 0))))
            elif u.path == "/api/marks":
                call = backtest_call(q["call"]) if q.get("call") else None       # a backtest call opened on the chart shows its own marks
                self._json({"marks": [], "read": [], **call} if call and call["asset"] == q.get("asset") else marks_for(q.get("asset", "")))
            elif u.path == "/backtest":
                self._send(200, BACKTEST_PAGE.read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/backtest/check":
                self._send(200, CHECK_PAGE.read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/api/backtest/check":                                    # ten merged calls for him to go through
                said = backtest.reviews(backtest.REVIEWS)
                self._json([{**c, "review": said.get(c["id"])} for c in backtest.check(backtest_calls())])
            elif u.path == "/api/backtest/tables":
                df = backtest_calls()
                names = [n for n in q.get("assets", "").split(",") if n]            # ?assets=A,B: only those instruments
                self._json(backtest.tables(df[df["asset"].isin(names)] if names and len(df) else df, [t for t in cd.TIMEFRAMES]))
            elif u.path == "/api/backtest/calls":
                df = backtest_calls()
                limit = min(int(q["limit"]), 500) if q.get("limit", "").isdigit() else 60
                self._json(backtest.pick(df, limit, **{k: q.get(k) for k in ("asset", "tf", "kind", "outcome", "nearer")}) if len(df) else [])
            elif u.path == "/api/backtest/call":
                call = backtest_call(q.get("id", ""))
                self._json(call or {"error": "no such call"}, 200 if call else 404)
            elif u.path == "/api/notes":
                self._json(list_notes(NOTES, replies=REPLIES))
            elif u.path == "/api/mode":
                self._json(get_mode(MODE))
            elif u.path == "/api/live":
                self._json(live_status(LIVE, time.time()))
            else:
                self._send(404, b"not found", "text/plain")
        except FileNotFoundError as e:
            self._json({"error": str(e)}, 404)

    def _body(self):
        """The JSON body of a write, or None after answering why not. Only the page itself may write: a JSON request
        (which another site cannot send without asking first) from this origin, of a sane size."""
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
            self._json({"error": "a save must be JSON"}, 415)
        elif not same_origin(self.headers.get("Origin"), self.headers.get("Host")):
            self._json({"error": "a save must come from the chart page"}, 403)
        else:
            size = int(self.headers.get("Content-Length") or 0)
            if size <= 0 or size > MAX_SAVE:
                self._json({"error": "bad save size"}, 413)
            else:
                try:
                    body = json.loads(self.rfile.read(size))
                    if isinstance(body, dict):
                        return body
                except Exception:
                    pass
                self._json({"error": "bad save"}, 400)
        return None

    def do_POST(self):
        if not self._ok():
            return
        path = urlparse(self.path).path
        if path not in ("/api/save", "/api/note", "/api/mode", "/api/live", "/api/backtest/review"):
            return self._send(404, b"not found", "text/plain")
        body = self._body()
        if body is None:
            return
        if path == "/api/backtest/review":
            try:
                return self._json(backtest.add_review(backtest.REVIEWS, body.get("id", ""), str(body.get("verdict", "")), body.get("text", ""), time.time()))
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
        if path == "/api/live":
            return self._json(live_set(LIVE, bool(body.get("on")), [str(a) for a in body.get("assets", []) if isinstance(a, str)], time.time()))
        if path == "/api/mode":
            try:
                return self._json(set_mode(MODE, str(body.get("mode", "")), "Sharif", time.time()))
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
        if path == "/api/note":
            try:
                if body.get("delete"):
                    remove_note(NOTES, body["delete"], time.time())
                    return self._json({"removed": True})
                made = add_note(NOTES, body, time.time())
                study()
                return self._json(made)
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
        try:
            row = {"saved": int(time.time()), "asset": str(body["asset"]), "tf": str(body.get("tf", "")),
                   "marks": list(body.get("marks", [])), "notes": list(body.get("notes", [])), "note": str(body.get("note", "")),
                   "chart_time": body.get("chart_time")}
        except Exception:
            return self._json({"error": "bad save"}, 400)
        with SAVES.open("a") as f:
            f.write(json.dumps(row) + "\n")
        study()
        self._json({"saved": len(row["marks"]) + len(row["notes"])})


def study() -> None:
    """Bring the per-instrument study log up to date with what he has saved. It only reads his files; a failure here
    must never stop a save, so it is swallowed and shown in the server's output."""
    try:
        since = json.loads(study_log.STUDY.read_text())["started"] if study_log.STUDY.exists() else 0
        study_log.build(SAVES, NOTES, study_log.OUT, since)
    except Exception as e:                                           # noqa: BLE001
        print("study log not rebuilt:", e, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="The v2 chart page")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8776)
    ap.add_argument("--allow-host", action="append", default=[], help="a host name this page may be opened under, besides addresses and localhost")
    ap.add_argument("--password-env", help="name of a variable (environment or .env) holding the password other devices must give")
    a = ap.parse_args()
    Handler.hosts = tuple(a.allow_host)
    if a.password_env:
        Handler.password = read_env(HERE.parents[1] / ".env", a.password_env)
        if not Handler.password:
            raise SystemExit(f"{a.password_env} is not set (environment or .env)")
    if a.host not in ("127.0.0.1", "localhost", "::1") and not Handler.password:
        raise SystemExit("refusing to listen on the network without a password: add --password-env")
    threading.Thread(target=live_loop, daemon=True).start()
    print(f"chart on http://{a.host}:{a.port}/  ({'password set for other devices' if Handler.password else 'this machine only'})", flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
