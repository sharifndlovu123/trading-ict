"""Alt-liquidity: imbalances price is drawn to, as Sharif defined each one on 17 Nov 2026 (alt-liquidity.md beside
this file). Tools only: candles in, a description out. The family name is imbalance; original liquidity comes first.

Candles are dicts with ``time`` (epoch seconds), ``open``, ``high``, ``low``, ``close``, oldest first.

Choices that are mine, not his, named so they can be changed:
  * "filled" = price has since traded across the whole gap; "partly" = into it but not across;
  * "traded through" for an IFVG = a later candle CLOSED beyond the gap's far edge;
  * when a feed has no 4:59 p.m. print, the close of an opening gap is the last print before 5 p.m.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def _state(lo: float, hi: float, after: list[dict], from_above: bool) -> dict:
    """How far price has come back into a gap since it formed. ``from_above``: price returns down into it (a BISI)."""
    if not after:
        return {"state": "untouched", "filled_at": None, "closed_through_at": None}
    if from_above:
        reach = min(x["low"] for x in after)
        filled = next((x["time"] for x in after if x["low"] <= lo), None)
        through = next((x["time"] for x in after if x["close"] < lo), None)
        state = "untouched" if reach >= hi else "filled" if reach <= lo else "partly"
    else:
        reach = max(x["high"] for x in after)
        filled = next((x["time"] for x in after if x["high"] >= hi), None)
        through = next((x["time"] for x in after if x["close"] > hi), None)
        state = "untouched" if reach <= lo else "filled" if reach >= hi else "partly"
    return {"state": state, "filled_at": filled, "closed_through_at": through}


def fvgs(c: list[dict]) -> list[dict]:
    """Fair value gaps: "a three-candle price imbalance: the middle candle moves so sharply that there's a gap between
    the first candle's range and the third candle's range."
    BISI = formed by an up-close candle (upward delivery); SIBI = formed by a down-close candle (downward delivery).
    ``{"type": "BISI" | "SIBI", "bottom", "top", "t", "state", "filled_at", "closed_through_at", "ifvg": None | "resistance" | "support"}``.
    ``ifvg``: the gap was traded through, so it may later act the other way (a BISI traded down through = resistance)."""
    out = []
    for i in range(2, len(c)):
        a, b, e = c[i - 2], c[i - 1], c[i]
        if e["low"] > a["high"] and b["close"] > b["open"]:
            kind, lo, hi = "BISI", a["high"], e["low"]
        elif e["high"] < a["low"] and b["close"] < b["open"]:
            kind, lo, hi = "SIBI", e["high"], a["low"]
        else:
            continue
        s = _state(lo, hi, c[i + 1:], from_above=kind == "BISI")
        inv = None if s["closed_through_at"] is None else ("resistance" if kind == "BISI" else "support")
        out.append({"type": kind, "bottom": lo, "top": hi, "t": b["time"], **s, "ifvg": inv})
    return out


def volume_imbalances(c: list[dict]) -> list[dict]:
    """Volume imbalance: "absence of body volume". Two candles side by side whose bodies do not touch while their
    wicks overlap (if the wicks do not overlap either, it is a full gap, not a volume imbalance).
    ``{"type": "VI", "direction": "up" | "down", "bottom", "top", "t", "state", ...}``."""
    out = []
    for i in range(1, len(c)):
        a, b = c[i - 1], c[i]
        a_top, a_bot = max(a["open"], a["close"]), min(a["open"], a["close"])
        b_top, b_bot = max(b["open"], b["close"]), min(b["open"], b["close"])
        if b_bot > a_top and b["low"] <= a["high"]:
            lo, hi, direction = a_top, b_bot, "up"
        elif b_top < a_bot and b["high"] >= a["low"]:
            lo, hi, direction = b_top, a_bot, "down"
        else:
            continue
        out.append({"type": "VI", "direction": direction, "bottom": lo, "top": hi, "t": b["time"],
                    **_state(lo, hi, c[i + 1:], from_above=direction == "up")})
    return out


def is_draw(gap: dict, price: float, moving: str) -> bool:
    """"Both count as a draw when unfilled, but when price is already moving in their direction." ``moving`` is
    "up" or "down": which way price is travelling now (decided by whoever reads the chart, not here)."""
    if gap.get("state") == "filled":
        return False
    return (gap["bottom"] > price and moving == "up") or (gap["top"] < price and moving == "down")


def opening_gaps(m: list[dict], tz: str = "America/New_York") -> list[dict]:
    """NDOG and NWOG from the lowest timeframe available (he: "use the lowest timeframe available when marking them, so 1m").
    NDOG: "prior session's 5 p.m. close to the 6 p.m. futures reopen". NWOG: "Friday's close at 4:59 p.m. to Sunday's
    6 p.m. open". A gap is found wherever trading stops before 5 p.m. and starts again at or after 6 p.m.: over a
    weekend it is the NWOG, otherwise the NDOG.
    ``{"type": "NDOG" | "NWOG", "bottom", "top", "close", "open", "direction", "t_close", "t_open", "size", "state", ...}``.
    ``tz`` is the clock the candle times are read in (New York by default)."""
    z, out = ZoneInfo(tz), []
    when = [datetime.fromtimestamp(x["time"], z) for x in m]
    for i in range(1, len(m)):
        a, b = when[i - 1], when[i]
        if not (a.hour < 17 and b.hour >= 18 and (b - a).total_seconds() >= 3600 and b.date() >= a.date()):
            continue
        cl, op = m[i - 1]["close"], m[i]["open"]
        if cl == op:
            continue
        lo, hi = min(cl, op), max(cl, op)
        out.append({"type": "NWOG" if (b.date() - a.date()).days >= 1 else "NDOG", "bottom": lo, "top": hi, "close": cl, "open": op,
                    "direction": "up" if op > cl else "down", "t_close": m[i - 1]["time"], "t_open": m[i]["time"], "size": hi - lo,
                    **_state(lo, hi, m[i:], from_above=op > cl)})
    return out


def _trading_day(t: float, z: ZoneInfo) -> int:
    """The trading day a moment belongs to, as a day number: a trading day runs from 6 p.m. to 5 p.m. the next day,
    so Sunday evening already belongs to Monday."""
    d = datetime.fromtimestamp(t, z)
    return d.toordinal() + (1 if d.hour >= 18 else 0)


def _trading_week(t: float, z: ZoneInfo) -> int:
    day = _trading_day(t, z)
    return day - datetime.fromordinal(day).weekday()          # the Monday of that trading week


def in_use(gap: dict, now: float, tz: str = "America/New_York") -> bool:
    """How long an opening gap is used. NDOG: "current week only"; "once it's filled it can still be useful through
    the day but not for the week". NWOG: the week ("within that week it can be a useful area")."""
    z = ZoneInfo(tz)
    if now < gap["t_open"] or _trading_week(gap["t_open"], z) != _trading_week(now, z):
        return False
    if gap["type"] == "NDOG" and gap.get("filled_at") is not None:
        return _trading_day(gap["filled_at"], z) == _trading_day(now, z)
    return True
