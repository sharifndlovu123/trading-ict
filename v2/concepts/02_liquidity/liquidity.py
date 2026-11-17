"""Liquidity, the way Sharif taught it on 17-18 Nov 2026 (lesson.md beside this file). A tool: candles in, a
description out. The top-down reading that uses it (the eyes) is built later.

His words this follows:
  * "buy stops above old highs, sell stops below old lows" (ICT);
  * "focus on if it was eaten first; if it wasn't eaten keep it" - eaten and swept are the same thing;
  * equal highs / lows "are just relatively close to each other; you could put a straight line at one point and the
    other point may not hit it but it's very close by";
  * "relative to where price currently is, we look at previous day and previous week for highs or lows that were left
    uneaten".

Candles are dicts with ``time``, ``open``, ``high``, ``low``, ``close``, oldest first.

Two choices here are mine, not his, and are named so they can be changed:
  * an "old high" is a candle whose high is above the highs of the candle before and after it (a turn), low likewise;
  * a high is eaten as soon as a later candle trades above it; a wick is enough (he did not say wick or close);
  * "very close by" is a distance the caller passes in (``near``). There is no built-in number;
  * equal highs are joined neighbour to neighbour, so a long group can be wider end to end than ``near``.
"""
from __future__ import annotations


def highs_lows(c: list[dict]) -> list[dict]:
    """Every old high and old low, with when (if ever) it was eaten: a later candle traded beyond it.
    ``{"side": "high" | "low", "price", "t", "eaten_at": time | None}``. The last candle cannot be a turn yet."""
    out = []
    for i in range(1, len(c) - 1):
        for side, key, sgn in (("high", "high", 1), ("low", "low", -1)):
            p = c[i][key]
            if sgn * p > sgn * c[i - 1][key] and sgn * p > sgn * c[i + 1][key]:
                hit = next((x["time"] for x in c[i + 1:] if sgn * x[key] > sgn * p), None)
                out.append({"side": side, "price": p, "t": c[i]["time"], "eaten_at": hit})
    return out


def resting(c: list[dict]) -> dict:
    """What is left uneaten: ``{"buyside": [highs above price, nearest first], "sellside": [lows below, nearest first]}``.
    A high that was eaten is never returned, however near or far it is."""
    left = [x for x in highs_lows(c) if x["eaten_at"] is None]
    return {"buyside": sorted((x for x in left if x["side"] == "high"), key=lambda x: x["price"]),
            "sellside": sorted((x for x in left if x["side"] == "low"), key=lambda x: -x["price"])}


def eaten_since(c: list[dict], since: float) -> list[dict]:
    """Highs and lows eaten at or after ``since`` (a time), newest first: what the present move has taken."""
    return sorted((x for x in highs_lows(c) if x["eaten_at"] is not None and x["eaten_at"] >= since), key=lambda x: -x["eaten_at"])


def equal(levels: list[dict], near: float) -> list[dict]:
    """Groups of two or more highs (or lows) that sit very close by: a straight line through one nearly touches the
    others. ``near`` is how close that is, in price; the caller decides it. Returns
    ``{"side", "top", "bottom", "count", "t0", "t1", "members"}``, each level in at most one group."""
    out = []
    for side in ("high", "low"):
        xs = sorted((x for x in levels if x["side"] == side), key=lambda x: x["price"])
        group: list[dict] = []
        for x in xs + [None]:
            if x is not None and (not group or x["price"] - group[-1]["price"] <= near):
                group.append(x)
                continue
            if len(group) >= 2:
                out.append({"side": side, "bottom": group[0]["price"], "top": group[-1]["price"], "count": len(group),
                            "t0": min(g["t"] for g in group), "t1": max(g["t"] for g in group), "members": group})
            group = [x] if x is not None else []
    return out


def previous_period(periods: list[dict], since: list[dict]) -> dict:
    """The previous day's (or week's) high and low, and whether each was left uneaten. ``periods`` are completed
    daily (or weekly) candles; ``since`` are the candles traded after the last of them (any timeframe).
    ``{"high": {"price", "t", "eaten_at"}, "low": {...}}``."""
    p = periods[-1]
    hi = next((x["time"] for x in since if x["high"] > p["high"]), None)
    lo = next((x["time"] for x in since if x["low"] < p["low"]), None)
    return {"high": {"price": p["high"], "t": p["time"], "eaten_at": hi}, "low": {"price": p["low"], "t": p["time"], "eaten_at": lo}}
