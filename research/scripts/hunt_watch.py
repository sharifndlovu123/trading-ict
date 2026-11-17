"""Watch the live sheet without a model: print one line only when something happens at what Claude marked.

Sharif 2026-11-17: a model check every few minutes is expensive; a script watches and wakes Claude only at the
important moments. It reads `out/live/today.json` (written by live_recipe.py) against Claude's marks in
`out/live/overlay.json` once a minute and prints an event when, per index:
  - price trades through a marked level (a sweep of marked liquidity)
  - price enters a marked zone (an area of interest)
  - a 5m candle is a hard push (body ≥ ``PUSH_ADR`` of the average day's range)
  - a 5m order block forms where the overlay asks for one (`watch_ob` per index: side, below / above, min_body);
    it is graded clean or dim by the body's share of the candle
  - Sharif saves new marks or notes (`reports/reviews/live.jsonl` grows; the file is only read)
  - the live feed goes stale (no new bar for ``STALE_MIN`` minutes)
Each event fires once per prep (the state resets when the overlay's `at` changes); state is kept in
`out/live/watch_state.json` so a restart does not repeat events. It only sees what was marked: anything unforeseen
needs the slower full check.

    uv run python research/scripts/hunt_watch.py            # runs until 16:05 New York
    uv run python research/scripts/hunt_watch.py --once
    uv run python research/scripts/hunt_watch.py --until-event --checker-min 15     # as Claude runs it

``--checker-min N``: every N minutes a cheaper model (Sonnet) reads `research/hunt-rules.md` and a short summary and
answers OK or ESCALATE; only escalations are printed. ``--until-event``: exit after the first report, so the
background run wakes Claude exactly once and is then restarted.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
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
            if key in fired or "p0" in m or m.get("watch") is False:      # arrows and history marks ("… swept") are not watched
                continue
            if m.get("price") is not None:                       # a level: fires when price trades through it
                if key not in state["side"]:                     # first sight: note the side, judge from the next reading
                    state["side"][key] = "below" if last < m["price"] else "above"
                    continue
                side = state["side"][key]
                if (side == "below" and hi > m["price"]) or (side == "above" and lo < m["price"]):   # strictly through: the candle that made the level is not a sweep of it
                    fired.append(key)
                    out.append(f"{asset}: price traded through {m['kind']} {m['price']} (from {side}); last {last}")
            elif m.get("top") is not None and lo <= m["top"] and hi >= m["bottom"]:
                fired.append(key)
                out.append(f"{asset}: price entered {m.get('tf', '')} {m['kind']} {m['bottom']}–{m['top']}; last {last}")
        wob = overlay.get(asset, {}).get("watch_ob")             # e.g. {"side": "sell", "below": 27303.3, "min_body": 50}
        if wob and len(c5) > 2:                                  # a 5m order block: a closed candle engulfed by the next closed one
            blk, eng = c5[-3], c5[-2]
            sell = wob.get("side", "sell") == "sell"
            body, rng = abs(blk["close"] - blk["open"]), blk["high"] - blk["low"]
            is_blk = (blk["close"] > blk["open"] and eng["close"] < blk["open"]) if sell else (blk["close"] < blk["open"] and eng["close"] > blk["open"])
            inside = blk["high"] < wob.get("below", float("inf")) and blk["low"] > wob.get("above", float("-inf"))
            key = f"{asset}|ob@{blk['time']}"
            if is_blk and inside and rng > 0 and key not in fired:
                fired.append(key)
                pct = round(100 * body / rng)
                grade = "clean" if pct >= wob.get("min_body", 50) else "dim"
                out.append(f"{asset}: 5m {'sell' if sell else 'buy'} order block formed ({grade}, body {pct}%): "
                           f"{min(blk['open'], blk['close'])}–{max(blk['open'], blk['close'])}, engulfed to {eng['close']}; last {last}")
        adr = item.get("adr")
        done = c5[-2] if len(c5) > 1 else None                   # the last closed 5m candle
        if adr and done and state["push"].get(asset) != done["time"]:
            body = done["close"] - done["open"]
            if abs(body) >= PUSH_ADR * adr:
                state["push"][asset] = done["time"]
                out.append(f"{asset}: hard 5m push {'up' if body > 0 else 'down'} ({abs(body):.1f} = {abs(body) / adr:.2f} ADR), "
                           f"{done['open']} → {done['close']}; last {last}")
    return out


def summary(doc: dict, overlay: dict) -> str:
    """A short text picture of the three indices for the checker: prices, recent candles, Claude's marks and read."""
    hm = lambda t: datetime.fromtimestamp(t, ZoneInfo("UTC")).strftime("%H:%M")  # noqa: E731  (candle times are NY wall clock)
    out = [f"Now: {doc.get('now')} New York. Prep: {overlay.get('at')}"]
    for asset, item in doc.get("assets", {}).items():
        c = item.get("candles", {})
        row = lambda xs: " | ".join(f"{hm(x['time'])} o{x['open']} h{x['high']} l{x['low']} c{x['close']}" for x in xs)  # noqa: E731
        ov = overlay.get(asset, {})
        out += [f"\n## {asset}: last {item.get('last')}, ADR {item.get('adr')}, levels {item.get('levels')}",
                "5m (last 12): " + row((c.get("5m") or [])[-12:]), "15m (last 12): " + row((c.get("15m") or [])[-12:]),
                "1h (last 8): " + row((c.get("1h") or [])[-8:]),
                "Marked: " + "; ".join(f"{m.get('kind')} {m.get('price', (m.get('bottom'), m.get('top')))}" for m in ov.get("marks", []) if "p0" not in m),
                "Read: " + " ".join(ov.get("read", []))]
    return "\n".join(out)


def parse_checker(reply: str) -> list[str]:
    """The checker's escalations (lines starting ESCALATE); anything else, including OK, is nothing."""
    return [ln.strip() for ln in reply.splitlines() if ln.strip().upper().startswith("ESCALATE")]


def ask_checker(text: str, model: str = "sonnet", rules: Path = Path("research/hunt-rules.md")) -> list[str]:
    """One small call to a cheaper model, from an empty folder so no project context is loaded. It sees only the
    rules and the summary, and answers OK or ESCALATE lines."""
    prompt = (rules.read_text() + "\n\n---\nThe current picture:\n\n" + text
              + "\n\nAnswer now: exactly `OK`, or one `ESCALATE: ...` line per thing Fable should look at.")
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["claude", "-p", "--model", model, "--max-turns", "1"], input=prompt, capture_output=True, text=True, timeout=120, cwd=tmp)
    return parse_checker(r.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--until-event", action="store_true", help="exit after the first reading that reports something")
    ap.add_argument("--checker-min", type=int, default=0, help="ask the cheaper model every N minutes (0 = never)")
    ap.add_argument("--checker-model", default="sonnet")
    a = ap.parse_args()
    last_ask = _time.time()
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
            if a.checker_min and _time.time() - last_ask >= a.checker_min * 60:
                last_ask = _time.time()
                try:
                    lines += [f"checker ({a.checker_model}) {x}" for x in ask_checker(summary(doc, overlay), a.checker_model)]
                except Exception as e:
                    lines.append(f"checker failed: {type(e).__name__}: {e}")
            for ln in lines:
                print(f"[{doc['now'][-5:]} NY] {ln}", flush=True)
            sp.write_text(json.dumps(state))
        except Exception as e:                                   # a half-written file must not stop the watch
            msg = f"WATCH ERROR: {type(e).__name__}: {e}"
            if state.get("err") != msg:                          # say it once, not every minute
                state["err"] = msg
                print(msg, flush=True)
        if a.once or (a.until_event and lines) or datetime.now(ny).strftime("%H:%M") >= "16:05":
            break
        _time.sleep(60)


if __name__ == "__main__":
    main()
