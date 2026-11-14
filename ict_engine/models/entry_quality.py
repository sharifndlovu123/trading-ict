"""Entry-quality gates for every model (research/preregistered-entry-quality-2026-11-14.md; ICT rulings §14).

Sharif: "we need a sweep, an aggressive move to show some movement"; "if we see too much consolidation within a key
zone, and no aggressive pushes against it, it's not so valid".

    sweep_disp  in the 60 min before the decision: a sweep of a session level (ctx.liquidity) or a 5m/15m swing on the
                side opposite the trade, THEN a 5m displacement candle in the trade direction (closed by the decision)
    no_chop     of the last 12 closed 5m candles before the decision, fewer than 6 trade inside the entry zone (the POI
                the model returned to when it has one, else its entry FVG)
    both        both gates

Location gates (research/preregistered-nested-fvg-2026-11-14.md; Sharif's batch 3, review log #14-15):

    nested_4h          the entry FVG's midpoint lies inside a 4h FVG of the trade's direction, formed before the
                       decision and still valid then (no 1m body close beyond its far edge)
    outside_daily_fvg  no trade when the entry price lies inside any daily FVG still valid at the decision

Only bars at or before the decision are read.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import Event, displacement_mask, fvgs, gap_lifecycle, sweeps, swing_levels, swings

GATES = ("sweep_disp", "no_chop", "both", "nested_4h", "outside_daily_fvg")
HTF_LOOKBACK = {"4h": timedelta(days=20), "1d": timedelta(days=90)}
SWEEP_WINDOW = timedelta(minutes=60)
CHOP_BARS, CHOP_MAX = 12, 6


def _upto(bars: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    i0, i1 = bars.index.searchsorted(start, side="left"), bars.index.searchsorted(end, side="right")
    return bars.iloc[i0:i1]


def sweep_then_displacement(long: bool, decided: pd.Timestamp, bars_1m: pd.DataFrame, ctx) -> tuple[bool, str]:
    hist = _upto(bars_1m, decided - timedelta(hours=24), decided)
    if hist.empty:
        return False, "no bars"
    side = "low" if long else "high"
    levels = [lv for lv in getattr(ctx, "liquidity", ()) if lv.side == side]
    for tf in ("5m", "15m"):
        b = resample(hist, tf)
        b = b[b.close_ts <= decided]
        levels += [lv for lv in swing_levels([e for e in swings(b, tf) if e.ts <= decided]) if lv.side == side]
    want = "bull" if long else "bear"
    sw = [e for e in sweeps(hist, levels, until=decided)
          if e.kind == "sweep" and e.direction == want and decided - SWEEP_WINDOW <= e.ts <= decided]
    if not sw:
        return False, "no sweep of opposite-side liquidity in the hour before"
    first = min(sw, key=lambda e: e.ts)
    b5 = resample(_upto(bars_1m, decided - timedelta(hours=6), decided), "5m")
    b5 = b5[b5.close_ts <= decided]
    disp = displacement_mask(b5)
    up = (b5.close > b5.open).to_numpy() if long else (b5.close < b5.open).to_numpy()
    after = (b5.close_ts >= first.ts).to_numpy()
    hit = disp & up & after
    if not hit.any():
        return False, f"swept {first.meta.get('level')} at {first.ts:%H:%M} but no 5m displacement after it"
    t = pd.Timestamp(b5.close_ts.to_numpy()[hit.argmax()])
    return True, f"swept {first.meta.get('level')} at {first.ts:%H:%M}, 5m displacement closed {t:%H:%M}"


def zone_of(setup) -> Event | None:
    poi = setup.evidence.get("poi")
    if isinstance(poi, Event) and poi.top > poi.bottom:
        return poi
    return setup.evidence.get("fvg")


def no_chop(setup, decided: pd.Timestamp, bars_1m: pd.DataFrame) -> tuple[bool, str]:
    z = zone_of(setup)
    if z is None:
        return True, "no zone"
    b5 = resample(_upto(bars_1m, decided - timedelta(hours=3), decided), "5m")
    b5 = b5[b5.close_ts <= decided].tail(CHOP_BARS)
    inside = int(((b5.high >= z.bottom) & (b5.low <= z.top)).sum())
    return inside < CHOP_MAX, f"{inside} of the last {len(b5)} 5m candles inside the zone {z.bottom:.2f}-{z.top:.2f}"


def _live_htf_fvgs(bars_1m: pd.DataFrame, decided: pd.Timestamp, tf: str) -> list[Event]:
    hist = _upto(bars_1m, decided - HTF_LOOKBACK[tf], decided)
    if hist.empty:
        return []
    b = resample(hist, tf)
    b = b[b.close_ts <= decided]
    return [g for g in fvgs(b, tf) if g.ts < decided and gap_lifecycle(g, hist, until=decided).valid_at(decided)]


def nested_4h(setup, bars_1m: pd.DataFrame) -> tuple[bool, str]:
    z = setup.evidence.get("fvg")
    if z is None:
        return False, "no entry FVG"
    mid = (z.top + z.bottom) / 2
    want = "bull" if setup.side == "long" else "bear"
    for g in _live_htf_fvgs(bars_1m, setup.decided_at, "4h"):
        if g.direction == want and g.bottom <= mid <= g.top:
            return True, f"entry FVG {z.bottom:.2f}-{z.top:.2f} inside 4h {want} FVG {g.bottom:.2f}-{g.top:.2f}"
    return False, f"entry FVG {z.bottom:.2f}-{z.top:.2f} not inside a live 4h {want} FVG"


def outside_daily_fvg(setup, bars_1m: pd.DataFrame) -> tuple[bool, str]:
    plan = setup.plan or setup.would_plan
    if plan is None:
        return True, "no plan"
    for g in _live_htf_fvgs(bars_1m, setup.decided_at, "1d"):
        if g.bottom <= plan.entry <= g.top:
            return False, f"entry {plan.entry:.2f} inside daily {g.direction} FVG {g.bottom:.2f}-{g.top:.2f}"
    return True, f"entry {plan.entry:.2f} outside live daily FVGs"


def check(setup, bars_1m: pd.DataFrame, ctx, gate: str) -> tuple[bool, str]:
    if gate not in GATES:
        raise ValueError(f"entry_gate must be one of {GATES}, got {gate!r}")
    if gate == "nested_4h":
        return nested_4h(setup, bars_1m)
    if gate == "outside_daily_fvg":
        return outside_daily_fvg(setup, bars_1m)
    long = setup.side == "long"
    decided = setup.decided_at
    out = []
    if gate in ("sweep_disp", "both"):
        ok, why = sweep_then_displacement(long, decided, bars_1m, ctx)
        if not ok:
            return False, why
        out.append(why)
    if gate in ("no_chop", "both"):
        ok, why = no_chop(setup, decided, bars_1m)
        if not ok:
            return False, "chop: " + why
        out.append(why)
    return True, "; ".join(out)
