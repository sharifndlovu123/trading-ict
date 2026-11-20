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
    inside = next((g for g in reversed(gaps) if g["type"] in ("BISI", "SIBI") and g["bottom"] <= price <= g["top"]), None)
    return {"side": b["side"], "price": price, "near": near, "behind": b["change"]["price"],
            "ahead": b["ahead"]["price"] if b["ahead"] else None, "buyside": above and above["price"],
            "sellside": below and below["price"], "imbalance_above": up and (up["bottom"], up["top"], up["type"]),
            "imbalance_below": down and (down["bottom"], down["top"], down["type"]),
            "inside": inside and (inside["bottom"], inside["top"], inside["type"])}


def merged(r: dict, above: dict | None) -> dict | None:
    """One call from two timeframes read together: this one (``r``) and the one above it (``above``).

    His (20 Nov 2026): the biases disagreeing is normal; the lower timeframe's momentum against the higher bias "must
    be looked at"; "where price is RIGHT NOW is always more important, because it's drawn to something"; not a far
    level but what is nearby; and when price has "retraced into a key area", "the current goal might be to reach a
    nearby imbalance". From the lesson before it: a closed candle beyond the higher timeframe's area, against it,
    favours the lower timeframe's side.

    Mine, not his (he: "it's tricky to say it specifically"), so that it can be tested at all:
      * ``agree``: both have the same bias: that is the way looked;
      * ``momentum``: they disagree: the way looked is this timeframe's (the momentum now);
      * ``key area``: they disagree and price is inside an unfilled FVG of the timeframe above that is on its bias's
        side (a BISI when it is bull, a SIBI when bear): the way looked is the timeframe above's;
      * the target is whatever is NEAREST from price now in that way, on either timeframe: resting liquidity or the
        near edge of an unfilled imbalance;
      * undone by: the nearest resting liquidity the other way (either timeframe) being eaten, or a body close beyond
        this timeframe's level behind; for ``key area``, only a body close of this timeframe beyond the area.
    ``None`` when there is no timeframe above, or nothing lies in that way."""
    if above is None:
        return None
    price, hold = r["price"], above.get("inside")
    if r["side"] == above["side"]:
        side, how = r["side"], "agree"
    elif hold and hold[2] == ("BISI" if above["side"] == "bull" else "SIBI"):
        side, how = above["side"], "key area"
    else:
        side, how = r["side"], "momentum"
    bull = side == "bull"
    found = []
    for who, x in (("own", r), ("above", above)):
        liq, gap = (x["buyside"], x["imbalance_above"]) if bull else (x["sellside"], x["imbalance_below"])
        if liq is not None:
            found.append({"target": (liq, "eat"), "what": "buyside" if bull else "sellside", "whose": who, "gap": None})
        if gap is not None:
            found.append({"target": (gap[0] if bull else gap[1], "trade"), "what": gap[2], "whose": who, "gap": gap})
    found = [f for f in found if (f["target"][0] > price) == bull and f["target"][0] != price]
    if not found:
        return None
    best = min(found, key=lambda f: abs(f["target"][0] - price))
    if how == "key area":
        undo = [(hold[0] if bull else hold[1], "close")]
    else:
        other = [x["sellside"] if bull else x["buyside"] for x in (r, above)]
        other = [p for p in other if p is not None and (p < price) == bull]
        undo = ([(min(other, key=lambda p: abs(p - price)), "eat")] if other else []) + [(r["behind"], "close")]
    d_t, d_u = abs(best["target"][0] - price), min(abs(u[0] - price) for u in undo)
    return {"kind": "merged", "side": side, "price": price, "near": r["near"], "target": best["target"], "undo": undo,
            "dist_target": d_t, "dist_undo": d_u, "nearer": "target" if d_t < d_u else "undo" if d_u < d_t else "level",
            "merge": how, "what": best["what"], "whose": best["whose"], "gap": best["gap"]}


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


def _hit(level: tuple, up: bool, candle: dict | None, close: float | None, near: float) -> bool:
    """Has this level been reached? ``up``: it lies above price. "eat" = traded clearly past it (his "clearly past");
    "trade" = traded to it; "close" = a body closed beyond it (only when a candle of the call's timeframe closed)."""
    price, how = level
    if how == "close":
        return close is not None and (close > price if up else close < price)
    if candle is None:
        return False
    reach = candle["high"] - price if up else price - candle["low"]
    return reach > near if how == "eat" else reach >= 0


def resolve(call: dict, fine: list[dict], closes: list[tuple], horizon: int = 20) -> dict:
    """What happened to a call. ``fine``: the lowest-timeframe candles from the moment of the call on (they show what
    price traded to, and in what order). ``closes``: ``(time the candle closed, its close)`` for candles of the call's
    own timeframe that closed after the moment; a body close is judged on these only. The call is given ``horizon``
    of its own candles (mine); after that it is ``unresolved``, and if the data ends first it is ``open``.

    Outcomes: ``true``, ``undone``, ``same candle`` (both reached inside one lowest-timeframe candle, so the order is
    not known), ``unresolved``, ``open``. Also ``at`` (when) and ``candles`` (how many of its own candles it took)."""
    bull = call["side"] == "bull"
    limit = closes[horizon - 1][0] if len(closes) >= horizon else None
    k = 0
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
        if won or lost:
            return {"outcome": "same candle" if won and lost else "true" if won else "undone", "at": x["time"], "candles": k}
    return {"outcome": "open", "at": None, "candles": k}
