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
from ict_engine.concepts.events import swings  # noqa: E402
from liqmap_build import NY, num, panel, wall  # noqa: E402

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


def current_range(f: pd.DataFrame, tf: str, past: pd.DataFrame) -> tuple[float, float] | None:
    """The range price is in now on ``tf``: the latest confirmed swing high and swing low (completed bars), each stretched
    to any new extreme made since (1m bars up to the moment), so it always contains price."""
    sw = swings(f, tf)
    H = next((e for e in reversed(sw) if e.kind == "swing_high"), None)
    L = next((e for e in reversed(sw) if e.kind == "swing_low"), None)
    if H is None or L is None:
        return None
    hi = max(H.top, float(past[past.index >= H.origin_ts].high.max()))
    lo = min(L.bottom, float(past[past.index >= L.origin_ts].low.min()))
    return (lo, hi) if hi > lo else None


def lab(x: dict) -> str:
    """'1d swing high', 'London low', '1d previous day low' — the timeframe once, sessions by name."""
    t = x["label"] or x["kind"]
    return t if t.startswith(x["tf"]) or x["tf"] == "session" else f"{x['tf']} {t}"


def fmt_day(ts: int | None, tf: str) -> str:
    if ts is None:
        return "–"
    t = datetime.fromtimestamp(ts, tz=timezone.utc)
    return t.strftime("%d %b %Y") if tf in ("1w", "1d") else t.strftime("%d %b %H:%M")


def read(asset: str, bars: pd.DataFrame, d: date) -> dict | None:
    at = pd.Timestamp(datetime.combine(d, time(8, 30)), tz=NY)
    past = bars[bars.index < at]
    if past.empty or bars[(bars.index >= at - timedelta(minutes=5)) & (bars.index < at)].empty:
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
    htf = lambda x: next((p for p in (bs if x == "bull" else ss) if p["tf"] in ("1w", "1d")), None)
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
    if inside:
        play += f" Price is inside the {inside[0]['tf']} {inside[0]['kind'].upper()} — respect there (reaction, closes holding) comes first."
    st.append({"id": "s_play", "tf": "", "text": "Where the play is: " + play})

    # the current range (framework §3): the 1H range = the leg we're in; the daily range = the HTF one.
    # Sell only in premium of both, buy only in discount of both — the side comes from the play.
    want_side = D if kind == "counter_weekly" else (W if W != "neutral" else D)
    ranges = []
    for tf, nm_ in (("1h", "1H range"), ("1d", "Daily range")):
        r = current_range(fr[tf], tf, past)
        if r:
            ranges.append((tf, nm_, *r))
    if ranges and want_side in ("bull", "bear"):
        want = "premium" if want_side == "bear" else "discount"
        parts, ok = [], []
        for tf, nm_, lo, hi in ranges:
            frac = (price - lo) / (hi - lo)
            zone = "premium" if frac > 0.5 else "discount"
            ok.append(zone == want)
            parts.append(f"{nm_} {lo:.2f}–{hi:.2f} (EQ {(lo + hi) / 2:.2f}): price at {frac:.0%} = {zone}")
        tf0, _, lo, hi = ranges[0]
        ote = (lo + 0.62 * (hi - lo), lo + 0.79 * (hi - lo)) if want == "premium" else (hi - 0.79 * (hi - lo), hi - 0.62 * (hi - lo))
        verb = "sell" if want == "premium" else "buy"
        now = ("price is already in " + want + " of both — this is where the engine would look"
               if all(ok) else f"not there yet — wait for price to come into {want}" if not any(ok)
               else "only one range agrees — not both yet")
        st.append({"id": "s_range", "tf": tf0, "text": "Current range: " + "; ".join(parts) + f". The play is {want_side}, "
                   f"so I'm hoping for a {want}: {verb} only in {want} of both (OTE 62–79% of the {ranges[0][1]} = "
                   f"{ote[0]:.2f}–{ote[1]:.2f}); {now}."})
        for tf, nm_, lo, hi in ranges:
            marks.append({"type": "range", "tf": tf, "low": lo, "high": hi, "want": want, "label": nm_})

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
    fwd_bars = bars[(bars.index >= at)]
    return {"id": f"{asset}-{d:%Y%m%d}", "asset": asset, "day": str(d), "at": wall(at), "price": price, "adr": adr,
            "kind": kind, "structure": S, "statements": st, "marks": marks,
            "panels": {tf: panel(past, tf, at - span, at) for tf, span in PANELS.items()},
            "fwd": {tf: panel(fwd_bars, tf, at, at + FWD[tf]) for tf in PANELS}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args()
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
