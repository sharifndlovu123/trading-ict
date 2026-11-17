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
needs the slower full check. Every reading also stamps `beat` in the state file; the pages read it with the overlay's
`hunt` entry to show whether the hunt is on and being watched.

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
        if last is None or not c5 or overlay.get(asset, {}).get("watch") is False:      # e.g. gold and silver: on the page for looking only
            continue
        bar = c5[-1]
        hi, lo = max(bar["high"], last), min(bar["low"], last)
        for m in overlay.get(asset, {}).get("marks", []):
            key = f"{asset}|{mark_id(m)}"
            if "p0" in m or m.get("watch") is False:                  # arrows and history marks ("… swept") are not watched
                continue
            if key in fired:                                           # already traded: now, has a 5m candle CLOSED beyond it?
                side0, done5 = state["side"].get(key), (c5[-2] if len(c5) > 1 else None)
                if m.get("price") is not None and done5 and key + "|close" not in fired \
                        and ((side0 == "below" and done5["close"] > m["price"]) or (side0 == "above" and done5["close"] < m["price"])):
                    fired.append(key + "|close")
                    out.append(f"{asset}: a 5m candle CLOSED {'above' if side0 == 'below' else 'below'} {m['kind']} {m['price']} ({done5['close']}): a body, not only a wick")
                continue
            if m.get("price") is not None:                       # a level: fires when price trades through it
                if key not in state["side"]:                     # first sight: note the side, judge from the next reading
                    state["side"][key] = "below" if last < m["price"] else "above"
                    continue
                side = state["side"][key]
                if (side == "below" and hi > m["price"]) or (side == "above" and lo < m["price"]):   # strictly through: the candle that made the level is not a sweep of it
                    fired.append(key)
                    out.append(f"{asset}: price traded through {m['kind']} {m['price']} (from {side}; a wick so far, watch the close); last {last}")
            elif m.get("top") is not None and lo < m["top"] and hi > m["bottom"]:      # strictly inside: the candle that made an edge has not entered
                fired.append(key)
                out.append(f"{asset}: price entered {m.get('tf', '')} {m['kind']} {m['bottom']}–{m['top']}; last {last}")
        idea = overlay.get(asset, {}).get("idea") or {}
        c1 = item.get("candles", {}).get("1m") or []
        if idea.get("side") in ("sell", "buy") and len(c1) > 1:
            sgn = -1 if idea["side"] == "sell" else 1                 # the way the trade goes
            done1, bar1 = c1[-2], c1[-1]
            beyond = lambda px, lvl: sgn * (px - lvl) > 0             # noqa: E731  price is past lvl in the trade's direction
            def once(tag, text):
                k = f"{asset}|idea|{tag}|{idea.get(tag.split(':')[0])}"
                if k not in fired:
                    fired.append(k)
                    out.append(f"{asset}: IDEA ({idea['side']}, goal {idea.get('goal_name', '')} {idea.get('goal', '')}): {text}; last {last}")
            ent = idea.get("entry")
            if ent is not None:
                e_lo, e_hi = (min(ent), max(ent)) if isinstance(ent, list) else (ent, ent)
                if lo <= e_hi and hi >= e_lo:
                    once("entry", f"price is at the entry {ent}")
            if idea.get("stop") is not None and not beyond(hi if sgn < 0 else lo, idea["stop"]) and (hi >= idea["stop"] if sgn < 0 else lo <= idea["stop"]):
                once("stop", f"the stop {idea['stop']} traded")
            for tag, what in (("cancel", "cancel the entry if it has not filled (his rule: a closed candle beyond the next liquidity past the first target)"),
                              ("goal", "the goal is closed through: if not in, the trade is missed and anything now is a chase")):
                lvl = idea.get(tag)
                if lvl is None:
                    continue
                if beyond(done1["close"], lvl):
                    once(tag, f"a 1m candle CLOSED beyond the {tag} level {lvl} ({done1['close']}): {what}")
                elif beyond(bar1["low"] if sgn < 0 else bar1["high"], lvl) or beyond(done1["low"] if sgn < 0 else done1["high"], lvl):
                    once(tag + ":wick", f"a wick beyond the {tag} level {lvl}, no close: nothing changes yet")
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
                if grade == "dim" and wob.get("clean_only"):
                    continue
                out.append(f"{asset}: 5m {'sell' if sell else 'buy'} order block formed ({grade}, body {pct}%): "
                           f"{min(blk['open'], blk['close'])}–{max(blk['open'], blk['close'])}, engulfed to {eng['close']}; last {last}")
        adr = item.get("adr")
        done = c5[-2] if len(c5) > 1 else None                   # the last closed 5m candle
        if adr and done and state["push"].get(asset) != done["time"]:
            body = done["close"] - done["open"]
            if abs(body) >= PUSH_ADR * adr:
                state["push"][asset] = done["time"]
                extra = ""
                if len(c5) > 3:
                    prev, nxt = c5[-3], c5[-1]
                    gap = (nxt["high"], prev["low"]) if body < 0 and prev["low"] > nxt["high"] else (prev["high"], nxt["low"]) if body > 0 and prev["high"] < nxt["low"] else None
                    if gap:
                        extra += f"; leaving a 5m gap {gap[0]}–{gap[1]} (not final until this candle closes)"
                    opp = pools(c5[-74:-2], adr)["highs" if body < 0 else "lows"]
                    near = [x for x in opp if abs(x["from"] - done["open"]) <= 0.5 * adr]
                    if near:
                        x = near[-1] if body < 0 else near[0]
                        extra += (f"; equal {'highs' if body < 0 else 'lows'} were created {'above' if body < 0 else 'below'} at {x['from']}–{x['to']} (x{x['count']}) and left: "
                                  "liquidity created, then displacement the other way; the return to the gap is where to look")
                out.append(f"{asset}: hard 5m push {'up' if body > 0 else 'down'} ({abs(body):.1f} = {abs(body) / adr:.2f} ADR), "
                           f"{done['open']} → {done['close']}{extra}; last {last}")
    return out


WINDOWS = (("08:20", "09:00"), ("09:20", "10:00"), ("10:20", "11:00"), ("13:20", "14:00"))   # Sharif's key windows, New York


def window(hhmm: str) -> str:
    """Where a New York time sits against his key windows (time is part of the context)."""
    for a, b in WINDOWS:
        if a <= hhmm < b:
            return f"inside the {a}–{b} window"
    nxt = next((a for a, _ in WINDOWS if a > hhmm), None)
    return f"between windows (next {nxt})" if nxt else "after the last window"


def conditions(c1: list[dict], n: int = 60) -> dict:
    """Is price going anywhere? Over the last ``n`` 1m candles: the net move against the distance travelled
    (sum of the candle bodies). Near 1 = one clean move, near 0 = chop. A first measure (Sharif 2026-11-17: know
    whether the market moves cleanly and fast enough to even consider a trade); not yet checked against his calls."""
    c = c1[-n:]
    if len(c) < 5:
        return {"score": None, "label": "unknown"}
    net = abs(c[-1]["close"] - c[0]["open"])
    path = sum(abs(x["close"] - x["open"]) for x in c) or 1e-9
    score = round(net / path, 2)
    return {"score": score, "net": round(net, 2), "travelled": round(path, 2),
            "label": "choppy" if score < 0.15 else "mixed" if score < 0.35 else "clean"}


def pools(c5: list[dict], adr: float, since: int | None = None) -> dict:
    """Liquidity created and still resting on the 5m: groups of two or more swing highs (lows) within 0.02 ADR of
    each other that no later candle has traded beyond. ``since`` = only swings from that time on."""
    c = [x for x in c5 if since is None or x["time"] >= since]
    out = {"highs": [], "lows": []}
    for name, key, sgn in (("highs", "high", 1), ("lows", "low", -1)):
        sw = sorted(((x["time"], x[key]) for i, x in enumerate(c) if 0 < i < len(c) - 1
                     and sgn * x[key] >= sgn * c[i - 1][key] and sgn * x[key] >= sgn * c[i + 1][key]), key=lambda q: q[1])
        groups: list[list] = []
        for q in sw:
            if groups and abs(q[1] - groups[-1][-1][1]) <= 0.02 * adr:
                groups[-1].append(q)
            else:
                groups.append([q])
        for g in groups:
            ext = max(q[1] for q in g) if sgn > 0 else min(q[1] for q in g)
            last_t = max(q[0] for q in g)
            if len(g) >= 2 and not any(sgn * x[key] > sgn * ext for x in c if x["time"] > last_t):
                out[name].append({"from": min(q[1] for q in g), "to": max(q[1] for q in g), "count": len(g)})
    return out


def summary(doc: dict, overlay: dict, state: dict | None = None) -> str:
    """A short text picture of the three indices for the checker: conditions, liquidity eaten and created, prices,
    recent candles, Claude's marks and read."""
    hm = lambda t: datetime.fromtimestamp(t, ZoneInfo("UTC")).strftime("%H:%M")  # noqa: E731  (candle times are NY wall clock)
    out = [f"Now: {doc.get('now')} New York, {window(str(doc.get('now', ''))[-5:])}. Prep: {overlay.get('at')}"]
    for asset, item in doc.get("assets", {}).items():
        c = item.get("candles", {})
        row = lambda xs: " | ".join(f"{hm(x['time'])} o{x['open']} h{x['high']} l{x['low']} c{x['close']}" for x in xs)  # noqa: E731
        ov = overlay.get(asset, {})
        if ov.get("watch") is False:                             # on the page for looking only
            continue
        cond = conditions(c.get("1m") or [])
        pl = pools((c.get("5m") or [])[-72:], item.get("adr") or 1e9)
        taken = [k.split("|", 1)[1] for k in (state or {}).get("fired", []) if k.startswith(asset + "|")]
        fmt = lambda xs: ", ".join(f"{x['from']}–{x['to']} x{x['count']}" for x in xs) or "none"  # noqa: E731
        out += [f"\n## {asset}: last {item.get('last')}, ADR {item.get('adr')}, levels {item.get('levels')}",
                "The trade in view: " + ("; ".join(f"{k} {v}" for k, v in (ov.get("idea") or {}).items()) or "none named"),
                f"Conditions, last hour of 1m candles: {cond['label']} (net {cond.get('net')} against {cond.get('travelled')} travelled, score {cond['score']})",
                f"Eaten since the prep (marked levels and zones price has traded): {'; '.join(taken) or 'none'}",
                f"Created and still resting on the 5m (equal highs): {fmt(pl['highs'])}; (equal lows): {fmt(pl['lows'])}",
                "5m (last 12): " + row((c.get("5m") or [])[-12:]), "15m (last 12): " + row((c.get("15m") or [])[-12:]),
                "1h (last 8): " + row((c.get("1h") or [])[-8:]),
                "Marked: " + "; ".join(f"{m.get('kind')} {m.get('price', (m.get('bottom'), m.get('top')))}" for m in ov.get("marks", []) if "p0" not in m),
                "Read: " + " ".join(ov.get("read", []))]
    return "\n".join(out)


def parse_state(reply: str) -> list[str]:
    """The checker's one line per index on conditions, eaten and created (lines starting STATE); kept for the page,
    never a reason to wake Fable."""
    return [ln.strip()[5:].lstrip(": ").strip() for ln in reply.splitlines() if ln.strip().upper().startswith("STATE")]


def parse_checker(reply: str) -> list[str]:
    """The checker's escalations (lines starting ESCALATE); anything else, including OK, is nothing."""
    return [ln.strip() for ln in reply.splitlines() if ln.strip().upper().startswith("ESCALATE")]


def ask_checker(text: str, model: str = "sonnet", rules: Path = Path("research/hunt-rules.md")) -> str:
    """One small call to a cheaper model, from an empty folder so no project context is loaded. It sees only the
    rules and the summary, and answers OK or ESCALATE lines."""
    prompt = (rules.read_text() + "\n\n---\nThe current picture:\n\n" + text
              + "\n\nAnswer now: first one `STATE: <index>: <clean | mixed | choppy>; eaten: ...; created: ...` line per index, "
                "then exactly `OK`, or one `ESCALATE: ...` line per thing Fable should look at.")
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["claude", "-p", "--model", model, "--max-turns", "1"], input=prompt, capture_output=True, text=True, timeout=120, cwd=tmp)
    return r.stdout


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
                    reply = ask_checker(summary(doc, overlay, state), a.checker_model)
                    state["checker"] = {"at": doc["now"][-5:], "state": parse_state(reply)}      # shown on the page
                    lines += [f"checker ({a.checker_model}) {x}" for x in parse_checker(reply)]
                except Exception as e:
                    lines.append(f"checker failed: {type(e).__name__}: {e}")
            state["conditions"] = {k: conditions(v.get("candles", {}).get("1m") or []) for k, v in doc.get("assets", {}).items()}
            state["beat"] = int(_time.time())                     # the pages show the hunt as watched while this is fresh
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
