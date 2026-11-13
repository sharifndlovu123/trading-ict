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
from ict_engine.data.instruments import COST
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
    # ICT runs the 2022 model 07:00–09:00 ("NY Open Kill Zone") and enters in the macros
    # (ictindex: 2023 MMxM; Oct 28 2024; 9:50/10:50 macros) — see ictindex-rulings.
    windows: tuple[str, ...] = ("london_kz", "ny_premarket", "ny_am_kz", "macro_0950", "macro_1050", "ny_pm_kz")
    sweep_lookback_min: int = 90         # liquidity must be taken within this many minutes before the MSS
    leg_bars_after_mss: int = 3          # FVG may finish forming up to N bars after the MSS candle
    fvg_pick: str = "deepest"            # deepest (lowest for buys) | nearest (closest to the MSS)
    entry_level: str = "proximal"        # proximal | ce | distal
    use_bias: bool = True
    # prev_day_dol: best bias rule in all 3 models OOS (variant sweep 2026-11-13, 4 assets; z < 2 — best so far)
    bias_rule: str = "prev_day_dol"
    neutral_bias: str = "opening_range"  # neutral day: block | opening_range (ICT: wait for the 09:30–10:00 move)
    use_pricing: bool = True
    # 20/40/60-day ranges are ICT's swing/daily-setup ranges (Charter PA Model 6); intraday he
    # measures the most recent large move (Lecture #4, 8 Aug 2024) = our leg/arm check. Off for day trades.
    use_htf_pricing: bool = False
    use_poi: bool = True
    min_potential: float = 10.0          # handles from entry to final target (ICT minimum framework)
    stop_buffer: float = 0.25
    # TP1 (earliest close), framework §0: day trade = opposite side of the day/session; 1m swings are
    # too fine. Swings of these TFs + context levels are candidates; TP1 at least min_tp1_r from entry.
    tp1_swing_tfs: tuple[str, ...] = ("5m",)
    min_tp1_r: float = 1.0
    # Both validated out-of-sample (2024 hold-out AND unseen 2022 bear year; reports/variants-*):
    tp1_cap_r: float | None = 2.0        # TP1 no further than this many R (ICT's earliest close is near); None = off
    max_cost_r: float | None = 0.1       # reject when round-trip cost / risk exceeds this; None = off
    poi_tfs: tuple[str, ...] = ("1h", "4h")
    # exit when a candle of this TF closes beyond the entry FVG's far edge (the retest failed); None = off
    invalidate_tf: str | None = None
    # scheduled news (ict_engine/news): (minutes before, after) a high-impact release with no new
    # entries; FOMC day rule trade | after_statement | skip. Off until a sweep supports them.
    news_blackout: tuple[int, int] | None = None
    fomc_day: str = "trade"
    tags: dict = field(default_factory=dict, compare=False)

    @property
    def variant(self) -> str:
        off = [n for n, on in (("bias", self.use_bias), ("pricing", self.use_pricing),
                               ("poi", self.use_poi)) if not on]
        extra = ["htf20"] if self.use_htf_pricing else []
        if (self.tp1_swing_tfs, self.min_tp1_r) != (("5m",), 1.0):
            extra.append(f"tp1_{'+'.join(self.tp1_swing_tfs)}_{self.min_tp1_r:g}R")
        if self.tp1_cap_r != 2.0:
            extra.append(f"tp1cap{self.tp1_cap_r:g}R" if self.tp1_cap_r is not None else "tp1uncapped")
        if self.max_cost_r != 0.1:
            extra.append(f"cost<={self.max_cost_r:g}R" if self.max_cost_r is not None else "nocostgate")
        if self.use_bias and (self.bias_rule, self.neutral_bias) != ("prev_day_dol", "opening_range"):
            extra.append(f"bias_{self.bias_rule}_{self.neutral_bias}")
        if self.invalidate_tf:
            extra.append(f"inval{self.invalidate_tf}")
        if self.news_blackout:
            extra.append(f"newsblackout{self.news_blackout[0]}-{self.news_blackout[1]}")
        if self.fomc_day != "trade":
            extra.append(f"fomc_{self.fomc_day}")
        win = "+".join(w.replace("_kz", "").replace("macro_", "m") for w in self.windows)
        base = f"{self.entry_tf}-{self.entry_level}-{self.fvg_pick}-[{win}]"
        return base + ("-no_" + "_".join(off) if off else "") + "".join(f"-{e}" for e in extra)


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

    setup.gates.append(bias_gate(ctx, long, decided, day_1m, p))

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

    needs_arm = not (armed_now or not p.use_pricing)
    tp1, tp1_name, final, final_name = _targets(entry, long, ctx, day_1m, decided,
                                                [x for x in swing_pts if x.tf in p.tp1_swing_tfs],
                                                beyond=arm if needs_arm else None,
                                                min_dist=p.min_tp1_r * abs(entry - stop))
    if tp1 is None:
        setup.gates.append(Gate("target", False, "no untaken liquidity beyond entry"))
        return setup
    risk = abs(entry - stop)
    if p.tp1_cap_r is not None and abs(tp1 - entry) > p.tp1_cap_r * risk:
        capped = entry + p.tp1_cap_r * risk if long else entry - p.tp1_cap_r * risk
        if needs_arm and (capped <= arm if long else capped >= arm):
            setup.gates.append(Gate("target", False, f"TP1 cap {p.tp1_cap_r:g}R {capped:.2f} not beyond arm {arm:.2f}"))
            return setup
        tp1, tp1_name = capped, f"cap {p.tp1_cap_r:g}R"
    potential = abs(final - entry)
    setup.gates.append(Gate("target", potential >= p.min_potential and abs(entry - stop) > 0,
                            f"TP1 {tp1_name} {tp1:.2f}, final {final_name} {final:.2f}, potential {potential:.1f}"))

    if p.max_cost_r is not None:
        cost_r = COST.get(asset, 0.0) / risk if risk else float("inf")
        setup.gates.append(Gate("risk", cost_r <= p.max_cost_r,
                                f"cost {COST.get(asset, 0.0):g} = {cost_r:.2f}R of a {risk:.2f} stop (max {p.max_cost_r:g}R)"))

    expires = _window_end(decided, w) if w else decided
    setup.would_plan = TradePlan(side, decided, expires, entry, stop, tp1, final, tp1_name, final_name,
                                 arm=arm if needs_arm else None,
                                 invalid_level=fvg.bottom if long else fvg.top, invalid_tf=p.invalidate_tf)
    if all(g.passed for g in setup.gates):
        setup.plan = setup.would_plan
    setup.tags["window"] = w.name if w else None
    return setup


OPEN_RANGE = (time(9, 30), time(10, 0))


def opening_range_bias(day_1m: pd.DataFrame, decided: pd.Timestamp) -> str | None:
    """Direction of the 09:30–10:00 move (10:00 close vs 09:30 open), or None before 10:00 —
    ICT on unclear days: "wait that first 30 minutes and see what they do" (Twitter Space 11 Jan 2023)."""
    d = decided.date()
    t0, t1 = _ts(d, OPEN_RANGE[0]), _ts(d, OPEN_RANGE[1])
    if decided < t1:
        return None
    rng = day_1m[(day_1m.index >= t0) & (day_1m.index < t1)]
    if rng.empty:
        return None
    return "bull" if rng.close.iloc[-1] > rng.open.iloc[0] else "bear"


def bias_gate(ctx: DayContext, long: bool, decided: pd.Timestamp, day_1m: pd.DataFrame, p: Params) -> Gate:
    want = "bull" if long else "bear"
    if p.bias_rule == "prev_day":
        bias, why = ctx.bias, ctx.bias_reason
    else:
        bias, why = getattr(ctx, "biases", {})[p.bias_rule]
    if not p.use_bias:
        return Gate("bias", True, f"off (daily {bias})")
    if bias != "neutral" or p.neutral_bias == "block":
        return Gate("bias", bias == want, f"daily bias {bias} [{p.bias_rule}]: {why}")
    orb = opening_range_bias(day_1m, decided)
    if orb is None:
        return Gate("bias", False, f"daily bias neutral [{p.bias_rule}]; waiting for the 09:30–10:00 move")
    return Gate("bias", orb == want, f"daily bias neutral [{p.bias_rule}]; opening range {orb}")


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


def _targets(entry, long, ctx: DayContext, day_1m, decided, swing_pts, beyond: float | None = None,
             min_dist: float = 0.0):
    """TP1 = nearest untaken level past ``beyond`` (the arm level when the order must arm first —
    anything between entry and arm is taken before we can fill; else the entry)."""
    seen = day_1m[day_1m.index <= decided]
    edge = entry if beyond is None else (max(entry, beyond) if long else min(entry, beyond))
    reach = entry + min_dist if long else entry - min_dist
    edge = max(edge, reach) if long else min(edge, reach)

    def untaken(price, since=None):
        """Not traded through between ``since`` (a swing's confirmation time — its own bar may
        print the high; day start for context levels) and the decision. A swing below the day's high can still be untaken."""
        after = seen if since is None else seen[seen.index > since]
        if after.empty:
            return True
        return price > float(after.high.max()) if long else price < float(after.low.min())

    cands = []
    for name in (EXTERNAL_HIGH if long else EXTERNAL_LOW):
        if name in ctx.levels and untaken(ctx.levels[name]) and (ctx.levels[name] > edge if long else ctx.levels[name] < edge):
            cands.append((ctx.levels[name], name, True))
    for s in swing_pts:
        if s.ts > decided:
            continue
        if long and s.kind == "swing_high" and s.top > edge and untaken(s.top, s.ts):
            cands.append((s.top, f"{s.tf} swing high", False))
        if not long and s.kind == "swing_low" and s.bottom < edge and untaken(s.bottom, s.ts):
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
