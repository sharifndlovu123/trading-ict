"""Entry-quality gates for every model (research/preregistered-entry-quality-2026-11-14.md; ICT rulings §14).

Sharif: "we need a sweep, an aggressive move to show some movement"; "if we see too much consolidation within a key
zone, and no aggressive pushes against it, it's not so valid".

    sweep_disp  in the 60 min before the decision: a sweep of a session level (ctx.liquidity) or a 5m/15m swing on the
                side opposite the trade, THEN a 5m displacement candle in the trade direction (closed by the decision)
    no_chop     of the last 12 closed 5m candles before the decision, fewer than 6 trade inside the entry zone (the POI
                the model returned to when it has one, else its entry FVG)
    both        both gates

Only bars at or before the decision are read.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import Event, displacement_mask, sweeps, swing_levels, swings

GATES = ("sweep_disp", "no_chop", "both")
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


def check(setup, bars_1m: pd.DataFrame, ctx, gate: str) -> tuple[bool, str]:
    if gate not in GATES:
        raise ValueError(f"entry_gate must be one of {GATES}, got {gate!r}")
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
