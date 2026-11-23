"""The tools backtest: calls made by the concept tools at a past moment, and what happened to each afterwards.
Design: v2/specs/2026-11-20-higher-timeframe-backtest.md (approved by Sharif, 20 Nov 2026).

He: "we are looking for price to possibly draw into this area, or this section; did that happen or not. DON'T look at
the exact entries and details in depth." So a call is one sentence about a draw that can turn out true or false. There
are no entries, stops or targets here, and nothing in this file changes a tool: it only calls them.

Three kinds of call, all for the timeframe being read:
  * ``liquidity``: with the bias, price might draw to the resting liquidity on the bias's side;
  * ``bias``: the bias holds: the level ahead is closed through before the level behind;
  * ``imbalance``: price might reach the nearest unfilled imbalance in the bias's direction.

A fourth kind, added 20 Nov 2026 after he went through the first run: ``merged`` (see ``merged`` below). He: "you're
still looking at the chart itself from daily and that's one perspective, or monthly and that's one perspective… there's
a mix of timeframes to provide a result." The first three are kept as they were, so the two ways can be compared.

Everything that decides a call is the tools' own reading (bias, liquidity, alt-liquidity). What is mine, not his:
which three calls are made, what undoes each, how long a call is given before it is left unresolved, how much of
the chart is taken as "the picture being looked at" when his eye's measure for "very close" is applied, using the bias
as "the way price is moving" for an imbalance, and reading candles (not the line chart).

Candles are dicts with ``time``, ``open``, ``high``, ``low``, ``close``, oldest first. No timeframe, instrument,
price or date is named in here: the runner passes the candles in.
"""
from __future__ import annotations

from alt_liquidity import fvgs, volume_imbalances
from bias import bias_levels
from liquidity import near_from_view, resting


def read(c: list[dict], parent: list[dict] | None = None, grand: list[dict] | None = None, forming: list[dict] | None = None,
         view: int = 120) -> dict | None:
    """What the tools see on one timeframe at a moment: the bias and its levels, the nearest resting liquidity each
    side of price, the nearest unfilled imbalance each side. ``None`` when there is no bias yet.

    ``c``, ``parent``, ``grand``: candles that had all closed by the moment. ``forming``: lowest-timeframe candles
    from the close of the last candle in ``c`` up to the moment, i.e. what the candle still forming has done so far.
    They are not read as a candle of this timeframe (a forming candle never is), but "relative to now" needs them:
    price now is their last close, and a level they have already taken is not resting any more.
    ``view`` is how many of the latest candles are taken as the picture being looked at (mine)."""
    if len(c) < 3:
        return None
    b = bias_levels(c, parent, grand)
    if b["side"] not in ("bull", "bear") or not b["change"]:
        return None
    seen, forming = c[-view:], forming or []
    price = forming[-1]["close"] if forming else c[-1]["close"]
    top = max([x["high"] for x in forming] + [price])
    bottom = min([x["low"] for x in forming] + [price])
    near = near_from_view(seen)
    rest = resting(seen, near)
    above = next((x for x in rest["buyside"] if x["price"] > price and top - x["price"] <= near), None)
    below = next((x for x in rest["sellside"] if x["price"] < price and x["price"] - bottom <= near), None)
    gaps = [g for g in fvgs(seen) + volume_imbalances(seen) if g["state"] != "filled"]
    up = min((g for g in gaps if g["bottom"] > top), key=lambda g: g["bottom"], default=None)
    down = max((g for g in gaps if g["top"] < bottom), key=lambda g: g["top"], default=None)
    # the zone price is in that still stands: no candle of THIS timeframe has closed beyond it (his, 23 Nov 2026: "a
    # close through that imbalance, relative to the timeframe of the break and the imbalance itself"; wicks are no break)
    inside = next((g for g in reversed(fvgs(seen)) if g["closed_through_at"] is None and g["bottom"] <= price <= g["top"]), None)
    return {"side": b["side"], "price": price, "near": near, "behind": b["change"]["price"],
            "ahead": b["ahead"]["price"] if b["ahead"] else None, "buyside": above and above["price"],
            "sellside": below and below["price"], "imbalance_above": up and (up["bottom"], up["top"], up["type"]),
            "imbalance_below": down and (down["bottom"], down["top"], down["type"]),
            "inside": inside and (inside["bottom"], inside["top"], inside["type"]),
            # when each of those was made (the candle's time), so a mark can start at the candle it belongs to
            "when": {"behind": b["change"]["t"], "ahead": b["ahead"]["t"] if b["ahead"] else None, "buyside": above and above["t"],
                     "sellside": below and below["t"], "imbalance_above": up and up["t"], "imbalance_below": down and down["t"],
                     "inside": inside and inside["t"]}}


def merged(r: dict, above: dict | list | None) -> dict | None:
    """One call from the whole ladder read together: this timeframe (``r``) and every timeframe above it (``above``:
    their reads, highest first; a timeframe with no read is ``None``; one read alone is taken as the one above).

    His (20 Nov 2026): the biases disagreeing is normal; the lower timeframe's momentum against the higher bias "must
    be looked at"; "where price is RIGHT NOW is always more important, because it's drawn to something"; not a far
    level but what is nearby; and when price has "retraced into a key area", "the current goal might be to reach a
    nearby imbalance". His (23 Nov 2026): at an interesting zone "we expect price to not break the interesting zone
    below with a closed candle, nor break below within that same timeframe of the interesting zone"; "a close through
    that imbalance, relative to the timeframe of the break and the imbalance itself". And always top to bottom.

    Mine, not his (he: "it's tricky to say it specifically"), so that it can be tested at all:
      * ``key area``: price is inside a standing imbalance (``read``'s ``inside``: no candle of its own timeframe has
        closed beyond it) of a timeframe above, on that timeframe's side (a BISI when it is bull, a SIBI when bear),
        and this timeframe's bias is the other way: the way looked is that higher timeframe's. With several, the
        highest timeframe's;
      * ``agree``: otherwise, every timeframe above has this one's bias: that is the way looked;
      * ``momentum``: otherwise: the way looked is this timeframe's (the momentum now);
      * the target is whatever is NEAREST from price now in that way, on any of the timeframes: resting liquidity or
        the near edge of an unfilled imbalance;
      * undone by: the nearest resting liquidity the other way (any of the timeframes) being eaten, or a body close
        beyond this timeframe's level behind; for ``key area``, only a body close of the AREA'S OWN timeframe beyond
        the area (``"close area"``).
    ``whose`` is "own" or "above", ``whose_i`` the place in ``above`` of the timeframe the target belongs to,
    ``area_i`` the place of the timeframe whose area it is. ``None`` when nothing was read above, or nothing lies
    that way."""
    ups = [above] if isinstance(above, dict) else list(above or [])
    if not any(ups):
        return None
    price, area_i = r["price"], None
    for i, x in enumerate(ups):
        hold = x and x.get("inside")
        if hold and x["side"] != r["side"] and hold[2] == ("BISI" if x["side"] == "bull" else "SIBI"):
            area_i = i
            break
    if area_i is not None:
        side, how, hold = ups[area_i]["side"], "key area", ups[area_i]["inside"]
    elif all(x["side"] == r["side"] for x in ups if x):
        side, how = r["side"], "agree"
    else:
        side, how = r["side"], "momentum"
    bull = side == "bull"
    found = []
    for i, x in [(None, r)] + [(i, x) for i, x in enumerate(ups) if x]:
        who = "own" if i is None else "above"
        liq, gap = (x["buyside"], x["imbalance_above"]) if bull else (x["sellside"], x["imbalance_below"])
        if liq is not None:
            found.append({"target": (liq, "eat"), "what": "buyside" if bull else "sellside", "whose": who, "whose_i": i, "gap": None})
        if gap is not None:
            found.append({"target": (gap[0] if bull else gap[1], "trade"), "what": gap[2], "whose": who, "whose_i": i, "gap": gap})
    found = [f for f in found if (f["target"][0] > price) == bull and f["target"][0] != price]
    if not found:
        return None
    best = min(found, key=lambda f: abs(f["target"][0] - price))
    if how == "key area":
        undo = [(hold[0] if bull else hold[1], "close area")]
    else:
        other = [x["sellside"] if bull else x["buyside"] for x in [r] + [x for x in ups if x]]
        other = [p for p in other if p is not None and (p < price) == bull]
        undo = ([(min(other, key=lambda p: abs(p - price)), "eat")] if other else []) + [(r["behind"], "close")]
    d_t, d_u = abs(best["target"][0] - price), min(abs(u[0] - price) for u in undo)
    return {"kind": "merged", "side": side, "price": price, "near": r["near"], "target": best["target"], "undo": undo,
            "dist_target": d_t, "dist_undo": d_u, "nearer": "target" if d_t < d_u else "undo" if d_u < d_t else "level",
            "merge": how, "what": best["what"], "whose": best["whose"], "whose_i": best["whose_i"], "area_i": area_i,
            "gap": best["gap"], "bias_behind": ups[area_i]["behind"] if area_i is not None else r["behind"]}


def calls(r: dict) -> list[dict]:
    """The calls a read makes. Each: ``kind``, ``side`` (the bias), ``target`` (a price and how it is reached),
    ``undo`` (what would undo the read first), and how far each is from price, so a result can be split by which was
    nearer. "trade" = price trades to it (clearly past it, for liquidity); "close" = a candle body closes beyond it."""
    bull, price, out = r["side"] == "bull", r["price"], []

    def add(kind, target, undo, **extra):
        undo = [u for u in undo if u[0] is not None]
        d_t, d_u = abs(target[0] - price), min((abs(u[0] - price) for u in undo), default=None)
        out.append({"kind": kind, "side": r["side"], "price": price, "near": r["near"], "target": target, "undo": undo,
                    "dist_target": d_t, "dist_undo": d_u,
                    "nearer": None if d_u is None else "target" if d_t < d_u else "undo" if d_u < d_t else "level", **extra})

    with_bias, other = (r["buyside"], r["sellside"]) if bull else (r["sellside"], r["buyside"])
    behind = (r["behind"], "close")
    if with_bias is not None:
        add("liquidity", (with_bias, "eat"), [(other, "eat"), behind])
    if r["ahead"] is not None and (r["ahead"] > price) == bull:
        add("bias", (r["ahead"], "close"), [behind])
    gap = r["imbalance_above"] if bull else r["imbalance_below"]
    if gap is not None:
        add("imbalance", (gap[0] if bull else gap[1], "trade"), [behind], imbalance=gap[2])
    return out


def _hit(level: tuple, up: bool, candle: dict | None, close: float | None, near: float, area: float | None = None) -> bool:
    """Has this level been reached? ``up``: it lies above price. "eat" = traded clearly past it (his "clearly past");
    "trade" = traded to it; "close" = a body closed beyond it (only when a candle of the call's timeframe closed);
    "close area" = a body of the AREA'S timeframe closed beyond it (``area``: that close, when one has just closed)."""
    price, how = level
    if how == "close area":
        return area is not None and (area > price if up else area < price)
    if how == "close":
        return close is not None and (close > price if up else close < price)
    if candle is None:
        return False
    reach = candle["high"] - price if up else price - candle["low"]
    return reach > near if how == "eat" else reach >= 0


def resolve(call: dict, fine: list[dict], closes: list[tuple], horizon: int = 20, area_closes: list[tuple] | None = None) -> dict:
    """What happened to a call. ``fine``: the lowest-timeframe candles from the moment of the call on (they show what
    price traded to, and in what order). ``closes``: ``(time the candle closed, its close)`` for candles of the call's
    own timeframe that closed after the moment; a body close is judged on these only. ``area_closes``: the same for
    the timeframe of a key area, which is what a "close area" is judged on. The call is given ``horizon`` of its own
    candles (mine); after that it is ``unresolved``, and if the data ends first it is ``open``.

    Outcomes: ``true``, ``undone``, ``same candle`` (both reached inside one lowest-timeframe candle, so the order is
    not known), ``unresolved``, ``open``. Also ``at`` (when) and ``candles`` (how many of its own candles it took)."""
    bull = call["side"] == "bull"
    limit = closes[horizon - 1][0] if len(closes) >= horizon else None
    area_closes = area_closes or []
    k = ka = 0
    for x in fine:
        if limit is not None and x["time"] >= limit:
            return {"outcome": "unresolved", "at": limit, "candles": horizon}
        won = _hit(call["target"], bull, x, None, call["near"])
        lost = any(_hit(u, not bull, x, None, call["near"]) for u in call["undo"])
        end = x["time"] + (fine[1]["time"] - fine[0]["time"] if len(fine) > 1 else 0)
        while not (won or lost) and k < len(closes) and closes[k][0] <= end:        # own-timeframe closes up to here
            won = _hit(call["target"], bull, None, closes[k][1], call["near"])
            lost = any(_hit(u, not bull, None, closes[k][1], call["near"]) for u in call["undo"])
            k += 1
        while k < len(closes) and closes[k][0] <= end:
            k += 1
        while ka < len(area_closes) and area_closes[ka][0] <= end:                  # the area's own timeframe closing
            lost = lost or any(_hit(u, not bull, None, None, call["near"], area_closes[ka][1]) for u in call["undo"])
            ka += 1
        if won or lost:
            return {"outcome": "same candle" if won and lost else "true" if won else "undone", "at": x["time"], "candles": k}
    return {"outcome": "open", "at": None, "candles": k}


def played_out(side: str, target: tuple, behind: float, near: float, fine: list[dict], start: int, closes: list[tuple], first: int) -> dict:
    """Did the bias play out? His way of judging a call (23 Nov 2026): he looks at the statement, bull or bear, and
    follows it forward. The area named being reached is the bias playing out, by whatever route: "what if price broke
    your level with a closed candle and went for a lower VI or a lower BISI, or it created EQLs, and then hit our
    area. Our bias still played out… it's not always a perfect find." What ends the idea: "bias changing would end
    the idea", i.e. a body close beyond the level behind, on the timeframe whose bias was stated (lesson 01).

    ``fine`` from ``start``: the lowest-timeframe candles from the moment on. ``closes`` from ``first``: ``(time the
    candle closed, its close)`` for the candles of the stated bias's timeframe that closed after the moment. There is
    no number of candles: the call is followed until one of the two happens or the data ends.
    ``{"played": "true" | "ended" | "same candle" | "open", "played_at": time | None}``.
    He also said "price goes so off" ends it; what that is has not been taught and is not guessed here."""
    bull, k = side == "bull", first
    step = fine[start + 1]["time"] - fine[start]["time"] if len(fine) > start + 1 else 0
    for n in range(start, len(fine)):
        x = fine[n]
        won, lost, end = _hit(target, bull, x, None, near), False, x["time"] + step
        while k < len(closes) and closes[k][0] <= end:
            lost = lost or (closes[k][1] < behind if bull else closes[k][1] > behind)
            k += 1
        if won or lost:
            return {"played": "same candle" if won and lost else "true" if won else "ended", "played_at": x["time"]}
    return {"played": "open", "played_at": None}
