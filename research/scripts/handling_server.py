"""Local trade-handling reviewer: the triage server pointed at viewer/handling.html + out/handling/*; answers go to
reports/reviews/handling.jsonl (one JSON per save; the newest save for an id wins).

    uv run python research/scripts/handling_server.py [--port 8767]   # then open http://127.0.0.1:8767
"""
import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_server as ts  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--answers", type=Path, default=ts.ROOT / "reports" / "reviews" / "handling.jsonl")
    a = ap.parse_args()
    ts.DATA, ts.PAGE, ts.ANSWERS = ts.ROOT / "out" / "handling", ts.ROOT / "viewer" / "handling.html", a.answers.resolve()
    if not (ts.DATA / "index.json").exists():
        raise SystemExit("build the set first: uv run python research/scripts/handling_build.py")
    print(f"trade handling: http://127.0.0.1:{a.port}  (marks → {ts.ANSWERS})")
    ThreadingHTTPServer(("127.0.0.1", a.port), ts.Handler).serve_forever()


if __name__ == "__main__":
    main()
