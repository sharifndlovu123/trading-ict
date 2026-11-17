"""Watch the live sheet without a model: print one line only when something happens at what Claude marked.

Sharif 2026-11-17: a model check every few minutes is expensive; a script watches and wakes Claude only at the
important moments. It reads `out/live/today.json` (written by live_recipe.py) against Claude's marks in
`out/live/overlay.json` once a minute and prints an event when, per index:
  - price trades through a marked level (a sweep of marked liquidity)
  - price enters a marked zone (an area of interest)
  - a 5m candle is a hard push (body ≥ ``PUSH_ADR`` of the average day's range)
  - Sharif saves new marks or notes (`reports/reviews/live.jsonl` grows; the file is only read)
  - the live feed goes stale (no new bar for ``STALE_MIN`` minutes)
Each event fires once per prep (the state resets when the overlay's `at` changes); state is kept in
`out/live/watch_state.json` so a restart does not repeat events. It only sees what was marked: anything unforeseen
needs the slower full check.

    uv run python research/scripts/hunt_watch.py            # runs until 16:05 New York
    uv run python research/scripts/hunt_watch.py --once
"""
from __future__ import annotations

import argparse
import json
import time as _time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

OUT = Path("out/live")
SAVES = Path("reports/reviews/live.jsonl")
PUSH_ADR = 0.08
STALE_MIN = 6


def mark_id(m: dict) -> str:
    return f"{m.get('kind')}@{m.get('price', (m.get('bottom'), m.get('top')))}"


def events(doc: dict, overlay: dict, state: dict) -> list[str]:
    """The new events for this reading; ``state`` (fired ids, each level's starting side, last push candle) is
    updated in place. Pure apart from that: no files, no clock."""
    if state.get("at") != overlay.get("at"):                     # a new prep: start again
        state.clear()
        state.update(at=overlay.get("at"), fired=[], side={}, push={})
    out, fired = [], state["fired"]
    for asset, item in doc.get("assets", {}).items():
        last, c5 = item.get("last"), (item.get("candles", {}).get("5m") or [])
        if last is None or not c5:
            continue
        bar = c5[-1]
        hi, lo = max(bar["high"], last), min(bar["low"], last)
        for m in overlay.get(asset, {}).get("marks", []):
            key = f"{asset}|{mark_id(m)}"
            if key in fired or "p0" in m:
                continue
            if m.get("price") is not None:                       # a level: fires when price trades through it
                if key not in state["side"]:                     # first sight: note the side, judge from the next reading
                    state["side"][key] = "below" if last < m["price"] else "above"
                    continue
                side = state["side"][key]
                if (side == "below" and hi >= m["price"]) or (side == "above" and lo <= m["price"]):
                    fired.append(key)
                    out.append(f"{asset}: price traded through {m['kind']} {m['price']} (from {side}); last {last}")
            elif m.get("top") is not None and lo <= m["top"] and hi >= m["bottom"]:
                fired.append(key)
                out.append(f"{asset}: price entered {m.get('tf', '')} {m['kind']} {m['bottom']}–{m['top']}; last {last}")
        adr = item.get("adr")
        done = c5[-2] if len(c5) > 1 else None                   # the last closed 5m candle
        if adr and done and state["push"].get(asset) != done["time"]:
            body = done["close"] - done["open"]
            if abs(body) >= PUSH_ADR * adr:
                state["push"][asset] = done["time"]
                out.append(f"{asset}: hard 5m push {'up' if body > 0 else 'down'} ({abs(body):.1f} = {abs(body) / adr:.2f} ADR), "
                           f"{done['open']} → {done['close']}; last {last}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    sp = OUT / "watch_state.json"
    state = json.loads(sp.read_text()) if sp.exists() else {}
    ny = ZoneInfo("America/New_York")
    while True:
        try:
            doc = json.loads((OUT / "today.json").read_text())
            overlay = json.loads((OUT / "overlay.json").read_text()) if (OUT / "overlay.json").exists() else {}
            lines = events(doc, overlay, state)
            n = sum(1 for _ in SAVES.open()) if SAVES.exists() else 0
            if state.get("saves") is not None and n > state["saves"]:
                lines.append(f"Sharif saved {n - state['saves']} new entr{'y' if n - state['saves'] == 1 else 'ies'} (marks / notes)")
            state["saves"] = n
            now = datetime.now(ny)
            age = (now.replace(tzinfo=None) - datetime.strptime(doc["now"], "%a %Y-%m-%d %H:%M")).total_seconds() / 60
            if age > STALE_MIN and not state.get("stale"):
                state["stale"] = True
                lines.append(f"FEED STALE: today.json is {age:.0f} minutes old (is live_recipe.py running?)")
            elif age <= STALE_MIN:
                state["stale"] = False
            for ln in lines:
                print(f"[{doc['now'][-5:]} NY] {ln}", flush=True)
            sp.write_text(json.dumps(state))
        except Exception as e:                                   # a half-written file must not stop the watch
            msg = f"WATCH ERROR: {type(e).__name__}: {e}"
            if state.get("err") != msg:                          # say it once, not every minute
                state["err"] = msg
                print(msg, flush=True)
        if a.once or datetime.now(ny).strftime("%H:%M") >= "16:05":
            break
        _time.sleep(60)


if __name__ == "__main__":
    main()
