"""Bias on one timeframe, the way Sharif re-taught it on 17 Nov 2026 (memory ``bias-reading``; playbook "Bias: how to
read it"). It describes; it never opens a trade. v2: the tool for concept 01, bias. The why is in lesson.md beside this file.

Three things per timeframe:
  * the break that put the bias where it is: a candle CLOSES through a significant high or low (he: "a body close;
    some form of body needs to do it, not wick");
  * the level below it (above, for a bear): the extreme of the pullback that break was built on. A close through it is
    the change. Nothing else is: not a wick, not a broken minor swing, not a failure at the level ahead;
  * the level ahead: breaking it continues the trend and moves the level below up to the newest pullback's extreme.

"Significant" is not a fitted threshold. This reading of it is mine, not his (it is named as mine in lesson.md): His words: "higher TF highs and lows have higher importance", so a level is
significant when it is a swing high or low of the timeframe ABOVE (a candle whose high is above both neighbours'; known
only once the next higher-timeframe candle has closed). Swings of the timeframe being read are the smaller pieces and
never move the bias. There are no prices, times or favourite timeframes in here, and no margins.

This is a second opinion beside the hand read, never a replacement: he reads significance by eye and can weigh a level
this rule cannot.

Candles are dicts with ``time`` (epoch seconds of the open), ``high``, ``low``, ``close``, oldest first, completed.
"""
from __future__ import annotations

from statistics import median


def _step(c: list[dict]) -> float:
    d = [b["time"] - a["time"] for a, b in zip(c, c[1:])]
    return median(d) if d else 0.0


def completed(c: list[dict], now: float) -> list[dict]:
    """Only the candles that have closed by ``now`` (epoch seconds): the one still forming is never read."""
    step = _step(c)
    return [x for x in c if x["time"] + step <= now]


def as_line(c: list[dict]) -> list[dict]:
    """The same candles as a line chart of their closes: each candle's high and low become its close. He, 19 Nov 2026:
    "when looking at bias, try using line chart; it focuses on body only, and body is strength." Read this way, a
    turn is a turn of the closes and a wick is never part of a level."""
    return [{**x, "open": x["close"], "high": x["close"], "low": x["close"]} for x in c]


def swings(c: list[dict]) -> tuple[list[dict], list[dict]]:
    """Swing highs and lows of a candle list: ``{"t": time of the swing candle, "price", "known": time it became known}``.
    A swing is known when the candle after it has closed (no look-ahead)."""
    step, hi, lo = _step(c), [], []
    for i in range(1, len(c) - 1):
        known = c[i + 1]["time"] + step
        if c[i]["high"] > c[i - 1]["high"] and c[i]["high"] > c[i + 1]["high"]:
            hi.append({"t": c[i]["time"], "price": c[i]["high"], "known": known})
        if c[i]["low"] < c[i - 1]["low"] and c[i]["low"] < c[i + 1]["low"]:
            lo.append({"t": c[i]["time"], "price": c[i]["low"], "known": known})
    return hi, lo


def bias_levels(c: list[dict], parent: list[dict] | None = None, grand: list[dict] | None = None) -> dict:
    """Walk the candles of one timeframe against the swings of the timeframe above (``parent``; the candles' own swings
    when there is none above) and, when given, of the one above that (``grand``). He, 19 Nov 2026: "it's relative to
    what you're looking at: if you're on daily, obviously weekly and monthly is stronger; if you're on hourly, 4-hour and
    daily is stronger… depending on where you're trading there is a limit, so 2 up makes sense." Which candles are
    "one up" and "two up" is the caller's choice; no timeframe is named in here. Returns::

        {"side": "bull" | "bear" | "neutral",
         "since": time of the candle that changed the bias (None while neutral),
         "break": {"t", "price"}       the latest break in the bias's direction (the first one or a continuation),
         "change": {"t", "price"}      the level behind the bias: a close through it is the change,
         "ahead": {"t", "price"} | None   the next significant level in the bias's direction, not yet closed through,
         "events": [{"t", "kind": "change" | "continue" | "first", "side", "price"}]}
    """
    step = _step(c)
    ph, pl = swings(parent if parent else c)
    if grand:                                # a level that turns the timeframe two up counts too, from when it is known there
        gh, gl = swings(grand)
        ph, pl = sorted(ph + gh, key=lambda v: v["known"]), sorted(pl + gl, key=lambda v: v["known"])
    side, since, brk, change, events = "neutral", None, None, None, []
    open_h: list[dict] = []          # significant highs known and not yet closed through
    open_l: list[dict] = []
    ih = il = 0
    # The pullback a coming change would be built on. While the bias is bear, a close above a significant high that
    # sits under the level behind starts a structure of its own: the lowest low since that high is the pullback. If the
    # level behind is then closed through, THAT low is the new level behind, not the lowest low of the whole fall
    # (he, 19 Nov 2026, on a chart where the two differ: the level behind is the low of the pullback the break was built
    # on). How the pullback is found is mine: the oldest high closed through on that candle, and the pullback is dropped
    # if a later candle closes back beyond it.
    pend_low: dict | None = None
    pend_high: dict | None = None

    def extreme(t0: float, k: int, low: bool) -> dict:
        """The lowest low (highest high) of this timeframe from ``t0`` up to candle ``k``: the pullback the break was built on."""
        seg = [x for x in c[: k + 1] if x["time"] + step > t0] or [c[k]]
        x = min(seg, key=lambda v: v["low"]) if low else max(seg, key=lambda v: v["high"])
        return {"t": x["time"], "price": x["low"] if low else x["high"]}

    for k, x in enumerate(c):
        closed_at = x["time"] + step
        while ih < len(ph) and ph[ih]["known"] <= closed_at:
            open_h.append(ph[ih])
            ih += 1
        while il < len(pl) and pl[il]["known"] <= closed_at:
            open_l.append(pl[il])
            il += 1
        up = [h for h in open_h if x["close"] > h["price"]]
        dn = [lv for lv in open_l if x["close"] < lv["price"]]
        open_h = [h for h in open_h if h not in up]
        open_l = [lv for lv in open_l if lv not in dn]
        if pend_low and x["close"] < pend_low["price"]:
            pend_low = None
        if pend_high and x["close"] > pend_high["price"]:
            pend_high = None
        if side == "bear":                   # only highs made on the way back up, after the low of the fall
            turn = extreme(change["t"], k, low=True)["t"]
            inner = [h for h in up if h["price"] < change["price"] and h["t"] > turn]
            if inner:
                pend_low = extreme(min(inner, key=lambda v: v["t"])["t"], k, low=True)
        elif side == "bull":
            turn = extreme(change["t"], k, low=False)["t"]
            inner = [lv for lv in dn if lv["price"] > change["price"] and lv["t"] > turn]
            if inner:
                pend_high = extreme(min(inner, key=lambda v: v["t"])["t"], k, low=False)

        if side == "bull" and x["close"] < change["price"]:              # the level below closed through: the change
            origin = change
            side, since, brk = "bear", x["time"], {"t": x["time"], "price": origin["price"]}
            change = pend_high or extreme(origin["t"], k, low=False)      # the high that break down was built on
            pend_low = pend_high = None
            events.append({"t": x["time"], "kind": "change", "side": "bear", "price": origin["price"]})
        elif side == "bear" and x["close"] > change["price"]:
            origin = change
            side, since, brk = "bull", x["time"], {"t": x["time"], "price": origin["price"]}
            change = pend_low or extreme(origin["t"], k, low=True)
            pend_low = pend_high = None
            events.append({"t": x["time"], "kind": "change", "side": "bull", "price": origin["price"]})
        elif side == "neutral" and (up or dn):                           # the first significant level closed through
            if up:
                h = max(up, key=lambda v: v["price"])
                side, brk, change = "bull", {"t": x["time"], "price": h["price"]}, extreme(h["t"], k, low=True)
            else:
                h = min(dn, key=lambda v: v["price"])
                side, brk, change = "bear", {"t": x["time"], "price": h["price"]}, extreme(h["t"], k, low=False)
            since = x["time"]
            events.append({"t": x["time"], "kind": "first", "side": side, "price": h["price"]})
        elif side == "bull" and up:
            # only the level ahead continues the trend: the top since the last break. A lower high closed through is a
            # smaller piece (price failed at the level ahead and is still under it).
            h = max(up, key=lambda v: v["price"])
            if h["price"] >= max((v["price"] for v in ph[:ih] if v["t"] >= brk["t"]), default=h["price"]):   # the highest significant high since the break (a wick past it earlier does not count)
                change = extreme(max(h["t"], brk["t"]), k, low=True)
                brk = {"t": x["time"], "price": h["price"]}
                events.append({"t": x["time"], "kind": "continue", "side": "bull", "price": h["price"]})
        elif side == "bear" and dn:
            lv = min(dn, key=lambda v: v["price"])
            if lv["price"] <= min((v["price"] for v in pl[:il] if v["t"] >= brk["t"]), default=lv["price"]):
                change = extreme(max(lv["t"], brk["t"]), k, low=False)
                brk = {"t": x["time"], "price": lv["price"]}
                events.append({"t": x["time"], "kind": "continue", "side": "bear", "price": lv["price"]})

    ahead = None                 # the highest significant high (lowest low) since the last break; the plain extreme if none is known yet
    if side in ("bull", "bear"):
        sig = [v for v in (ph[:ih] if side == "bull" else pl[:il]) if v["t"] >= brk["t"]]
        best = (max if side == "bull" else min)(sig, key=lambda v: v["price"]) if sig else None
        ahead = {"t": best["t"], "price": best["price"]} if best else extreme(brk["t"], len(c) - 1, low=side == "bear")
    return {"side": side, "since": since, "break": brk, "change": change, "ahead": ahead, "events": events}
