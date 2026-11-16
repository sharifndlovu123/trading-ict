"""ICT Silver Bullet — models.md card #1 (+ ictindex rulings §1, §2, §7, §8).

Mechanical version:
    time        the entry (fill) must happen inside 03:00–04:00, 10:00–11:00 or 14:00–15:00
                (15:00–16:00 optional, ``late_window``). The FVG may form before the hour
                (``strict_fvg_in_hour`` = it must form inside); the order is placed at
                max(FVG known, hour start) and expires at the hour's end. Trade may run past it.
    draw        the draw on liquidity (DOL) is the nearest untaken liquidity in the trade's direction
                known at the decision: PDH/PDL, Asia high/low, PWH/PWL, 5m/15m swing highs/lows.
    setup       displacement → 1m FVG in the direction of the DOL.
    framework   the DOL must offer ≥ ``min_framework_ticks`` (40 ticks = 10 points on NQ/ES) from
                the entry — "best case price delivery", not the target; metals/FX use
                ``framework_adr_frac`` of the 14-day ADR (ICT gives no gold minimum).
    stop        beyond the swing that started the displacement leg.
    TP1         nearest liquidity in the direction ≥ ``min_tp1_r`` (ICT banks early).
    cap         one trade per day (ICT's rule for his son; ruling §1) — ``cap_scope`` is read by
                the runner.
    gates       time → bias → pricing (entry in discount of leg start ↔ DOL) → poi (leg started at a
                HTF array: ran a context level or from a 1h/4h FVG) → trigger → target → risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import DayContext, build_context
from ict_engine.concepts.events import Event, fvgs, gap_lifecycle, swings
from ict_engine.data.instruments import cost_at, get
from ict_engine.models.base import Gate, Setup, TradePlan
from ict_engine.models.model_2022 import _ts, bias_gate

MODEL = "silver_bullet"
NAMES = ("silver_bullet",)
SB_WINDOWS = {"sb_london": (time(3), time(4)), "sb_am": (time(10), time(11)), "sb_pm": (time(14), time(15))}
SB_LATE = {"sb_late": (time(15), time(16))}
LEVELS_UP = ("asia_high", "pdh", "pwh")
LEVELS_DOWN = ("asia_low", "pdl", "pwl")


@dataclass(frozen=True)
class Params:
    late_window: bool = False            # 15:00–16:00 as a 4th window (ruling §2), scored separately
    strict_fvg_in_hour: bool = False     # FVG must form inside the hour (card param)
    fvg_lookback_min: int = 30           # FVG may form up to this long before the hour
    entry_level: str = "proximal"        # proximal | ce | distal
    min_framework_ticks: int = 40        # indices: 10 points NQ/ES (ICT: "10 points or 40 ticks")
    framework_adr_frac: float = 0.2      # metals / FX: share of 14-day ADR (≈ 10 pts / ES ADR)
    min_tp1_r: float = 1.0
    tp1_cap_r: float | None = None
    max_cost_r: float | None = 0.1
    stop_buffer: float = 0.25
    leg_lookback_min: int = 30           # displacement leg start searched this far before the FVG
    use_bias: bool = True
    # prev_day_dol: best bias rule in all 3 models OOS (variant sweep 2026-11-13, 4 assets; z < 2 — best so far)
    bias_rule: str = "prev_day_dol"
    neutral_bias: str = "opening_range"
    use_pricing: bool = True
    use_poi: bool = True                 # CLAUDE.md: a FVG outside a POI never opens a trade
    poi_tfs: tuple[str, ...] = ("1h", "4h")
    cap_scope: str = "day"               # one Silver Bullet trade per day (ruling §1)
    invalidate_tf: str | None = None     # exit on a close of this TF beyond the FVG's far edge; None = off
    # scheduled news (ict_engine/news): (minutes before, after) a high-impact release with no new
    # entries; FOMC day rule trade | after_statement | skip. Off until a sweep supports them.
    news_blackout: tuple[int, int] | None = None
    # no new setup when the last hour's range is under this × normal for the time of day (concepts.activity); None = off
    min_activity: float | None = None
    entry_gate: str | None = None        # entry_quality.GATES (entry-quality pre-registration)
    fomc_day: str = "trade"
    partial_frac: float = 0.5            # share closed at TP1 (runner_r); ICT live: 75–80%
    runner_stop: str = "entry"           # runner stop after TP1: entry | lock_half | original
    tags: dict = field(default_factory=dict, compare=False)

    @property
    def windows(self) -> dict[str, tuple[time, time]]:
        return {**SB_WINDOWS, **(SB_LATE if self.late_window else {})}

    @property
    def variant(self) -> str:
        d = Params()
        parts = ["sb", self.entry_level]
        for name in ("late_window", "strict_fvg_in_hour", "min_framework_ticks", "framework_adr_frac", "min_tp1_r",
                     "tp1_cap_r", "max_cost_r", "use_bias", "use_pricing", "use_poi", "bias_rule", "cap_scope", "invalidate_tf", "news_blackout", "fomc_day", "partial_frac", "runner_stop", "entry_gate", "min_activity"):
            if getattr(self, name) != getattr(d, name):
                parts.append(f"{name}={getattr(self, name)}")
        return "-".join(parts)


def _at(d: date, t: time) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d, t), tz="America/New_York")


def min_framework(asset: str, bars_1m: pd.DataFrame, day: date, p: Params) -> float:
    """Minimum distance entry → DOL, in price units."""
    a = get(asset)
    if a.clock == "futures":
        return p.min_framework_ticks * a.tick
    daily = resample(bars_1m[bars_1m.index < _ts(day, time(0))], "1d").tail(14)
    adr = float((daily.high - daily.low).mean()) if len(daily) else 0.0
    return p.framework_adr_frac * adr


def draw_on_liquidity(long: bool, entry: float, ctx: DayContext, swing_pts: list[Event], day_1m: pd.DataFrame,
                      decided: pd.Timestamp) -> list[tuple[float, str, bool]]:
    """Untaken liquidity beyond ``entry`` in the trade direction, nearest first:
    (price, name, external) — external = a context level (Asia / previous day / previous week)."""
    seen = day_1m[day_1m.index <= decided]

    def untaken(price, since=None):
        after = seen if since is None else seen[seen.index > since]
        return after.empty or (price > after.high.max() if long else price < after.low.min())

    out = []
    for n in (LEVELS_UP if long else LEVELS_DOWN):
        v = ctx.levels.get(n)
        if v is not None and (v > entry if long else v < entry) and untaken(v):
            out.append((v, n, True))
    kind = "swing_high" if long else "swing_low"
    for s in swing_pts:
        if s.kind != kind or s.ts > decided:
            continue
        v = s.top if long else s.bottom
        if (v > entry if long else v < entry) and untaken(v, s.ts):
            out.append((v, f"{s.tf} swing {'high' if long else 'low'}", False))
    return sorted(out, key=lambda x: abs(x[0] - entry))


def find_setups(bars_1m: pd.DataFrame, day: date, asset: str, p: Params = Params(),
                ctx: DayContext | None = None) -> list[Setup]:
    ctx = ctx or build_context(bars_1m, day)
    d0, d1 = _ts(day, time(0)), _ts(day, time(16, 30))
    day_1m = bars_1m[(bars_1m.index >= d0) & (bars_1m.index < d1)].assign(close_ts=lambda x: x.index)
    if day_1m.empty:
        return []
    gaps = [g for g in fvgs(day_1m, "1m") if g.meta.get("displacement")]
    swing_pts = swings(resample(day_1m.drop(columns="close_ts"), "5m"), "5m") + \
        swings(resample(day_1m.drop(columns="close_ts"), "15m"), "15m")
    hist = bars_1m[(bars_1m.index >= d0 - timedelta(days=10)) & (bars_1m.index < d1)]
    htf_gaps = [g for tf in p.poi_tfs for g in fvgs(resample(hist, tf), tf)]
    frame_min = min_framework(asset, bars_1m, day, p)
    out = []
    for wname, (w0, w1) in p.windows.items():
        start, end = _at(day, w0), _at(day, w1)
        earliest = start if p.strict_fvg_in_hour else start - pd.Timedelta(minutes=p.fvg_lookback_min)
        for g in gaps:
            if earliest <= g.origin_ts and g.ts < end:
                out.append(_evaluate(g, wname, start, end, ctx, day, asset, p, day_1m, swing_pts, htf_gaps, frame_min))
    return out


def _evaluate(fvg: Event, wname, start, end, ctx, day, asset, p: Params, day_1m, swing_pts, htf_gaps, frame_min) -> Setup:
    long = fvg.direction == "bull"
    side = "long" if long else "short"
    decided = max(fvg.ts, start)
    setup = Setup(MODEL, p.variant, asset, "day", day, side, decided, {"fvg": fvg}, pd_array="fvg", pd_array_tf="1m")
    setup.tags["window"] = wname
    if not gap_lifecycle(fvg, day_1m, until=decided).valid_at(decided):
        setup.gates.append(Gate("trigger", False, "FVG already invalidated before the hour"))
        return setup
    entry = {"proximal": fvg.top if long else fvg.bottom, "ce": fvg.ce,
             "distal": fvg.bottom if long else fvg.top}[p.entry_level]

    # displacement leg start: extreme of the bars from leg_lookback before the FVG to its first candle
    leg = day_1m[(day_1m.index >= fvg.origin_ts - pd.Timedelta(minutes=p.leg_lookback_min))
                 & (day_1m.index <= fvg.origin_ts)]
    anchor_ts = leg.low.idxmin() if long else leg.high.idxmax()
    anchor = float(leg.low.min()) if long else float(leg.high.max())
    stop = anchor - p.stop_buffer if long else anchor + p.stop_buffer
    if (long and not stop < entry) or (not long and not stop > entry):
        setup.gates.append(Gate("trigger", False, f"stop {stop:.2f} on wrong side of entry {entry:.2f}"))
        return setup
    risk = abs(entry - stop)
    setup.evidence["liquidity"] = Event("sweep", "1m", fvg.direction, anchor_ts, anchor_ts, anchor, anchor,
                                        {"level": "leg start"})

    dol = draw_on_liquidity(long, entry, ctx, swing_pts, day_1m, decided)
    setup.tags["dol"] = dol[0][1] if dol else None

    # gates ------------------------------------------------------------------------
    setup.gates.append(Gate("time", True, f"{wname}: order {decided:%H:%M}–{end:%H:%M}"))
    setup.gates.append(bias_gate(ctx, long, decided, day_1m, p))
    ext = [d for d in dol if d[2]]
    draw = ext[0] if ext else (dol[-1] if dol else None)      # the draw: nearest external level, else furthest swing
    far = draw[0] if draw else None
    if dol:
        eq = (anchor + dol[0][0]) / 2
        ok = entry <= eq if long else entry >= eq
        setup.gates.append(Gate("pricing", ok or not p.use_pricing,
                                f"entry {entry:.2f} vs leg-start↔DOL equilibrium {eq:.2f}"))
    else:
        setup.gates.append(Gate("pricing", not p.use_pricing, "no draw on liquidity"))
    poi = _poi(long, anchor, anchor_ts, leg.index[0], ctx, htf_gaps, day_1m)
    setup.tags["poi"] = poi
    setup.gates.append(Gate("poi", poi is not None or not p.use_poi, poi or "leg did not start at a HTF array"))
    setup.gates.append(Gate("trigger", True, f"1m displacement FVG {fvg.bottom:.2f}-{fvg.top:.2f}"))

    reach = entry + (1 if long else -1) * p.min_tp1_r * risk
    tp1 = next(((v, n) for v, n, _ in dol if (v >= reach if long else v <= reach)), None)
    offered = abs(far - entry) if far is not None else 0.0
    if tp1 is None or offered < frame_min:
        setup.gates.append(Gate("target", False, f"draw offers {offered:.2f} (min framework {frame_min:.2f})"
                                                 f"{'' if tp1 else '; no liquidity ≥ min TP1 distance'}"))
        return setup
    tp1_px, tp1_name = tp1
    if p.tp1_cap_r is not None and abs(tp1_px - entry) > p.tp1_cap_r * risk:
        tp1_px, tp1_name = entry + (1 if long else -1) * p.tp1_cap_r * risk, f"cap {p.tp1_cap_r:g}R"
    setup.gates.append(Gate("target", True, f"TP1 {tp1_name} {tp1_px:.2f}; draw offers {offered:.2f} ≥ {frame_min:.2f}"))
    if p.max_cost_r is not None:
        cost_r = cost_at(asset, entry, decided) / risk
        setup.gates.append(Gate("risk", cost_r <= p.max_cost_r, f"cost {cost_r:.2f}R (max {p.max_cost_r:g}R)"))

    final = far if (far - tp1_px) * (1 if long else -1) >= 0 else tp1_px
    setup.would_plan = TradePlan(side, decided, end, entry, stop, tp1_px, final, tp1_name, draw[1],
                                 invalid_level=fvg.bottom if long else fvg.top, invalid_tf=p.invalidate_tf)
    if all(g.passed for g in setup.gates):
        setup.plan = setup.would_plan
    return setup


def _poi(long, anchor, anchor_ts, leg_start, ctx: DayContext, htf_gaps, day_1m) -> str | None:
    """The displacement leg started at a HTF array: its extreme ran a context level still untaken when
    the leg began (the run into the extreme passes it first), or sits in a valid same-direction 1h/4h FVG."""
    for n in (LEVELS_DOWN if long else LEVELS_UP):
        v = ctx.levels.get(n)
        if v is not None and (anchor < v if long else anchor > v):
            before = day_1m[day_1m.index < leg_start]
            fresh = before.empty or (before.low.min() > v if long else before.high.max() < v)
            if fresh:
                return f"leg ran {n}"
    for g in htf_gaps:
        if g.direction != ("bull" if long else "bear") or g.ts >= anchor_ts:
            continue
        if g.bottom - 1e-9 <= anchor <= g.top + 1e-9 and gap_lifecycle(g, day_1m, until=anchor_ts).valid_at(anchor_ts):
            return f"{g.tf} FVG {g.bottom:.2f}-{g.top:.2f}"
    return None
