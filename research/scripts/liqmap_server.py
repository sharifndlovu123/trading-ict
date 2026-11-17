"""Local liquidity-map reviewer: the triage server pointed at viewer/liqmap.html + out/liqmap/*; marks go to
reports/reviews/liqmap.jsonl (one JSON per save; the newest save for an id wins).

    uv run python research/scripts/liqmap_server.py [--port 8766]   # then open http://127.0.0.1:8766
    top-down review: ... liqmap_server.py --port 8768 --data out/topdown --page viewer/topdown.html \
                         --answers reports/reviews/topdown.jsonl
"""
import argparse
import os
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_server as ts  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = reachable from other devices on the network (anyone there can view and save)")
    ap.add_argument("--answers", type=Path, default=ts.ROOT / "reports" / "reviews" / "liqmap.jsonl")
    ap.add_argument("--data", type=Path, default=ts.ROOT / "out" / "liqmap")
    ap.add_argument("--page", type=Path, default=ts.ROOT / "viewer" / "liqmap.html")
    ap.add_argument("--password-env", help="name of a variable (environment or .env) holding a password that other devices must give")
    a = ap.parse_args()
    if a.password_env:
        pw = os.environ.get(a.password_env)
        env = ts.ROOT / ".env"
        if not pw and env.exists():
            pw = next((ln.split("=", 1)[1].strip().strip("'\"") for ln in env.read_text().splitlines() if ln.startswith(a.password_env + "=")), None)
        if not pw:
            raise SystemExit(f"{a.password_env} is not set (environment or .env)")
        ts.PASSWORD = pw
    elif a.host != "127.0.0.1":
        print("warning: open to the network without a password (--password-env)")
    ts.DATA, ts.PAGE, ts.ANSWERS = a.data.resolve(), a.page.resolve(), a.answers.resolve()
    if not (ts.DATA / "index.json").exists():
        raise SystemExit("build the set first: uv run python research/scripts/liqmap_build.py")
    print(f"liquidity map: http://{a.host}:{a.port}  (marks → {ts.ANSWERS})")
    ThreadingHTTPServer((a.host, a.port), ts.Handler).serve_forever()


if __name__ == "__main__":
    main()
