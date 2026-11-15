"""Local liquidity-map reviewer: the triage server pointed at viewer/liqmap.html + out/liqmap/*; marks go to
reports/reviews/liqmap.jsonl (one JSON per save; the newest save for an id wins).

    uv run python research/scripts/liqmap_server.py [--port 8766]   # then open http://127.0.0.1:8766
"""
import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_server as ts  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--answers", type=Path, default=ts.ROOT / "reports" / "reviews" / "liqmap.jsonl")
    a = ap.parse_args()
    ts.DATA, ts.PAGE, ts.ANSWERS = ts.ROOT / "out" / "liqmap", ts.ROOT / "viewer" / "liqmap.html", a.answers.resolve()
    if not (ts.DATA / "index.json").exists():
        raise SystemExit("build the set first: uv run python research/scripts/liqmap_build.py")
    print(f"liquidity map: http://127.0.0.1:{a.port}  (marks → {ts.ANSWERS})")
    ThreadingHTTPServer(("127.0.0.1", a.port), ts.Handler).serve_forever()


if __name__ == "__main__":
    main()
