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
    # the nearest zone on the bias's own side that price would retrace into (a BISI under price when bull, a SIBI over
    # it when bear) and that still stands: his "interesting area" the higher timeframe looks to trade from
    mine = [g for g in fvgs(seen) if g["closed_through_at"] is None and g["type"] == ("BISI" if b["side"] == "bull" else "SIBI")]
    area = (max((g for g in mine if g["top"] < bottom), key=lambda g: g["top"], default=None) if b["side"] == "bull"
            else min((g for g in mine if g["bottom"] > top), key=lambda g: g["bottom"], default=None))
    return {"side": b["side"], "price": price, "near": near, "behind": b["change"]["price"], "area": area and (area["bottom"], area["top"], area["type"]),
            "ahead": b["ahead"]["price"] if b["ahead"] else None, "buyside": above and above["price"],
            "sellside": below and below["price"], "imbalance_above": up and (up["bottom"], up["top"], up["type"]),
            "imbalance_below": down and (down["bottom"], down["top"], down["type"]),
            "inside": inside and (inside["bottom"], inside["top"], inside["type"]),
            # when each of those was made (the candle's time), so a mark can start at the candle it belongs to
            "when": {"behind": b["change"]["t"], "ahead": b["ahead"]["t"] if b["ahead"] else None, "buyside": above and above["t"],
                     "sellside": below and below["t"], "imbalance_above": up and up["t"], "imbalance_below": down and down["t"],
                     "inside": inside and inside["t"], "area": area and area["t"]}}


def merged(r: dict, above: dict | list | None) -> dict | None:
    """One call from the whole ladder read together: this timeframe (``r``) and every timeframe above it (``above``:
    their reads, highest first; a timeframe with no read is ``None``; one read alone is taken as the one above).

    His (20 Nov 2026): the biases disagreeing is normal; the lower timeframe's momentum against the higher bias "must
    be looked at"; "where price is RIGHT NOW is always more important, because it's drawn to something". His (23 Nov
    2026): a retracement is "what kills bias for a bit": the higher timeframes are bullish, the lower ones sell
    "into an interesting zone" the higher ones look to buy from. "Always trade with what's current: if we are just
    above the interesting area, sell into it; if we are inside the area, watch what happens to build confidence for a
    buy or sell." The nearest thing "is normally when you're just looking for what's the closest relative to where
    price is already going". Selling into the area needs "something… play in our current area supporting lower
    prices; if we don't see that we don't sell into it".

    Mine, not his, so that it can be tested at all (an "area" is a standing imbalance on its timeframe's own side:
    no candle of that timeframe has closed beyond it):
      * ``watch``: price is inside the area of a timeframe above and this timeframe's bias is against that
        timeframe's: nothing is called (``target`` is ``None``). With several, the highest timeframe's;
      * ``from area``: price is inside such an area and this timeframe's bias is that timeframe's: something has
        played out for it. The way looked is theirs; the target is the nearest thing that way on any timeframe;
      * ``into area``: this timeframe's bias is against a timeframe above, and that timeframe's area lies ahead in
        this timeframe's direction: the way looked is this timeframe's, and the target is the near edge of that area
        (the nearest such area). "Something supporting" it is taken to be this timeframe's own bias, which only
        exists once it has broken structure that way;
      * ``agree``: otherwise, every timeframe above has this one's bias; ``momentum``: otherwise. The way looked is
        this timeframe's and the target the nearest thing that way on any timeframe: resting liquidity or the near
        edge of an unfilled imbalance;
      * the older, exact count is undone by the nearest resting liquidity the other way (any timeframe) being eaten,
        or a body close beyond this timeframe's level behind. His own way of judging is ``played_out``.
    ``whose`` is "own" or "above", ``whose_i`` the place in ``above`` of the timeframe the target belongs to,
    ``area_i`` the place of the timeframe whose area it is. ``None`` when nothing was read above, or nothing lies
    that way."""
    ups = [above] if isinstance(above, dict) else list(above or [])
    if not any(ups):
        return None
    price, side, bull = r["price"], r["side"], r["side"] == "bull"
    on_side = lambda x, z: z is not None and z[2] == ("BISI" if x["side"] == "bull" else "SIBI")       # noqa: E731
    area_i = next((i for i, x in enumerate(ups) if x and on_side(x, x.get("inside"))), None)
    found, how = [], None
    if area_i is not None:
        if ups[area_i]["side"] != side:
            return {"kind": "merged", "merge": "watch", "side": None, "target": None, "area_i": area_i}
        how = "from area"
    else:
        ahead = [(i, x["area"]) for i, x in enumerate(ups) if x and x["side"] != side and on_side(x, x.get("area"))]
        ahead = [(i, z) for i, z in ahead if ((z[0] if bull else z[1]) > price) == bull]                # it lies the way this timeframe looks
        if ahead:
            area_i, z = min(ahead, key=lambda a: abs((a[1][0] if bull else a[1][1]) - price))
            how = "into area"
            found = [{"target": (z[0] if bull else z[1], "trade"), "what": z[2], "whose": "above", "whose_i": area_i, "gap": z}]
    if how is None:
        how = "agree" if all(x["side"] == side for x in ups if x) else "momentum"
    if not found:
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
    other = [x["sellside"] if bull else x["buyside"] for x in [r] + [x for x in ups if x]]
    other = [p for p in other if p is not None and (p < price) == bull]
    undo = ([(min(other, key=lambda p: abs(p - price)), "eat")] if other else []) + [(r["behind"], "close")]
    d_t, d_u = abs(best["target"][0] - price), min(abs(u[0] - price) for u in undo)
    return {"kind": "merged", "side": side, "price": price, "near": r["near"], "target": best["target"], "undo": undo,
            "dist_target": d_t, "dist_undo": d_u, "nearer": "target" if d_t < d_u else "undo" if d_u < d_t else "level",
            "merge": how, "what": best["what"], "whose": best["whose"], "whose_i": best["whose_i"], "area_i": area_i,
            "gap": best["gap"], "bias_behind": r["behind"]}


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


def story(side: str, goal: float, behind: float, zones: list[tuple], fine: list[dict], start: int, closes: list[tuple], first: int,
          zone_closes: dict) -> dict:
    """What happened to a bias, told in order instead of being marked hit or miss. His (23 Nov 2026): "it's not really
    hit or miss… You will never KNOW, you can only let it play out"; "this is bias focused": we look at price breaking
    a level; "we reach an interesting zone to buy from"; "if that interesting zone fails, there could be a possibility
    for other plays, but FOCUS and look at the context: is there a break and close candle below, what else is
    interesting below"; "if it flips over you could have read the bias wrong for a second"; "even if x breaks below,
    there's another area price could buy from".

    ``goal``: the level the bias looks to break (a body close beyond it). ``behind``: the level whose break by a body
    close is the bias flipping. ``zones``: ``(timeframe, bottom, top)`` for each interesting zone on the bias's side,
    in any order. ``closes`` from ``first``: this timeframe's ``(time closed, close)`` after the moment.
    ``zone_closes``: ``{timeframe: (its closes, first index)}``; a zone fails only on a close of its OWN timeframe.

    Returns ``story``: "straight" (the level broke and no zone failed), "deeper" (the level broke after at least one
    zone had failed), "flipped, areas left" (the bias flipped while a zone still stood), "flipped" or "open"; with
    ``events`` in order ``(time, what, timeframe)``, how many zones were ``reached`` and ``failed``, and ``story_at``.
    The four names and counting it this way are mine."""
    bull, k = side == "bull", first
    step = fine[start + 1]["time"] - fine[start]["time"] if len(fine) > start + 1 else 0
    zs = [{"tf": tf, "lo": lo, "hi": hi, "reached": False, "failed": False} for tf, lo, hi in zones]
    zk = {tf: i for tf, (_, i) in zone_closes.items()}
    events: list = []

    def done(name, at):
        return {"story": name, "events": events, "reached": sum(z["reached"] for z in zs), "failed": sum(z["failed"] for z in zs),
                "zones": len(zs), "story_at": at}

    for n in range(start, len(fine)):
        x = fine[n]
        end = x["time"] + step
        for z in zs:
            if not z["reached"] and not z["failed"] and (x["low"] <= z["hi"] if bull else x["high"] >= z["lo"]):
                z["reached"] = True
                events.append((x["time"], "reached", z["tf"]))
        for tf, (cl, _) in zone_closes.items():
            while zk[tf] < len(cl) and cl[zk[tf]][0] <= end:
                c = cl[zk[tf]][1]
                for z in zs:
                    if z["tf"] == tf and not z["failed"] and (c < z["lo"] if bull else c > z["hi"]):
                        z["failed"] = True
                        events.append((x["time"], "closed through", tf))
                zk[tf] += 1
        won = lost = False
        while k < len(closes) and closes[k][0] <= end:
            c = closes[k][1]
            won, lost = won or (c > goal if bull else c < goal), lost or (c < behind if bull else c > behind)
            k += 1
        if lost:
            events.append((x["time"], "bias flipped", None))
            return done("flipped, areas left" if any(not z["failed"] for z in zs) else "flipped", x["time"])
        if won:
            events.append((x["time"], "level broken", None))
            return done("deeper" if any(z["failed"] for z in zs) else "straight", x["time"])
    return done("open", None)
