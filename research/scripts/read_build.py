"""Engine-read review set (local only): at a moment, what the engine SEES — structure per timeframe (W / D / 4H / 1H,
the weekly-structure rule on each), the areas it watches, where liquidity sits, and where it thinks the play is (on
smaller TFs, respecting a higher-TF area, or reaching for lower liquidity). No entries. Sharif comments per statement.

    uv run python research/scripts/read_build.py [--n 12] [--seed 5]
    uv run python research/scripts/liqmap_server.py --port 8772 --data out/read --page viewer/read.html \
        --answers reports/reviews/read.jsonl          → http://127.0.0.1:8772

Moments: weekday 08:30 NY, 2022-03-01 → 2023-09-28 (in-sample), US100 US500 US30, stratified by the kind of play the
engine names. Charts show only candles before the moment; what happened next is shown after a save, on request.
"""
import argparse
import json
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.concepts.bars import resample  # noqa: E402
from ict_engine.concepts.context import _weekly_bars, completed_daily, weekly_structure_state  # noqa: E402
from ict_engine.concepts.liquidity_map import build  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402
from ict_engine.concepts.events import fvgs, swings  # noqa: E402
from ict_engine.concepts.liquidity_map import _htf_gap  # noqa: E402
from ict_engine.concepts.ob_context import ob_reads, period_bars  # noqa: E402
from ict_engine.concepts.htf_draw import bos_draw  # noqa: E402
from liqmap_build import NY, candles, num, panel, wall  # noqa: E402

OUT = Path("out/read")
ASSETS = ("US100", "US500", "US30")
START, CUT = date(2022, 3, 1), date(2023, 9, 29)
HIST = date(2019, 10, 1)
CLOSED = {date(2022, 4, 15), date(2022, 5, 30), date(2022, 6, 20), date(2022, 7, 4), date(2022, 9, 5), date(2022, 11, 24),
          date(2022, 12, 26), date(2023, 1, 2), date(2023, 1, 16), date(2023, 2, 20), date(2023, 4, 7), date(2023, 5, 29),
          date(2023, 6, 19), date(2023, 7, 4), date(2023, 9, 4)}             # US cash-index holidays in range
PANELS = {"1w": timedelta(days=900), "1d": timedelta(days=240), "4h": timedelta(days=35), "1h": timedelta(days=8)}
FWD = {"1w": timedelta(days=56), "1d": timedelta(days=21), "4h": timedelta(days=7), "1h": timedelta(days=3)}
TF_LEN = {"4h": timedelta(hours=4), "1h": timedelta(hours=1)}
NAME = {"1w": "Weekly", "1d": "Daily", "4h": "4H", "1h": "1H"}
SHORT = {"1w": "W", "1d": "D", "4h": "4H", "1h": "1H"}


def frames(past: pd.DataFrame, d: date, at: pd.Timestamp) -> dict:
    """Completed bars per timeframe at ``at`` (no partial candle)."""
    daily = completed_daily(resample(past, "1d"), d)
    out = {"1w": _weekly_bars(daily), "1d": daily}
    for tf, n in TF_LEN.items():
        f = resample(past, tf)
        out[tf] = f[f.index + n <= at]
    return out


def structure(f: pd.DataFrame) -> dict:
    st, guard, flips = weekly_structure_state(f)
    last = flips[-1] if flips else None
    return {"state": st, "guard": num(guard) if guard is not None else None,
            "since": wall(pd.Timestamp(last[0]).tz_localize(NY) if pd.Timestamp(last[0]).tzinfo is None else last[0]) if last else None,
            "flips": [[wall(pd.Timestamp(t).tz_localize(NY) if pd.Timestamp(t).tzinfo is None else t), s] for t, s in flips[-3:]]}


def trade_range(f: pd.DataFrame, tf: str, side: str, guard: float, past: pd.DataFrame) -> dict | None:
    """The range we're trading (Sharif, 2026-11-16): the fake-out swing against us — for a sell, the protected high,
    which usually took buyside first — to the extreme of the move in our direction since. Bull mirrors."""
    col = "high" if side == "bear" else "low"
    at_guard = f.index[(f[col] - guard).abs() < 0.006]
    if not len(at_guard):
        return None
    t = at_guard[-1]
    since = past[past.index >= t]
    lo, hi = (float(since.low.min()), guard) if side == "bear" else (guard, float(since.high.max()))
    if hi <= lo:
        return None
    # the fake-out: did that swing take an earlier swing's liquidity (buyside for a sell) on the way?
    prior = [e for e in swings(f[f.index < t], tf) if e.origin_ts >= t - 30 * (f.index[1] - f.index[0])]
    took = ([e.top for e in prior if e.kind == "swing_high" and e.top < guard] if side == "bear"
            else [e.bottom for e in prior if e.kind == "swing_low" and e.bottom > guard])
    swept = (max(took) if side == "bear" else min(took)) if took else None
    return {"lo": lo, "hi": hi, "t": wall(t), "t0": t, "swept": swept}


def range_arrays(fr: dict, at: pd.Timestamp, side: str, lo: float, hi: float, t0: pd.Timestamp, price: float) -> list[dict]:
    """4H / 1H gaps on our side (bearish to sell, bullish to buy) inside the range, judged on their own timeframe's closes
    like 1w/1d (closed through → IFVG flipped, closed back → retired). Only arrays of the move in our direction (the
    distribution the range is): a FVG formed after the fake-out swing ``t0``, or an IFVG whose flip came after it.
    Depth = retracement on the fib of the move (0 = its extreme, 1 = the fake-out; Sharif, 2026-11-16 example): a
    shallow array may be all price gives, a deep one (OTE 0.62–0.79) the better price. Neither is wrong; each has a
    risk — shallow: knocked out if price goes deeper; deep: the trade is missed. Momentum decides."""
    out = []
    dep = (lambda p: (hi - p) / (hi - lo)) if side == "bull" else (lambda p: (p - lo) / (hi - lo))
    for tf in ("4h", "1h"):
        f = fr[tf]
        for g in fvgs(f, tf):
            if g.ts >= at:
                continue
            stt = _htf_gap(g, f, at)
            if stt is None:
                continue
            d = g.direction if stt == "fvg" else ("bear" if g.direction == "bull" else "bull")
            if d != side or g.top <= lo or g.bottom >= hi:
                continue
            if stt == "fvg" and g.origin_ts < t0:
                continue
            if stt == "ifvg":
                c = f[(f.close_ts > g.ts) & (f.close_ts < at)].close
                thru = c[(c < g.bottom) if g.direction == "bull" else (c > g.top)]
                if thru.empty or thru.index[0] < t0:
                    continue
            d0, d1 = sorted((dep(g.top), dep(g.bottom)))
            depth = ("deep — risk: price may not come this far, the trade is missed" if d1 >= 0.62 else
                     "around EQ" if d1 >= 0.5 else
                     "shallow — risk: knocked out if price goes deeper")
            out.append({"tf": tf, "kind": stt, "bottom": round(float(g.bottom), 2), "top": round(float(g.top), 2),
                        "d0": d0, "d1": d1, "depth": depth, "formed": wall(g.origin_ts),
                        "label": f"{tf} {'bearish' if d == 'bear' else 'bullish'} {stt.upper()}"})
    now = dep(price)
    ahead = sorted([x for x in out if x["d1"] > now], key=lambda x: x["d0"])            # still on the pullback's way
    return ahead[:6], now


def month_panel(mon: pd.DataFrame, daily: pd.DataFrame) -> list:
    """Completed months + the unfinished current month (from the completed days after the last monthly close)."""
    rows = candles(mon.drop(columns="close_ts"))
    cur = daily[daily["close_ts"] > mon["close_ts"].iloc[-1]] if len(mon) else daily
    if len(cur):
        t = mon.index[-1] + pd.offsets.MonthBegin(1) if len(mon) else cur.index[0]
        rows.append([wall(t), num(cur.open.iloc[0]), num(cur.high.max()), num(cur.low.min()), num(cur.close.iloc[-1])])
    return rows


def lab(x: dict) -> str:
    """'1d swing high', 'London low', '1d previous day low' — the timeframe once, sessions by name."""
    t = x["label"] or x["kind"]
    return t if t.startswith(x["tf"]) or x["tf"] == "session" else f"{x['tf']} {t}"


def fmt_day(ts: int | None, tf: str) -> str:
    if ts is None:
        return "–"
    t = datetime.fromtimestamp(ts, tz=timezone.utc)
    return t.strftime("%d %b %Y") if tf in ("1w", "1d") else t.strftime("%d %b %H:%M")


def read(asset: str, bars: pd.DataFrame, d: date, at: pd.Timestamp | None = None) -> dict | None:
    live = at is not None
    at = at if live else pd.Timestamp(datetime.combine(d, time(8, 30)), tz=NY)
    past = bars[bars.index < at]
    if past.empty or (not live and bars[(bars.index >= at - timedelta(minutes=5)) & (bars.index < at)].empty):
        return None
    fr = frames(past, d, at)
    S = {tf: structure(f) for tf, f in fr.items()}
    m = build(bars, at)
    price, adr = m["price"], m["adr"]
    items = {it["id"]: it for it in m["items"]}
    td = m["key"].get("topdown", {})
    areas = [items[i] for tf in ("1w", "1d") for i in td.get(tf, {}).get("areas", [])]
    bs = [items[i] for tf in ("1w", "1d") for i in td.get(tf, {}).get("buyside", [])]
    ss = [items[i] for tf in ("1w", "1d") for i in td.get(tf, {}).get("sellside", [])]
    for tf in ("4h", "1h"):
        nb, ns = m["key"]["nearest"].get(tf, {}).get("buyside"), m["key"]["nearest"].get(tf, {}).get("sellside")
        bs += [items[nb]] if nb else []
        ss += [items[ns]] if ns else []
    dedup = lambda xs: list({x["id"]: x for x in xs}.values())
    areas, bs, ss = dedup(areas), sorted(dedup(bs), key=lambda x: x["price"]), sorted(dedup(ss), key=lambda x: -x["price"])

    # statements
    st, marks = [], []
    for tf in ("1w", "1d", "4h", "1h"):
        s = S[tf]
        if s["state"] == "neutral":
            st.append({"id": f"s_{tf}", "tf": tf, "text": f"{NAME[tf]}: no structure break yet — no side on this timeframe."})
            continue
        lvl = "lower high" if s["state"] == "bear" else "higher low"
        dist = abs(price - s["guard"]) / adr if s["guard"] else 0
        st.append({"id": f"s_{tf}", "tf": tf, "text": f"{NAME[tf]}: {s['state']} since {fmt_day(s['since'], tf)}. "
                   f"Protected {lvl} {s['guard']:.2f} ({dist:.1f} ADR away) — until a {SHORT[tf]} close breaks it, "
                   f"moves the other way are shifts inside a {s['state']} trend."})
    inside = [a for a in areas if a["bottom"] <= price <= a["top"]]
    if areas:
        txt = "; ".join(f"{a['tf']} {a['kind'].upper()} {a['bottom']:.2f}–{a['top']:.2f} "
                        f"({'price is inside' if a in inside else a['where'] + f', {a['dist_adr']:.1f} ADR'})" for a in areas[:5])
        st.append({"id": "s_areas", "tf": "", "text": f"Areas I'm watching: {txt}."})
    liq = []
    if bs:
        liq.append("buyside above: " + ", ".join(f"{lab(b)} {b['price']:.2f} ({b['dist_adr']:.1f} ADR)" for b in bs[:3]))
    if ss:
        liq.append("sellside below: " + ", ".join(f"{lab(s_)} {s_['price']:.2f} ({s_['dist_adr']:.1f} ADR)" for s_ in ss[:3]))
    if liq:
        st.append({"id": "s_liq", "tf": "", "text": "Liquidity — " + "; ".join(liq) + "."})

    W, D, H4, H1 = (S[tf]["state"] for tf in ("1w", "1d", "4h", "1h"))
    side = lambda x: {"bull": "buyside", "bear": "sellside"}.get(x)
    pool = lambda x: (bs[0] if x == "bull" and bs else ss[0] if x == "bear" and ss else None)
    htf = lambda x: next((p for p in (bs if x == "bull" else ss) if p["tf"] in ("1w", "1d") and p is not pool(x)), None)
    nm = lambda p: f"{lab(p)} {p['price']:.2f}" if p else "–"
    if W == "neutral":
        play, kind = ("No weekly side yet: the play is on the daily and lower — near liquidity only "
                      f"({nm(pool(D))} if the daily holds)."), "no_weekly"
    elif D == W and H4 == W and H1 == W:
        play, kind = (f"Everything lines up {W}: the play respects the higher TF — a continuation toward the {side(W)}: "
                      f"next {nm(pool(W))}, then the higher-TF draw {nm(htf(W))}; the weekly allows the distant targets."), "aligned"
    elif D != W and D != "neutral":
        play, kind = (f"Daily {D} against the weekly {W}: the play sits on the daily — a counter-weekly leg. Expect small "
                      f"grabs ({nm(pool(D))}), not the distant weekly areas; the weekly protected level "
                      f"{S['1w']['guard']:.2f} decides if it becomes more."), "counter_weekly"
    elif D == W and (H4 not in (W, "neutral") or H1 not in (W, "neutral")):
        lt = "4H" if H4 not in (W, "neutral") else "1H"
        lx = H4 if lt == "4H" else H1
        play, kind = (f"Weekly and daily {W}, the {lt} against them: a lower-TF pullback reaching for lower-TF {side(lx)} "
                      f"({nm(pool(lx))}) — the higher TF should be respected at an area"
                      f"{' (price is inside one now)' if inside else ''}, then {W} resumes toward {nm(htf(W))}."), "ltf_pullback"
    else:
        play, kind = (f"Weekly {W}, lower timeframes mixed: no clear play — wait for a {SHORT['1h']}/{SHORT['4h']} "
                      f"break in the weekly direction."), "mixed"
    mon = period_bars(fr["1d"], "M", at)
    chain = bos_draw(mon, "1M", at)
    play_side = D if kind == "counter_weekly" else (W if W != "neutral" else D)
    if chain and chain["bos"]["direction"] == play_side and chain["draw"] and not chain["draw"]["reached"]:
        eq, dr = chain["equal"], chain["draw"]
        first = (f"first the 1M equal {'lows' if play_side == 'bear' else 'highs'} {eq['level']:.2f}, then "
                 if eq and not eq["taken"] else "")
        play += (f" The higher-TF draw (monthly): {first}the 1M FVG {dr['fvg'][0]:.2f}–{dr['fvg'][1]:.2f}, its near edge "
                 f"{dr['edge']:.2f} = the target.")
    if inside:
        play += f" Price is inside the {inside[0]['tf']} {inside[0]['kind'].upper()} — respect there (reaction, closes holding) comes first."
    st.append({"id": "s_play", "tf": "", "text": "Where the play is: " + play})

    # the range we're trading: the protected level on the play's timeframe (4H first) → the extreme since; sell in its
    # premium half (or a bit cheaper, at a bearish array on EQ), buy in its discount half
    want_side = D if kind == "counter_weekly" else (W if W != "neutral" else D)
    rtf = next((tf for tf in ("4h", "1d", "1h") if S[tf]["state"] == want_side and S[tf]["guard"] is not None), None)
    r = trade_range(fr[rtf], rtf, want_side, S[rtf]["guard"], past) if rtf else None
    if r:
        lo, hi = r["lo"], r["hi"]
        eq, frac = (lo + hi) / 2, (price - lo) / (hi - lo)
        want = "premium" if want_side == "bear" else "discount"
        verb = "sell" if want == "premium" else "buy"
        zone = "premium" if frac > 0.5 else "discount"
        arr, now_d = range_arrays(fr, at, want_side, lo, hi, r["t0"], price)
        ext, fk = (hi, lo) if want_side == "bull" else (lo, hi)
        lv = lambda q: ext + (fk - ext) * q
        if want_side == "bear":
            anchor = (f"the fake-out high {hi:.2f} (it took buyside {r['swept']:.2f} first, against us)" if r["swept"]
                      else f"the protected high {hi:.2f}") + f" → the low of the move down since, {lo:.2f}"
        else:
            anchor = (f"the fake-out low {lo:.2f} (it took sellside {r['swept']:.2f} first, against us)" if r["swept"]
                      else f"the protected low {lo:.2f}") + f" → the high of the move up since, {hi:.2f}"
        ext_t = (since_ext := past[past.index >= r["t0"]])["high" if want_side == "bull" else "low"]
        ext_t = ext_t.idxmax() if want_side == "bull" else ext_t.idxmin()
        nb = int(((fr[rtf].index >= r["t0"]) & (fr[rtf].index <= ext_t)).sum())
        mom = f"momentum: the move ran {(hi - lo) / adr:.1f} ADR in {nb} {SHORT[rtf]} candle{'s' if nb != 1 else ''}"
        fib = f"fib of the move: 0 = {ext:.2f}, 0.5 EQ = {lv(.5):.2f}, OTE 0.62–0.79 = {lv(.62):.2f}–{lv(.79):.2f}, 1 = {fk:.2f}"
        arr_t = ("; ".join(f"{x['label']} {x['bottom']:.2f}–{x['top']:.2f} ({x['d0']:.2f}–{x['d1']:.2f}, {x['depth']})"
                           for x in arr) if arr else "none left between price and the fake-out")
        where = ("price is at the extreme of the move (0) — no pullback yet" if now_d <= 0.05 else
                 f"price has pulled back to {now_d:.2f}" + (" — in the OTE now" if 0.62 <= now_d <= 0.79 else
                                                              " — past the OTE, the range is at risk" if now_d > 0.79 else ""))
        st.append({"id": "s_range", "tf": rtf, "text": f"Current range ({SHORT[rtf]}): {anchor} — the distribution our "
                   f"PD arrays come from ({mom}). {fib}; {where}. Hoping for a {want}: {'buy' if want_side == 'bull' else 'sell'} "
                   f"at an array on the pullback, in the order price meets them: {arr_t}. Shallow or deep is not right or wrong: "
                   f"shallow risks a knock-out, deep risks missing it — momentum decides. Target beyond the move: the liquidity in the play above."})
        marks.append({"type": "range", "tf": rtf, "t": r["t"], "low": round(lo, 2), "high": round(hi, 2), "want": want,
                      "label": f"{SHORT[rtf]} range"})
        for x in arr:
            marks.append({"type": "zone", "grp": "range", "tf": x["tf"], "t": x["formed"], "top": x["top"], "bottom": x["bottom"],
                          "label": f"{x['label']} {x['d0']:.2f}–{x['d1']:.2f}"})
    for tf, s in S.items():
        if s["guard"] is not None and s["state"] != "neutral":
            marks.append({"type": "level", "tf": tf, "price": s["guard"], "color": "down" if s["state"] == "bear" else "up",
                          "label": f"{SHORT[tf]} protected {'LH' if s['state'] == 'bear' else 'HL'}"})
        for t, to in s["flips"]:
            marks.append({"type": "vline", "tf": tf, "t": t, "color": "up" if to == "bull" else "down",
                          "label": f"{SHORT[tf]} → {to}"})
    for a in areas[:5]:
        marks.append({"type": "zone", "tf": a["tf"], "top": a["top"], "bottom": a["bottom"], "label": f"{a['tf']} {a['kind'].upper()}"})
    for b in bs[:3]:
        marks.append({"type": "level", "tf": b["tf"] if b["tf"] in SHORT else "1h", "price": b["price"], "color": "bs",
                      "label": f"BSL {lab(b)}"})
    for s_ in ss[:3]:
        marks.append({"type": "level", "tf": s_["tf"] if s_["tf"] in SHORT else "1h", "price": s_["price"], "color": "ss",
                      "label": f"SSL {lab(s_)}"})
    # monthly panel + order blocks (monthly / weekly) in their place, with their draw (live reads; ruling §22)
    wk = period_bars(fr["1d"], "W", at)
    obs = []
    for tf, x, hi in (("1M", mon, None), ("1w", wk, [(mon, "1M")]), ("1d", fr["1d"], [(mon, "1M"), (wk, "1w")])):
        for r in ob_reads(x, tf, at, last=2, fine=fr["1d"] if tf != "1d" else fr["1h"], htf=hi):
            ev = r["event"]
            ev_t = (f"after {ev['what']} {ev['price']:.2f} (to {ev['extreme']:.2f})" if ev else "no event before it — just a candle")
            pl = r["place"]
            fits = "the right place" if pl["fits"] else "the wrong half"
            dr = r["draw"]
            dr_t = (f" Draw: the remaining {dr['tf']} FVG {dr['fvg'][0]:.2f}–{dr['fvg'][1]:.2f} (CE {dr['ce']:.2f})"
                    + (f", liquidity at its edge {dr['liquidity']:.2f}" if dr["liquidity"] else "") + f" — {dr['state']}." if dr else "")
            when = {"1M": f"{r['candle']:%b %Y}", "1w": f"wk {r['candle']:%d %b %Y}", "1d": f"{r['candle'] + timedelta(hours=6):%d %b %Y}"}[tf]
            live_ob = bool(ev) and pl["fits"] and not r["state"].startswith("failed")
            why = ", ".join(w for w, bad in (("no event", not ev), ("wrong half", not pl["fits"])) if bad)
            tag = ("tradeable" if live_ob else "not one to use: " + ", ".join(x for x in (why, r["state"] if
                   r["state"].startswith("failed") else "") if x))
            if not r["state"].startswith("failed"):
                tag += f"; {r['state']}"
            obs.append(f"{tf} {r['direction']}ish OB {when} [{tag}]: body "
                       f"{r['body'][0]:.2f}–{r['body'][1]:.2f} (MT {r['mt']:.2f}), {ev_t}; {pl['zone']} {pl['fraction']:.2f} of "
                       f"the {pl['basis']} {pl['range'][0]:.2f}–{pl['range'][1]:.2f} = {fits}.{dr_t}")
            T = {"1M": "M", "1w": "W", "1d": "D"}[tf]
            if live_ob:                           # only an OB with an event, in the right half, not failed is drawn
                marks.append({"type": "zone", "grp": "struct", "tf": tf, "own": True, "t": wall(r["candle"]),
                              "top": r["body"][1], "bottom": r["body"][0],
                              "label": f"{T} {'bear' if r['direction'] == 'bear' else 'bull'} OB"
                                       + ("" if r["state"] == "holding" else " (" + r["state"].split(" (")[0] + ")")})
            same = chain and chain["draw"] and dr and tuple(dr["fvg"]) == tuple(chain["draw"]["fvg"])   # drawn once below
            if live_ob and dr and dr["tf"] == tf and not same:
                marks.append({"type": "zone", "grp": "struct", "tf": tf, "own": True, "top": dr["fvg"][1],
                              "bottom": dr["fvg"][0], "label": f"{T} draw FVG (after the OB)"})
    if obs:
        st.insert(0, {"id": "s_ob", "tf": "1M", "text": "Order blocks: " + " | ".join(obs)})
    if chain:                                     # the monthly story first: BOS → equal lows/highs → the draw beyond
        b, eq, dr = chain["bos"], chain["equal"], chain["draw"]
        bear = b["direction"] == "bear"
        t = (f"Monthly: structure broke {'down' if bear else 'up'} — {b['candle']:%b %Y} closed {b['close']:.2f} "
             f"{'below' if bear else 'above'} the {b['swing']:%b %Y} swing {'low' if bear else 'high'} {b['level']:.2f} (BOS).")
        if eq:
            t += (f" Equal {'lows' if bear else 'highs'} {eq['level']:.2f} ("
                  + ", ".join(f"{c:%b %Y} {p_:.2f}" for c, p_ in zip(eq["candles"], eq["prices"]))
                  + f") = the {'sellside' if bear else 'buyside'} that leg is drawn to"
                  + (f"; taken in {eq['taken']['candle']:%b %Y} ({eq['taken']['extreme']:.2f})." if eq["taken"] else "; still resting."))
            marks.append({"type": "level", "tf": "1M", "price": eq["level"], "color": "ss" if bear else "bs",
                          "label": f"M EQ{'L' if bear else 'H'}" + (" (taken)" if eq["taken"] else "")})
        if dr:
            t += (f" Beyond them, the interest: the 1M FVG {dr['fvg'][0]:.2f}–{dr['fvg'][1]:.2f} (CE {dr['ce']:.2f}), "
                  f"near edge {dr['edge']:.2f} — {'reached' if dr['reached'] else 'not reached yet'}.")
            marks.append({"type": "zone", "grp": "struct", "tf": "1M", "top": dr["fvg"][1], "bottom": dr["fvg"][0],
                          "label": "M draw FVG (after BOS + EQ)"})
        marks.append({"type": "level", "tf": "1M", "price": b["level"], "color": "ss" if bear else "bs",
                      "label": f"M BOS {b['level']:.2f}"})
        st.insert(0, {"id": "s_mbos", "tf": "1M", "text": t})
    fwd_bars = bars[(bars.index >= at)]
    return {"id": f"{asset}-{d:%Y%m%d}", "asset": asset, "day": str(d), "at": wall(at), "price": price, "adr": adr,
            "kind": kind, "structure": S, "statements": st, "marks": marks,
            "panels": {"1M": month_panel(mon, fr["1d"]),
                       **{tf: panel(past, tf, at - span, at) for tf, span in PANELS.items()}},
            "fwd": {tf: panel(fwd_bars, tf, at, at + FWD[tf]) for tf in PANELS}}


def live(at: pd.Timestamp, assets=("US100", "US500")):
    """The current chart (US100, US500): a live read, not a test — no selection is made from it."""
    out = Path("out/read-live")
    (out / "s").mkdir(parents=True, exist_ok=True)
    ids = []
    for x in assets:
        bars = dukascopy.load(x, at.date() - timedelta(days=1000), at.date() + timedelta(days=1))
        it = read(x, bars, at.date(), at=at)
        it["id"] = f"{x}-live-{at:%Y%m%d}"
        (out / "s" / f"{it['id']}.json").write_text(json.dumps(it, separators=(",", ":")))
        ids.append(it["id"]); print(it["id"], it["kind"])
    old = json.loads((out / "index.json").read_text())["ids"] if (out / "index.json").exists() else []
    ids = list(dict.fromkeys(old + ids))
    (out / "index.json").write_text(json.dumps({"generated": str(date.today()), "live": str(at), "ids": ids}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--assets", default="US100,US500", help="--live only: comma-separated assets")
    ap.add_argument("--live", help="one read per index as of this NY time, e.g. '2026-11-15 18:00' (Sunday open: "
                                   "Friday's day and week count as closed) → out/read-live")
    a = ap.parse_args()
    if a.live:
        return live(pd.Timestamp(a.live, tz=NY), tuple(a.assets.split(",")))
    rnd = random.Random(a.seed)
    bars = {x: dukascopy.load(x, HIST, CUT + timedelta(days=60)) for x in ASSETS}
    days = [START + timedelta(days=i) for i in range((CUT - START).days)]
    days = [d for d in days if d.weekday() < 5 and d not in CLOSED]
    kinds = ("aligned", "counter_weekly", "ltf_pullback")
    want = {k: a.n // len(kinds) for k in kinds}
    got, used, tries = {k: [] for k in kinds}, [], 0
    while any(len(got[k]) < want[k] for k in kinds) and tries < 600:
        tries += 1
        x, d = rnd.choice(ASSETS), rnd.choice(days)
        if any(abs((d - u).days) < 21 for u in used):                     # spread across time, all indices
            continue
        try:
            it = read(x, bars[x], d)
        except (ValueError, KeyError):
            continue
        if it and it["kind"] in got and len(got[it["kind"]]) < want[it["kind"]]:
            got[it["kind"]].append(it); used.append(d)
            print(it["id"], it["kind"], flush=True)
    items = [it for k in kinds for it in got[k]]
    rnd.shuffle(items)
    (OUT / "s").mkdir(parents=True, exist_ok=True)
    for it in items:
        (OUT / "s" / f"{it['id']}.json").write_text(json.dumps(it, separators=(",", ":")))
    (OUT / "index.json").write_text(json.dumps({"generated": str(date.today()), "seed": a.seed,
                                                "ids": [it["id"] for it in items]}, indent=1))
    print(len(items), "moments →", OUT / "index.json", "| tries", tries)


if __name__ == "__main__":
    main()
