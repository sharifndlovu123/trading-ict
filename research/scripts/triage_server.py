"""Local triage reviewer: serves viewer/triage.html + out/triage/* on 127.0.0.1 and appends answers to
reports/reviews/triage.jsonl (one JSON per answer; the newest answer for an id wins).

    uv run python research/scripts/triage_server.py [--port 8765]   # then open http://127.0.0.1:8765
"""
import argparse
import base64
import hmac
import json
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "out" / "triage"
PAGE = ROOT / "viewer" / "triage.html"
ANSWERS = ROOT / "reports" / "reviews" / "triage.jsonl"
REPLAY_SRC = None    # set by liqmap_server --replay-src: the live file a review page may re-cut itself from (/api/replay?at=HH:MM)
PASSWORD = None      # set by liqmap_server --password-env: devices other than this machine must give it (HTTP basic auth, any user name)


def answers() -> dict:
    out = {}
    if ANSWERS.exists():
        for line in ANSWERS.read_text().splitlines():
            if line.strip():
                a = json.loads(line)
                out[a["id"]] = a
    return out


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DATA), **kw)

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _allowed(self) -> bool:
        """This machine is always let in; with a password set, any other device has to send it."""
        if not PASSWORD or self.client_address[0] in ("127.0.0.1", "::1"):
            return True
        h = self.headers.get("Authorization", "")
        try:
            given = base64.b64decode(h.split(" ", 1)[1]).decode().split(":", 1)[1] if h.startswith("Basic ") else ""
        except Exception:
            given = ""
        if hmac.compare_digest(given.encode(), PASSWORD.encode()):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="live sheet"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def do_GET(self):
        if not self._allowed():
            return
        if self.path.split("?")[0] in ("/", "/index.html"):          # a link may carry ?asset=…&tf=…
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.split("?")[0].rstrip("/") == "/multi" and (PAGE.parent / "multi.html").exists():   # several charts together (the live sheet)
            body = (PAGE.parent / "multi.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ("/linedrag.js", "/marks.js"):     # shared viewer helpers (viewer/*.js)
            body = (ROOT / "viewer" / self.path[1:]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/api/replay") and REPLAY_SRC:    # temporary: step a review page forward or back in time
            import re
            import live_snapshot as ls
            m = re.search(r"at=(\d{1,2})(?::|%3A)(\d{2})", self.path)
            if not m:
                return self._json({"error": "at=HH:MM"}, 400)
            doc = json.loads(Path(REPLAY_SRC).read_text())
            want = ls.at_epoch(doc, f"{m.group(1)}:{m.group(2)}")
            end = max(a["candles"]["1m"][-1]["time"] for a in doc["assets"].values() if a.get("candles", {}).get("1m")) + 60
            snap = ls.cut(doc, min(want, end))                    # never past the last candle the live file has
            if not snap["assets"]:
                return self._json({"error": "no candles before that time"}, 400)
            ls.write(snap, DATA)
            self._json({"now": snap["now"], "live": doc["now"], "end": want >= end})
        elif self.path == "/api/answers":
            self._json(answers())
        else:
            super().do_GET()

    def do_POST(self):
        if not self._allowed():
            return
        if self.path != "/api/answer":
            return self._json({"error": "not found"}, 404)
        a = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if not isinstance(a, dict) or "id" not in a:
            return self._json({"error": "bad answer"}, 400)
        a["saved"] = time.time()
        ANSWERS.parent.mkdir(parents=True, exist_ok=True)
        with ANSWERS.open("a") as f:
            f.write(json.dumps(a) + "\n")
        self._json({"ok": True})


def main():
    global ANSWERS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--answers", type=Path, default=ANSWERS, help="answers file (tests use a scratch file)")
    a = ap.parse_args()
    ANSWERS = a.answers.resolve()
    if not (DATA / "index.json").exists():
        raise SystemExit("build the set first: uv run python research/scripts/triage_build.py")
    print(f"triage: http://127.0.0.1:{a.port}  (answers → {ANSWERS})")
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
