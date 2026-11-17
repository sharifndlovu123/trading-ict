"""Eyes of the hunting brain: turn a chart into typed observations, the same way at every look.

Sharif 2026-11-17. Two things shaped this file:
  - I only found what I thought to ask the data for, so the asking is fixed here and runs the same every time.
  - "Don't ever try to lock down time and timeframes to what I mention... it's a different snowflake." So NOTHING
    here knows a price, a clock time or a favourite timeframe. Every timeframe is read by the same code, and every
    size is measured against that timeframe's own typical candle, never against a number taken from an example.

It serves the five judgements he wants made from the chart itself in a hunt:
  1. is price choppy          `cond.*`   net move against distance travelled, per timeframe
  2. what is the bias         `bias.*`   the last two swing highs and lows, per timeframe
  3. the areas of interest    `gap.*`, `block.*`, `liq.*`   and how each has been treated on its OWN timeframe
                              (untouched / wicked = wicks in, no body / body_inside / flipped / flipped_retest)
  4. any recent displacement  `displacement*`   a candle far larger than its timeframe's usual, going one way
  5. is price volatile        `vol.*`    recent candles against the timeframe's usual, and the day against its average

Each observation has a `type` (what the lesson graph links on), a `tf`, prices, times, a plain `text`, and a `weight`
(nearer, fresher, higher timeframe = heavier) so a reader can take the top few. It does not judge what matters.

    uv run python research/scripts/hunt_scan.py US100                 # now
    uv run python research/scripts/hunt_scan.py US100 --at 03:52      # the day as it stood at that minute
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))    # the engine's structure rule lives in ict_engine

import hunt_watch as hw  # noqa: E402
import live_snapshot as ls  # noqa: E402

TFS = ["1m", "5m", "15m", "1h", "4h", "1D", "1W", "1M"]
RANK = {t: i for i, t in enumerate(TFS)}
BACK = 150            # candles read back on any timeframe
NEAR = 14             # an area counts as near while it is within this many typical candles of price
GAP_MIN = 0.15        # a gap smaller than this share of a typical candle is noise
EQ_TOL = 0.2          # equal highs / lows: within this share of a typical candle of each other
GROUP_GAP = 8         # ...and no more than this many candles after the previous one in its group
GROUP_SPAN = 20       # a group is one small stretch of price action, at most this many candles long
REACH_ADR = 1.0       # keep to where price is NOW: areas and liquidity within this many average days' ranges (or holding price)
DISP = 2.2            # a displacement candle's body against the usual body on its timeframe
RECENT = 8            # "recent" = within this many closed candles, on whichever timeframe


def hm(t: int, tf: str = "5m") -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%H:%M" if RANK.get(tf, 0) <= 2 else "%a %d %H:%M" if RANK[tf] <= 4 else "%d %b %y")


def _body(c):
    return min(c["open"], c["close"]), max(c["open"], c["close"])


def typical(c: list[dict], n: int = 40) -> float:
    """The usual candle range on this timeframe: the yardstick every size on it is measured with."""
    r = [x["high"] - x["low"] for x in c[-n:] if x["high"] > x["low"]]
    return median(r) if r else 0.0


def _w(tf: str, dist: float, typ: float, age: int = 0) -> float:
    near = max(0.15, 1 - dist / (NEAR * typ)) if typ else 0.15
    return round((1 + RANK[tf]) * near * max(0.3, 1 - age / BACK), 2)


def gaps(c: list[dict], tf: str, last: float, reach: float | None = None) -> list[dict]:
    typ, out = typical(c), []
    reach = reach if reach is not None else NEAR * typ
    for i in range(max(2, len(c) - BACK), len(c)):
        a, b = c[i - 2], c[i]
        for side, lo, hi in (("bull", a["high"], b["low"]), ("bear", b["high"], a["low"])):
            if hi - lo < GAP_MIN * typ:
                continue
            dist = 0 if lo <= last <= hi else min(abs(lo - last), abs(hi - last))
            if dist > reach:
                continue
            after = c[i + 1:]
            wick = [k for k in after if k["low"] < hi and k["high"] > lo]
            bodies = [k for k in after if _body(k)[0] < hi and _body(k)[1] > lo]
            ti = next((n for n, k in enumerate(after) if (k["close"] < lo if side == "bull" else k["close"] > hi)), None)
            state, extra = "untouched", "; not revisited"
            if ti is not None:
                later = after[ti + 1:]
                if any((k["close"] > hi if side == "bull" else k["close"] < lo) for k in later):
                    continue                                    # closed through and back again: it no longer says anything
                back = [k for k in later if (k["high"] > lo if side == "bull" else k["low"] < hi)]
                state = "flipped_retest" if back else "flipped"
                extra = f"; a {tf} candle closed through it at {hm(after[ti]['time'], tf)}" + (
                    f", and it has been tested from the other side {len(back)} time(s) with no close back through" if back else "")
            elif bodies:
                state, extra = "body_inside", f"; {len(bodies)} {tf} bodies inside, none closed through"
            elif wick:
                state, extra = "wicked", f"; {len(wick)} {tf} wick(s) in, no body: respected so far"
            out.append({"type": f"gap.{state}", "tf": tf, "side": side, "bottom": lo, "top": hi, "mid": round((lo + hi) / 2, 5),
                        "t0": c[i - 1]["time"], "weight": _w(tf, dist, typ, len(c) - i),
                        "text": f"{tf} {'bullish' if side == 'bull' else 'bearish'} gap {lo}–{hi} from {hm(c[i - 1]['time'], tf)}{extra}"})
    return out


def liquidity(c: list[dict], tf: str, last: float, reach: float | None = None) -> list[dict]:
    """Equal highs / lows, each belonging to ONE sub-group of candles (Sharif 2026-11-17: "EQHs are relative to a sub
    group, not for an area... always relative to the group"). Swing highs count as equal only when they sit next to
    each other in time, inside the same small stretch of price action; highs that merely share a price weeks apart
    are separate stories. Each group is created and still resting, or eaten (when, and did that candle close back)."""
    c = c[-BACK:]
    typ, out = typical(c), []
    reach = reach if reach is not None else NEAR * typ
    for side, key, sgn in (("highs", "high", 1), ("lows", "low", -1)):
        sw = [(n, x[key]) for n, x in enumerate(c) if 0 < n < len(c) - 1
              and sgn * x[key] >= sgn * c[n - 1][key] and sgn * x[key] >= sgn * c[n + 1][key]]          # in time order
        groups: list[list] = []
        for q in sw:
            g = groups[-1] if groups else None
            between = c[g[-1][0] + 1:q[0]] if g else []
            same = (g is not None and q[0] - g[-1][0] <= GROUP_GAP and q[0] - g[0][0] <= GROUP_SPAN
                    and abs(q[1] - g[0][1]) <= EQ_TOL * typ and not any(sgn * k[key] > sgn * max(g[0][1], q[1], key=lambda v: sgn * v) for k in between))
            if same:
                g.append(q)
            else:
                groups.append([q])
        for g in groups:
            if len(g) < 2:
                continue
            ext = max(q[1] for q in g) if sgn > 0 else min(q[1] for q in g)
            n_last, n_first = g[-1][0], g[0][0]
            lo, hi = min(q[1] for q in g), max(q[1] for q in g)
            eat = next((n for n in range(n_last + 1, len(c)) if sgn * c[n][key] > sgn * ext), None)
            base = {"tf": tf, "side": side, "bottom": lo, "top": hi, "price": ext, "count": len(g), "t0": c[n_first]["time"], "t_last": c[n_last]["time"],
                    "t_end": c[min(n_last + 1, len(c) - 1)]["time"]}
            if abs(ext - last) > reach:
                continue                                        # keep to where price is now
            if eat is None:
                out.append({**base, "type": "liq.created", "weight": round(_w(tf, abs(ext - last), typ, len(c) - n_last) * (1 + 0.15 * len(g)), 2),
                            "text": f"{tf} equal {side} {lo}–{hi} (x{len(g)}, one group, {hm(base['t0'], tf)} to {hm(base['t_last'], tf)}): created, still resting"})
            elif len(c) - eat <= 30:                            # eaten recently enough to still be news
                k = c[eat]
                back = sgn * k["close"] < sgn * ext
                out.append({**base, "type": "liq.eaten", "t1": k["time"], "extreme": k[key], "closed_back": back,
                            "weight": round(_w(tf, abs(ext - last), typ, len(c) - eat) * (1 + 0.15 * len(g)), 2),
                            "text": f"{tf} equal {side} {lo}–{hi} (x{len(g)}, one group): eaten at {hm(k['time'], tf)} to {k[key]}; "
                                    + ("that candle closed back: a wick" if back else "that candle closed beyond: a body")})
    return out


def against_areas(liq: list[dict], gps: list[dict], typ: dict[str, float]) -> list[dict]:
    """Liquidity built against, or swept into, a gap of a HIGHER timeframe that still stands."""
    out = []
    for p in liq:
        want = "bear" if p["side"] == "highs" else "bull"
        tol = 0.4 * typ.get(p["tf"], 0)
        for g in gps:
            if g["side"] != want or RANK[g["tf"]] <= RANK[p["tf"]] or g["type"].startswith("gap.flipped"):
                continue
            edge = g["bottom"] if want == "bear" else g["top"]
            if not (abs(p["price"] - edge) <= tol or g["bottom"] <= p["price"] <= g["top"]):
                continue
            where = f"the {g['tf']} {'bearish' if want == 'bear' else 'bullish'} gap {g['bottom']}–{g['top']}"
            if p["type"] == "liq.created":
                out.append({**p, "type": "liq.created_against_area", "area": [g["bottom"], g["top"]], "area_tf": g["tf"], "weight": round(p["weight"] * 1.6, 2),
                            "text": p["text"].replace(": created, still resting", "") + f": created against {where}"})
            elif g["bottom"] - tol <= p["extreme"] <= g["top"] + tol:
                out.append({**p, "type": "liq.swept_into_area", "area": [g["bottom"], g["top"]], "area_tf": g["tf"], "weight": round(p["weight"] * 1.8, 2),
                            "text": p["text"] + f"; swept into {where}"})
    return out


def displacements(c: list[dict], tf: str, liq: list[dict], gps: list[dict]) -> list[dict]:
    """A closed candle far larger than its timeframe's usual body, going one way."""
    closed = c[:-1]
    bodies = [abs(x["close"] - x["open"]) for x in closed[-45:-1] if x["close"] != x["open"]]
    if len(bodies) < 8:
        return []
    usual, typ, out = median(bodies), typical(closed), []
    step = median([b["time"] - a["time"] for a, b in zip(closed[-20:], closed[-19:])]) if len(closed) > 20 else 0
    for i in range(max(8, len(closed) - RECENT), len(closed)):
        x = closed[i]
        if closed[-1]["time"] - x["time"] > max(2 * step, 2 * 86400):   # recent = the last two days, or the last two candles on a larger timeframe
            continue
        body, rng = x["close"] - x["open"], x["high"] - x["low"]
        if not rng or abs(body) < DISP * usual or abs(body) / rng < 0.6:
            continue
        down, prev, nxt = body < 0, closed[i - 1], c[i + 1] if i + 1 < len(c) else None
        ref = closed[max(0, i - 7):i]
        bos = x["close"] < min(k["low"] for k in ref) if down else x["close"] > max(k["high"] for k in ref)
        age = len(closed) - 1 - i
        base = {"tf": tf, "side": "down" if down else "up", "t0": x["time"], "t1": x["time"] + step, "p0": x["open"], "p1": x["close"], "bos": bos,
                "weight": round((1 + RANK[tf]) * (1.4 if bos else 1.0) * max(0.3, 1 - age / RECENT) * 1.5, 2)}
        out.append({**base, "type": "displacement", "times_usual": round(abs(body) / usual, 1),
                    "text": f"{tf} displacement {'down' if down else 'up'} at {hm(x['time'], tf)}: {x['open']} → {x['close']}, "
                            f"{abs(body) / usual:.1f} times the usual {tf} body" + ("; it broke the recent structure" if bos else "")})
        if nxt is not None:
            gap = (nxt["high"], prev["low"]) if down and prev["low"] > nxt["high"] else (prev["high"], nxt["low"]) if not down and prev["high"] < nxt["low"] else None
            if gap and max(gap) - min(gap) >= GAP_MIN * typ:
                out.append({**base, "type": "displacement.left_gap", "bottom": min(gap), "top": max(gap),
                            "text": f"that {tf} displacement left a gap {min(gap)}–{max(gap)}; a return to it is a place to look"})
        opp = [p for p in liq if abs(RANK[p["tf"]] - RANK[tf]) <= 1 and p["side"] == ("highs" if down else "lows") and p["t_last"] < x["time"]
               and x["time"] - p["t_last"] <= 40 * step and (p["type"] == "liq.created" or p.get("t1", 0) > x["time"]) and abs(p["price"] - x["open"]) <= 8 * typ]
        if opp:
            p = max(opp, key=lambda q: q["count"])
            out.append({**base, "type": "displacement.after_created_liq", "price": p["price"],
                        "text": f"before it, {p['tf']} equal {p['side']} had been created at {p['bottom']}–{p['top']} (x{p['count']}) and were left: created, then displaced the other way"})
        for g in gps:                                            # did it close beyond the middle of a larger gap it started in?
            if RANK[g["tf"]] > RANK[tf] and g["bottom"] <= x["open"] <= g["top"] and ((down and x["close"] < g["mid"]) or (not down and x["close"] > g["mid"])):
                out.append({**base, "type": "displacement.beyond_mid_of_higher_gap", "area": [g["bottom"], g["top"]], "area_tf": g["tf"],
                            "text": f"it started inside the {g['tf']} gap {g['bottom']}–{g['top']} and closed beyond its middle ({g['mid']})"})
                break
    return out


def blocks(c: list[dict], tf: str, last: float, reach: float | None = None) -> list[dict]:
    """Order blocks by his reading: the last opposite candle engulfed by the very next one, its body."""
    closed, out = c[:-1], []
    typ = typical(closed)
    reach = reach if reach is not None else NEAR * typ
    for i in range(max(0, len(closed) - 60), len(closed) - 1):
        b, e = closed[i], closed[i + 1]
        rng = b["high"] - b["low"]
        lo, hi = _body(b)
        side = "sell" if b["close"] > b["open"] and e["close"] < b["open"] else "buy" if b["close"] < b["open"] and e["close"] > b["open"] else None
        dist = min(abs(lo - last), abs(hi - last))
        if not side or not rng or hi - lo < GAP_MIN * typ or dist > reach:
            continue
        after = closed[i + 2:]
        if any((k["close"] > hi if side == "sell" else k["close"] < lo) for k in after):
            continue                                            # a close beyond its far edge: gone
        pct, mid = round(100 * (hi - lo) / rng), (lo + hi) / 2
        inside = [k for k in after if lo <= k["close"] <= hi]
        touched = [k for k in after if k["high"] >= lo and k["low"] <= hi]
        state = "weakened" if inside else "middle_hit" if any(k["low"] <= mid <= k["high"] for k in after) else "wicked" if touched else "untouched"
        grade = "clean" if pct >= 50 else "dim"
        out.append({"type": f"block.{state}", "tf": tf, "side": side, "bottom": lo, "top": hi, "mid": round(mid, 5), "t0": b["time"], "grade": grade,
                    "weight": round(_w(tf, dist, typ, len(closed) - i) * (1.0 if grade == "clean" else 0.6), 2),
                    "text": f"{tf} {side} order block {lo}–{hi} from {hm(b['time'], tf)} ({grade}: {pct}% body); "
                            + {"weakened": f"a {tf} candle has closed inside it: weaker", "middle_hit": "its middle has been reached",
                               "wicked": "wicked only", "untouched": "not revisited"}[state]})
    return out


def bias(c: list[dict], tf: str) -> dict | None:
    """Structure on this timeframe, by the rule Sharif taught and checked on 16 Nov 2026 (it is not the last two swings):
    the trend holds until a candle of this timeframe CLOSES through the protected level, an intermediate-term swing;
    higher highs under a protected lower high are shifts inside a bear trend, not a change; a wick through it with the
    close back inside changes nothing; a weak close through it is a range. (`context.weekly_structure_state`, the same
    code on every timeframe, margins in that timeframe's own ATR.)"""
    import pandas as pd
    from ict_engine.concepts.context import weekly_structure_state
    if len(c) < 30:
        return None
    f = pd.DataFrame({k: [x[k] for x in c] for k in ("high", "low", "close")}, index=[x["time"] for x in c])
    state, guard, flips = weekly_structure_state(f)
    if state == "neutral" or guard is None:
        return {"type": "bias.neutral", "tf": tf, "side": "neutral", "weight": 1 + RANK[tf],
                "text": f"{tf}: no structure break yet in the candles I have ({len(c)})"}
    since, prot = flips[-1][0], "lower high" if state == "bear" else "higher low"
    return {"type": f"bias.{state}", "tf": tf, "side": state, "guard": float(guard), "since": int(since), "weight": 1 + RANK[tf],
            "text": f"{tf}: {state} since {hm(int(since), tf)}; protected {prot} {guard:.5g}. Until a {tf} candle closes "
                    f"{'above' if state == 'bear' else 'below'} it, moves the other way are shifts inside the {state} trend, not a change"}


def conditions(c: list[dict], tf: str, n: int = 24) -> dict | None:
    """Choppy or going somewhere, on this timeframe: the net move of the last ``n`` closed candles against the distance travelled."""
    k = c[:-1][-n:]
    if len(k) < 8:
        return None
    net = abs(k[-1]["close"] - k[0]["open"])
    path = sum(abs(x["close"] - x["open"]) for x in k) or 1e-9
    score = round(net / path, 2)
    label = "choppy" if score < 0.15 else "mixed" if score < 0.35 else "clean"
    return {"type": f"cond.{label}", "tf": tf, "score": score, "weight": 1 + RANK[tf],
            "text": f"{tf}, last {len(k)} candles: {label} (ended {net:.5g} from where it started after travelling {path:.5g}; score {score})"}


def volatility(c: list[dict], tf: str) -> dict | None:
    """Are the recent candles on this timeframe larger or smaller than its usual?"""
    k = c[:-1]
    if len(k) < 40:
        return None
    usual, recent = typical(k[:-8], 60), median([x["high"] - x["low"] for x in k[-8:]])
    if not usual:
        return None
    r = round(recent / usual, 2)
    label = "expanding" if r >= 1.5 else "quiet" if r <= 0.6 else "normal"
    return {"type": f"vol.{label}", "tf": tf, "ratio": r, "weight": 1 + RANK[tf],
            "text": f"{tf} candles lately are {r} times their usual size: {label}"}


NAMED = {"pdh": ("previous day's high", "highs"), "pdl": ("previous day's low", "lows"), "pwh": ("previous week's high", "highs"),
         "pwl": ("previous week's low", "lows"), "pmh": ("previous month's high", "highs"), "pml": ("previous month's low", "lows"),
         "asia_high": ("Asia high", "highs"), "asia_low": ("Asia low", "lows"), "london_high": ("London high", "highs"), "london_low": ("London low", "lows")}


def named_levels(levels: dict, today: list[dict], last: float, reach: float | None) -> list[dict]:
    """The named highs and lows the feed already knows (previous day / week, the sessions) as liquidity: resting, or
    taken since the day's open (by a wick so far, or with a close beyond)."""
    out = []
    for key, price in (levels or {}).items():
        if key not in NAMED or price is None or (reach is not None and abs(price - last) > reach):
            continue
        name, side = NAMED[key]
        sgn = 1 if side == "highs" else -1
        hit = next((k for k in today if sgn * (k["high"] if sgn > 0 else k["low"]) > sgn * price), None)
        base = {"tf": "1D" if key[:2] in ("pd", "pw", "pm") else "1h", "side": side, "price": price, "name": name, "t0": today[0]["time"] if today else None,
                "weight": round(4 * max(0.2, 1 - abs(price - last) / reach) if reach else 2, 2)}
        if hit is None:
            out.append({**base, "type": "level.resting", "text": f"{name} {price}: not taken today, resting"})
        else:
            beyond = any(sgn * k["close"] > sgn * price for k in today if k["time"] >= hit["time"])
            out.append({**base, "type": "level.taken", "t1": hit["time"], "closed_beyond": beyond,
                        "text": f"{name} {price}: taken today at {hm(hit['time'], '1m')}"
                                + ("; lower-timeframe candles have closed beyond it" if beyond else "; wicks only so far")})
    return out


def scan(doc: dict, asset: str) -> list[dict]:
    """Every observation for one instrument at the moment of ``doc``, heaviest first."""
    it = doc["assets"][asset]
    C, last = it["candles"], it["last"]
    out: list[dict] = []
    now = str(doc.get("now", ""))[-5:]
    out.append({"type": "time.in_window" if "inside" in hw.window(now) else "time.outside_window", "tf": "", "weight": 1,
                "text": f"{now} New York, {hw.window(now)}"})
    gps, liq, typ = [], [], {}
    reach = REACH_ADR * it["adr"] if it.get("adr") else None      # one yardstick for "near", whatever the timeframe: the instrument's own average day
    for tf in TFS:
        c = C.get(tf) or []
        closed = c[:-1]                                          # the last candle on any timeframe is still forming
        if len(closed) < 6:
            continue
        typ[tf] = typical(closed)
        gps += gaps(closed, tf, last, reach)
        liq += liquidity(closed, tf, last, reach)
        out += blocks(c, tf, last, reach)
        for f in (bias(closed, tf), conditions(c, tf), volatility(c, tf)):
            if f:
                out.append(f)
    out += gps + liq + against_areas(liq, gps, typ)
    out += named_levels(it.get("levels") or {}, C.get("1m") or [], last, reach)
    for tf in TFS:
        if len(C.get(tf) or []) > 12:
            out += [x for x in displacements(C[tf], tf, liq, gps) if reach is None or min(abs(x["p0"] - last), abs(x["p1"] - last)) <= 1.5 * reach]
    day = (C.get("1D") or [None])[-1]
    if day and it.get("adr"):
        used = (day["high"] - day["low"]) / it["adr"]
        out.append({"type": "vol.day_used", "tf": "1D", "ratio": round(used, 2), "weight": 3,
                    "text": f"today has used {used:.2f} of an average day's range so far"})
    for x in [o for o in out if o["type"] == "displacement"]:    # did this displacement come out of chop on its own timeframe?
        before = [k for k in C.get(x["tf"]) or [] if k["time"] < x["t0"]][-25:]
        f = conditions(before + before[-1:], x["tf"]) if len(before) > 9 else None
        if f and f["type"] == "cond.choppy":
            out.append({"type": "cond.displacement_out_of_chop", "tf": x["tf"], "t0": x["t0"], "weight": x["weight"],
                        "text": f"the {x['tf']} displacement at {hm(x['t0'], x['tf'])} came out of a choppy stretch on that timeframe"})
    for tf in TFS[:-3]:                                          # a candle against the run, sitting in a standing gap
        c, b = C.get(tf) or [], next((x for x in out if x["type"] in ("bias.bear", "bias.bull") and RANK[x["tf"]] == RANK[tf] + 1), None)
        if len(c) < 3 or not b:
            continue
        k = c[-2]
        counter = k["close"] > k["open"] if b["side"] == "bear" else k["close"] < k["open"]
        g = next((g for g in gps if RANK[g["tf"]] >= RANK[tf] and k["low"] <= g["top"] and k["high"] >= g["bottom"] and g["type"] != "gap.untouched"), None)
        if counter and g:
            out.append({"type": "candle.counter_in_gap", "tf": tf, "t0": k["time"], "area": [g["bottom"], g["top"]], "area_tf": g["tf"], "weight": 2 + RANK[tf],
                        "text": f"the last closed {tf} candle ({hm(k['time'], tf)}) goes against the {b['tf']} structure ({b['side']}) and sits in the "
                                f"{g['tf']} gap {g['bottom']}–{g['top']} ({g['type'].split('.')[1].replace('_', ' ')}): look back at how that gap has been treated"})
    return sorted(out, key=lambda o: -o.get("weight", 0))


def select(obs: list[dict], last: float) -> dict[str, list[dict]]:
    """The observations that answer the five judgements (and liquidity), a few each. This only arranges what was
    seen; deciding what it means is the reader's job."""
    by = lambda *pre: [o for o in obs if o["type"].startswith(pre)]          # noqa: E731
    tfo = lambda xs: sorted(xs, key=lambda o: RANK.get(o["tf"], 0))          # noqa: E731
    lab = lambda xs: {"type": "summary", "tf": "", "text": ", ".join(f"{o['tf']} {o['type'].split('.')[1]}" for o in (xs if xs and xs[0]["type"].startswith("bias.") else tfo(xs))) or "nothing to go on"}   # noqa: E731
    cond = [o for o in by("cond.") if o["type"] in ("cond.choppy", "cond.mixed", "cond.clean")]
    out = {"choppy": [lab(cond)] + by("cond.displacement_out_of_chop")[:2],
           "bias": [{"type": "summary", "tf": "", "text": "Not read by the scan. Bias is read by hand at every prep, the way Sharif re-taught it on 17 Nov 2026: per timeframe, the break that set it, the level below (a close through it is the change) and the level ahead. See Claude's read. The fitted rule that was here got it wrong and is no longer shown."}]}
    areas = [o for o in by("gap.", "block.") if "bottom" in o]
    pick = []
    for tier in (("1M", "1W"), ("1D",), ("4h", "1h"), ("15m", "5m", "1m")):       # top-down (Sharif 16 Nov 2026: weekly first, then daily, ...; both sides, no forced draw)
        t = sorted((o for o in areas if o["tf"] in tier), key=lambda o: -RANK[o["tf"]])
        inside = [o for o in t if o["bottom"] <= last <= o["top"]][:1]
        above = sorted((o for o in t if o["bottom"] > last), key=lambda o: o["bottom"] - last)[:1]
        below = sorted((o for o in t if o["top"] < last), key=lambda o: last - o["top"])[:1]
        pick += inside + above + below
    out["areas"] = pick + by("liq.created_against_area", "liq.swept_into_area")[:3]
    disp, lines = by("displacement"), []
    for o in sorted((o for o in disp if o["type"] == "displacement"), key=lambda o: -o["weight"])[:3]:
        lines += sorted((x for x in disp if x.get("t0") == o["t0"] and x["tf"] == o["tf"]), key=lambda x: len(x["type"]))
    out["displacement"] = lines or [{"type": "summary", "tf": "", "text": "none recently on any timeframe"}]
    out["volatile"] = [lab([o for o in by("vol.") if o["type"] != "vol.day_used"])] + by("vol.day_used")
    pools = [o for o in obs if o["type"] in ("liq.created", "level.resting")]
    out["liquidity"] = (sorted((o for o in pools if o["side"] == "highs" and o["price"] > last), key=lambda o: o["price"] - last)[:2]       # the nearest two buyside above
                        + sorted((o for o in pools if o["side"] == "lows" and o["price"] < last), key=lambda o: last - o["price"])[:2]      # and the nearest two sellside below
                        + sorted((o for o in obs if o["type"] in ("liq.eaten", "level.taken")), key=lambda o: -o.get("t1", 0))[:4])
    return out


def judgements(obs: list[dict], last: float) -> dict[str, list[str]]:
    """The five things Sharif wants judged from the chart itself, each as a few plain lines taken from the scan."""
    def line(k, o):
        if k == "areas" and "bottom" in o and o["type"].startswith(("gap.", "block.")):
            return ("price is inside: " if o["bottom"] <= last <= o["top"] else "above: " if o["bottom"] > last else "below: ") + o["text"]
        return o["text"]
    return {k: [line(k, o) for o in v] for k, v in select(obs, last).items()}


GAP_WORD = {"untouched": "gap", "wicked": "gap · respected", "body_inside": "gap · bodies in", "flipped": "gap · flipped", "flipped_retest": "gap · flipped, retested"}


def to_mark(o: dict) -> dict | None:
    """One observation as a mark the page can draw (a zone, a level or an arrow), with a short name. No sentences on the chart."""
    t, tf = o["type"], o["tf"]
    base = {"by": "B", "tf": tf, "t0": o.get("t0"), "t1": None, "watch": False}
    hl = "EQH" if o.get("side") == "highs" else "EQL"
    lside = "buyside" if o.get("side") == "highs" else "sellside"
    if t.startswith("gap."):
        return {**base, "kind": f"{tf} {GAP_WORD[t[4:]]}", "side": "area", "top": o["top"], "bottom": o["bottom"]}
    if t.startswith("block."):
        return {**base, "kind": f"{tf} {o['side']} block" + (" (dim)" if o["grade"] == "dim" else "") + (" · weaker" if t.endswith("weakened") else ""),
                "side": "area", "top": o["top"], "bottom": o["bottom"]}
    if t == "liq.created":
        return {**base, "kind": f"{hl} x{o['count']}", "side": lside, "price": o["price"], "t1": o["t_end"]}
    if t == "liq.created_against_area":
        return {**base, "kind": f"{hl} x{o['count']} against {o['area_tf']} gap", "side": lside, "price": o["price"], "t1": o["t_end"]}
    if t in ("liq.eaten", "liq.swept_into_area"):
        how = "wick" if o["closed_back"] else "body"
        return {**base, "kind": f"{hl} eaten ({how})" + (f" into {o['area_tf']} gap" if t.endswith("area") else ""), "side": lside, "price": o["price"], "t1": o["t1"]}
    if t in ("level.resting", "level.taken"):
        short = "".join(w[0] for w in o["name"].replace("'s", "").split()).upper() if o["name"].startswith("previous") else o["name"]
        return {**base, "kind": short + (" taken" + ("" if o.get("closed_beyond") else " (wick)") if t.endswith("taken") else ""), "side": lside, "price": o["price"], "t1": o.get("t1")}
    if t in ("bias.bear", "bias.bull"):
        return {**base, "kind": f"{tf} protected {'high' if t.endswith('bear') else 'low'}", "side": "buyside" if t.endswith("bear") else "sellside", "price": o["guard"], "t0": o["since"]}
    if t == "displacement":
        return {**base, "kind": "displacement", "side": "", "p0": o["p0"], "p1": o["p1"], "t1": o.get("t1", o["t0"])}
    if t == "displacement.left_gap":
        return {**base, "kind": f"{tf} gap left by displacement", "side": "area", "top": o["top"], "bottom": o["bottom"]}
    return None


def layer(doc: dict) -> dict:
    """What the scan sees, per instrument, for the page: the five judgements as text and the picked observations as marks."""
    out = {"at": doc.get("now")}
    for asset, it in doc.get("assets", {}).items():
        try:
            obs = scan(doc, asset)
            sel = select(obs, it["last"])
            marks, seen = [], set()
            for o in [x for v in sel.values() for x in v]:
                m = to_mark(o)
                key = m and (m["kind"], m.get("price"), m.get("top"), m.get("p1"))
                if m and key not in seen:
                    seen.add(key)
                    marks.append(m)
            out[asset] = {"judgements": judgements(obs, it["last"]), "marks": marks, "count": len(obs)}
        except Exception as e:                                   # one instrument failing must not blank the others
            out[asset] = {"error": f"{type(e).__name__}: {e}", "marks": [], "judgements": {}}
    return out


def write_layer(doc: dict, folder: Path) -> None:
    tmp = folder / "brain.json.tmp"
    tmp.write_text(json.dumps(layer(doc)))
    tmp.replace(folder / "brain.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset")
    ap.add_argument("--at", help="New York time today, HH:MM: read the day as it stood then")
    ap.add_argument("--src", type=Path, default=Path("out/live/today.json"))
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--write", type=Path, help="write brain.json (every instrument) into this folder for the page to draw, e.g. out/live")
    ap.add_argument("--raw", action="store_true", help="the weighted observations themselves, not the five judgements")
    a = ap.parse_args()
    doc = json.loads(a.src.read_text())
    if a.at:
        doc = ls.cut(doc, ls.at_epoch(doc, a.at))
    if a.write:
        write_layer(doc, a.write)
        print(f"what the scan sees at {doc['now']} → {a.write / 'brain.json'}")
    obs = scan(doc, a.asset)
    if a.raw:
        for o in obs[:a.top]:
            print(f"{o.get('weight', 0):6.2f}  {o['type']:38s} {o['text']}")
        return
    print(f"{a.asset} at {doc['now']} New York, last {doc['assets'][a.asset]['last']}  ({len(obs)} observations)")
    names = {"choppy": "1. Choppy?", "bias": "2. Bias", "areas": "3. Areas of interest", "displacement": "4. Recent displacement", "volatile": "5. Volatile?", "liquidity": "Liquidity: created, eaten"}
    for k, lines in judgements(obs, doc["assets"][a.asset]["last"]).items():
        print("\n" + names[k])
        for ln in lines:
            print("  - " + ln)


if __name__ == "__main__":
    main()
