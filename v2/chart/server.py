"""The v2 chart: one small page that shows candles and marks.

    uv run python v2/chart/server.py                                              # this machine only
    uv run python v2/chart/server.py --host 0.0.0.0 --password-env LIVE_PAGE_PASSWORD   # other devices, with a password

Then http://127.0.0.1:8776/?asset=UK100&tf=1D

A display and nothing else. Claude's marks are read from `marks.json` beside this file; what Sharif draws and saves
is appended to `saves.jsonl`. Candles come from `data/bars/` (refresh them with `fetch.py`).
"""
from __future__ import annotations

import argparse
import base64
import hmac
import ipaddress
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candles as cd  # noqa: E402

MARKS, SAVES, PAGE = HERE / "marks.json", HERE / "saves.jsonl", HERE / "page.html"
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


def frames(asset: str):
    """The instrument's 1-minute candles, re-read only when a file changed."""
    files = sorted((cd.DATA / cd.FOLDERS[asset]).glob("*-bid.parquet"))
    sig = tuple((f.name, f.stat().st_mtime_ns) for f in files[-2:]) + (len(files),)
    if asset not in _cache or _cache[asset][0] != sig:
        _cache[asset] = (sig, cd.load_1m(asset), {})
    return _cache[asset]


def candles(asset: str, tf: str) -> list[dict]:
    _, df, done = frames(asset)
    if tf not in done:
        done[tf] = cd.to_candles(cd.resample(df, tf), LAST.get(tf))
    return done[tf]


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
            elif u.path == "/api/assets":
                self._json({"assets": cd.available(), "timeframes": cd.TIMEFRAMES})
            elif u.path == "/api/candles":
                if q.get("asset") not in cd.FOLDERS or q.get("tf") not in cd.TIMEFRAMES:
                    return self._json({"error": "unknown instrument or timeframe"}, 400)
                self._json(candles(q["asset"], q["tf"]))
            elif u.path == "/api/marks":
                self._json(marks_for(q.get("asset", "")))
            else:
                self._send(404, b"not found", "text/plain")
        except FileNotFoundError as e:
            self._json({"error": str(e)}, 404)

    def do_POST(self):
        if not self._ok():
            return
        if urlparse(self.path).path != "/api/save":
            return self._send(404, b"not found", "text/plain")
        # only the page itself may save: a JSON request (which another site cannot send without asking first) from this origin
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
            return self._json({"error": "a save must be JSON"}, 415)
        if not same_origin(self.headers.get("Origin"), self.headers.get("Host")):
            return self._json({"error": "a save must come from the chart page"}, 403)
        size = int(self.headers.get("Content-Length") or 0)
        if size <= 0 or size > MAX_SAVE:
            return self._json({"error": "bad save size"}, 413)
        try:
            body = json.loads(self.rfile.read(size))
            row = {"saved": int(time.time()), "asset": str(body["asset"]), "tf": str(body.get("tf", "")),
                   "marks": list(body.get("marks", [])), "note": str(body.get("note", ""))}
        except Exception:
            return self._json({"error": "bad save"}, 400)
        with SAVES.open("a") as f:
            f.write(json.dumps(row) + "\n")
        self._json({"saved": len(row["marks"])})


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
    print(f"chart on http://{a.host}:{a.port}/  ({'password set for other devices' if Handler.password else 'this machine only'})", flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
