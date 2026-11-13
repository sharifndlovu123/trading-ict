"""ICT 2022 Model — models.md card #2 (+ 2022 Mentorship notes).

Sequence (long; short is the mirror):
    1 liquidity  sell-side taken (sweep or run of a context level or a confirmed swing low)
    2 shift      bullish MSS on the entry timeframe, after the liquidity was taken
    3 fvg        bullish FVG created by displacement inside that leg ("secret handshake")
    → gates      time window → daily bias → discount (intraday leg, and HTF range) → HTF POI → trigger → target
    → plan       limit at the FVG; stop beyond the swept extreme; TP1 = nearest untaken
                 buy-side; final = nearest untaken external level (PDH/Asia high/PWH)

Event-driven but look-ahead free: for each MSS the model only uses events whose
``ts`` (time known) is at or before the decision time, and gap validity is checked
with ``until=decision``. Every MSS becomes a Setup; gates record why it did or
didn't trade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.clock import WINDOWS, Window
from ict_engine.concepts.context import DayContext, build_context, pricing
from ict_engine.concepts.events import (
    Event, fvgs, gap_lifecycle, structure, sweeps, swing_levels, swings,
)
from ict_engine.models.base import Gate, Setup, TradePlan

NY = "America/New_York"
MODEL = "2022_model"

HTF_LIQUIDITY = {"pdl", "pwl", "asia_low", "pdh", "pwh", "asia_high"}
EXTERNAL_HIGH = ("asia_high", "pdh", "pwh")
EXTERNAL_LOW = ("asia_low", "pdl", "pwl")


@dataclass(frozen=True)
class Params:
    entry_tf: str = "1m"
    windows: tuple[str, ...] = ("london_kz", "ny_am_kz", "ny_pm_kz")
    sweep_lookback_min: int = 90         # liquidity must be taken within this many minutes before the MSS
    leg_bars_after_mss: int = 3          # FVG may finish forming up to N bars after the MSS candle
    fvg_pick: str = "deepest"            # deepest (lowest for buys) | nearest (closest to the MSS)
    entry_level: str = "proximal"        # proximal | ce | distal
    use_bias: bool = True
    use_pricing: bool = True
    use_htf_pricing: bool = True         # framework §3: discount of BOTH ranges
    use_poi: bool = True
    min_potential: float = 10.0          # handles from entry to final target (ICT minimum framework)
    stop_buffer: float = 0.25
    poi_tfs: tuple[str, ...] = ("1h", "4h")
    tags: dict = field(default_factory=dict, compare=False)

    @property
    def variant(self) -> str:
        off = [n for n, on in (("bias", self.use_bias), ("pricing", self.use_pricing),
                               ("htf", self.use_htf_pricing), ("poi", self.use_poi)) if not on]
        win = "+".join(w.replace("_kz", "").replace("macro_", "m") for w in self.windows)
        base = f"{self.entry_tf}-{self.entry_level}-{self.fvg_pick}-[{win}]"
        return base + ("-no_" + "_".join(off) if off else "")


def _ts(d: date, t: time) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d, t), tz=NY)


def _window_at(ts: pd.Timestamp, names: tuple[str, ...]) -> Window | None:
    for w in WINDOWS:
        if w.name in names and w.contains(ts.time()):
            return w
    return None


def _window_end(ts: pd.Timestamp, w: Window) -> pd.Timestamp:
    end = _ts(ts.date(), w.end)
    return end if end > ts else end + timedelta(days=1)


def find_setups(bars_1m: pd.DataFrame, day: date, asset: str, p: Params = Params(),
                ctx: DayContext | None = None) -> list[Setup]:
    """All 2022-model setups on ``day`` (00:00–16:00 NY), each with its gate trace and plan."""
    ctx = ctx or build_context(bars_1m, day)
    d0, d1 = _ts(day, time(0)), _ts(day, time(16))
    day_1m = bars_1m[(bars_1m.index >= d0) & (bars_1m.index < d1)].assign(close_ts=lambda x: x.index)
    if day_1m.empty:
        return []
    etf = day_1m if p.entry_tf == "1m" else resample(day_1m.drop(columns="close_ts"), p.entry_tf)

    sw_entry = swings(etf, p.entry_tf)
    sw_5m = swings(resample(day_1m.drop(columns="close_ts"), "5m"), "5m")
    levels = list(ctx.liquidity) + swing_levels(sw_entry) + swing_levels(sw_5m)
    taken = sweeps(day_1m, levels)                                   # first take of each level
    shifts = [e for e in structure(etf, p.entry_tf, sw_entry) if e.kind == "mss"]
    gaps = [g for g in fvgs(etf, p.entry_tf) if g.meta.get("displacement")]

    hist = bars_1m[(bars_1m.index >= d0 - timedelta(days=10)) & (bars_1m.index < d1)]
    htf_gaps = [g for tf in p.poi_tfs for g in fvgs(resample(hist, tf), tf)]
    swing_highs_lows = sw_5m + sw_entry

    out = []
    for mss in shifts:
        out.append(_evaluate(mss, ctx, day, asset, p, day_1m, taken, gaps, htf_gaps, swing_highs_lows))
    return out


def _evaluate(mss: Event, ctx, day, asset, p: Params, day_1m, taken, gaps, htf_gaps, swing_pts) -> Setup:
    long = mss.direction == "bull"
    side = "long" if long else "short"
    decided = mss.ts
    setup = Setup(MODEL, p.variant, asset, "day", day, side, decided, {"shift": mss},
                  pd_array="fvg", pd_array_tf=p.entry_tf)

    # 1 — liquidity on the opposite side, taken before the shift
    want = "low" if long else "high"
    liq = [e for e in taken
           if e.meta["level"] and _side_of(e) == want
           and mss.origin_ts - timedelta(minutes=p.sweep_lookback_min) <= e.origin_ts < mss.origin_ts
           and e.ts <= decided]
    if not liq:
        setup.gates.append(Gate("trigger", False, "no opposite liquidity taken before the MSS"))
        return setup
    liquidity = max(liq, key=lambda e: e.origin_ts)
    setup.evidence["liquidity"] = liquidity

    # 3 — displacement FVG in the leg
    leg_end = mss.origin_ts + timedelta(minutes=p.leg_bars_after_mss * _tf_minutes(p.entry_tf))
    cands = [g for g in gaps if g.direction == mss.direction and liquidity.origin_ts < g.origin_ts <= leg_end]
    if not cands:
        setup.gates.append(Gate("trigger", False, "MSS without a displacement FVG"))
        return setup
    if p.fvg_pick == "deepest":
        fvg = min(cands, key=lambda g: g.bottom) if long else max(cands, key=lambda g: g.top)
    else:
        fvg = max(cands, key=lambda g: g.origin_ts)
    decided = max(decided, fvg.ts)
    setup.decided_at = decided
    if not gap_lifecycle(fvg, day_1m, until=decided).valid_at(decided):
        setup.gates.append(Gate("trigger", False, "FVG already invalidated at decision time"))
        return setup
    setup.evidence["fvg"] = fvg

    entry = {"proximal": fvg.top if long else fvg.bottom, "ce": fvg.ce,
             "distal": fvg.bottom if long else fvg.top}[p.entry_level]
    # stop beyond the extreme of the manipulation: lowest low (highest high) from the liquidity grab to the MSS
    manip = day_1m[(day_1m.index >= liquidity.origin_ts) & (day_1m.index <= mss.origin_ts)]
    extreme = float(manip.low.min()) if long else float(manip.high.max())
    stop = extreme - p.stop_buffer if long else extreme + p.stop_buffer
    if (long and not stop < entry) or (not long and not stop > entry):
        setup.gates.append(Gate("trigger", False, f"stop {stop:.2f} on wrong side of entry {entry:.2f}"))
        return setup

    # gates, in order -------------------------------------------------------------
    w = _window_at(decided, p.windows)
    setup.gates.append(Gate("time", w is not None, w.name if w else f"{decided:%H:%M} outside {p.windows}"))

    want_bias = "bull" if long else "bear"
    setup.gates.append(Gate("bias", (ctx.bias == want_bias) or not p.use_bias, f"daily bias {ctx.bias}"))

    # Intraday pricing is judged on the FINISHED leg: the entry must be in discount (premium) of
    # extreme → leg high. That needs the leg to reach the arm level 2·entry − extreme; the order
    # only goes live once it does (decided now, enforced by the simulator → no look-ahead).
    leg = day_1m[(day_1m.index >= liquidity.origin_ts) & (day_1m.index <= decided)]
    leg_far = float(leg.high.max()) if long else float(leg.low.min())
    arm = 2 * entry - extreme
    armed_now = (leg_far >= arm) if long else (leg_far <= arm)
    htf = ctx.pricing(entry, 20)
    good = "discount" if long else "premium"
    ok_htf = htf.zone == good or not p.use_htf_pricing
    setup.tags.update({"arm": round(arm, 2), "armed_at_decision": armed_now,
                       "htf20_fraction": round(htf.fraction, 3)})
    setup.gates.append(Gate("pricing", ok_htf or not p.use_pricing,
                            f"intraday {good} once leg reaches {arm:.2f}"
                            f"{' (already)' if armed_now else ''}; htf20 {htf.zone} ({htf.fraction:.2f})"))

    poi = _poi(liquidity, long, htf_gaps, day_1m)
    setup.tags["poi"] = poi
    setup.gates.append(Gate("poi", poi is not None or not p.use_poi, poi or "no HTF POI under the sweep"))

    setup.gates.append(Gate("trigger", True, f"{p.entry_tf} displacement FVG {fvg.bottom:.2f}-{fvg.top:.2f}"))

    tp1, tp1_name, final, final_name = _targets(entry, long, ctx, day_1m, decided, swing_pts)
    if tp1 is None:
        setup.gates.append(Gate("target", False, "no untaken liquidity beyond entry"))
        return setup
    potential = abs(final - entry)
    setup.gates.append(Gate("target", potential >= p.min_potential and abs(entry - stop) > 0,
                            f"TP1 {tp1_name} {tp1:.2f}, final {final_name} {final:.2f}, potential {potential:.1f}"))

    expires = _window_end(decided, w) if w else decided
    setup.would_plan = TradePlan(side, decided, expires, entry, stop, tp1, final, tp1_name, final_name,
                                 arm=None if (armed_now or not p.use_pricing) else arm)
    if all(g.passed for g in setup.gates):
        setup.plan = setup.would_plan
    setup.tags["window"] = w.name if w else None
    return setup


def _side_of(e: Event) -> str:
    # sweep: bull = sell-side (a low) was swept; run: bear = a low was run through
    if e.kind == "sweep":
        return "low" if e.direction == "bull" else "high"
    return "low" if e.direction == "bear" else "high"


def _tf_minutes(tf: str) -> int:
    return {"1m": 1, "2m": 2, "3m": 3, "5m": 5, "15m": 15}[tf]


def _poi(liquidity: Event, long: bool, htf_gaps: list[Event], day_1m) -> str | None:
    name = liquidity.meta["level"]
    if name in HTF_LIQUIDITY:
        return f"swept {name}"
    extreme = liquidity.bottom if long else liquidity.top
    t = liquidity.origin_ts
    for g in htf_gaps:
        if g.direction != ("bull" if long else "bear") or g.ts >= t:
            continue
        if g.bottom - 1e-9 <= extreme <= g.top + 1e-9 and gap_lifecycle(g, day_1m, until=t).valid_at(t):
            return f"{g.tf} FVG {g.bottom:.2f}-{g.top:.2f}"
    return None


def _targets(entry, long, ctx: DayContext, day_1m, decided, swing_pts):
    seen = day_1m[day_1m.index <= decided]
    hi_so_far, lo_so_far = float(seen.high.max()), float(seen.low.min())

    def untaken(price):
        return price > hi_so_far if long else price < lo_so_far

    cands = []
    for name in (EXTERNAL_HIGH if long else EXTERNAL_LOW):
        if name in ctx.levels and untaken(ctx.levels[name]) and (ctx.levels[name] > entry if long else ctx.levels[name] < entry):
            cands.append((ctx.levels[name], name, True))
    for s in swing_pts:
        if s.ts > decided:
            continue
        if long and s.kind == "swing_high" and s.top > entry and untaken(s.top):
            cands.append((s.top, f"{s.tf} swing high", False))
        if not long and s.kind == "swing_low" and s.bottom < entry and untaken(s.bottom):
            cands.append((s.bottom, f"{s.tf} swing low", False))
    if not cands:
        return None, "", None, ""
    cands.sort(key=lambda c: abs(c[0] - entry))
    tp1, tp1_name, _ = cands[0]
    ext = [c for c in cands if c[2]]
    final, final_name = (ext[0][0], ext[0][1]) if ext else (tp1, tp1_name)
    if abs(final - entry) < abs(tp1 - entry):
        final, final_name = tp1, tp1_name
    return tp1, tp1_name, final, final_name
