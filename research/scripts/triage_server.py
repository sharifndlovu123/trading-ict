"""Local triage reviewer: serves viewer/triage.html + out/triage/* on 127.0.0.1 and appends answers to
reports/reviews/triage.jsonl (one JSON per answer; the newest answer for an id wins).

    uv run python research/scripts/triage_server.py [--port 8765]   # then open http://127.0.0.1:8765
"""
import argparse
import json
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "out" / "triage"
PAGE = ROOT / "viewer" / "triage.html"
ANSWERS = ROOT / "reports" / "reviews" / "triage.jsonl"


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

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/answers":
            self._json(answers())
        else:
            super().do_GET()

    def do_POST(self):
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
