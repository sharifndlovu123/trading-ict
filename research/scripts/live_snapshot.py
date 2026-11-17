"""Take the live sheet back to a moment of today: a frozen copy of `out/live/today.json` cut at a New York time, for
going over a trade on a fresh chart (Sharif 2026-11-17). Nothing after the cut is in the copy: every candle that was
still forming at that moment is rebuilt from the 1-minute candles up to it.

    uv run python research/scripts/live_snapshot.py --at 09:54 --out out/review
    uv run python research/scripts/liqmap_server.py --port 8777 --data out/review --page viewer/live.html \
        --answers reports/reviews/review.jsonl

Run it again with another `--at` to step the same page forward or back (the page re-reads every 20 seconds). The
copy keeps the candles and the day's levels only: plans, areas and structure breaks are left out, because the live
file computed them later.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

SPAN = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400}


def _merge(parts: list[dict], start: int) -> dict:
    return {"time": start, "open": parts[0]["open"], "high": max(p["high"] for p in parts),
            "low": min(p["low"] for p in parts), "close": parts[-1]["close"]}


def cut(doc: dict, at: int) -> dict:
    """``doc`` as it stood at epoch ``at`` (candle times are New York wall clock as UTC epochs)."""
    out = {**doc, "mode": "replay", "hunting": False, "assets": {}}
    out["now"] = datetime.fromtimestamp(at, timezone.utc).strftime("%a %Y-%m-%d %H:%M")
    for name, item in doc["assets"].items():
        C = item["candles"]
        m1 = [c for c in C.get("1m", []) if c["time"] + 60 <= at]                 # closed 1m candles only
        if not m1:
            continue
        new = {"1m": m1}
        for tf, span in SPAN.items():                                           # intraday: rebuild the forming candle
            src = C.get(tf, [])
            done = [c for c in src if c["time"] + span <= at]
            cur = next((c for c in src if c["time"] <= at - 1 < c["time"] + span and c["time"] + span > at), None)   # still forming at the cut
            part = [c for c in m1 if cur and c["time"] >= cur["time"]]
            new[tf] = done + ([_merge(part, cur["time"])] if part else [])
        day = C.get("1D", [])
        today = _merge(m1, day[-1]["time"]) if day else None                    # 1m candles start at the day's 18:00 open
        if day:
            new["1D"] = day[:-1] + [today]
        for tf in ("1W", "1M"):                                                  # week / month: earlier days + today so far
            src = C.get(tf, [])
            if src and day:
                parts = [c for c in day[:-1] if c["time"] >= src[-1]["time"]] + [today]
                new[tf] = src[:-1] + [{**_merge(parts, src[-1]["time"]), "open": src[-1]["open"]}]
        out["assets"][name] = {"last": m1[-1]["close"], "last_bar": datetime.fromtimestamp(m1[-1]["time"], timezone.utc).strftime("%a %H:%M"),
                               "adr": item.get("adr"), "levels": item.get("levels", {}), "conditions": item.get("conditions", {}),
                               "setups": [], "breaks": [], "areas": [], "candles": new}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", required=True, help="New York time today, HH:MM")
    ap.add_argument("--src", type=Path, default=Path("out/live/today.json"))
    ap.add_argument("--out", type=Path, default=Path("out/review"))
    a = ap.parse_args()
    doc = json.loads(a.src.read_text())
    h, m = map(int, a.at.split(":"))
    day = datetime.strptime(doc["day"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    snap = cut(doc, int(day.timestamp()) + h * 3600 + m * 60)
    a.out.mkdir(parents=True, exist_ok=True)
    tmp = a.out / "today.json.tmp"
    tmp.write_text(json.dumps(snap))
    tmp.replace(a.out / "today.json")
    (a.out / "index.json").write_text(json.dumps({"ids": ["today"]}))
    print(f"snapshot at {snap['now']} New York → {a.out / 'today.json'}")


if __name__ == "__main__":
    main()
