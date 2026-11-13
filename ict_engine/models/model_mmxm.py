"""ICT Market Maker Buy / Sell Model (MMBM / MMSM) — models.md card #3.

Mechanical version (buy model; the sell model is the mirror):

    1 original consolidation (OC)  ``oc_bars`` framing-TF bars whose total range is at most
                                   ``oc_range_mult`` × the median framing bar range — a tight range
                                   that engineers buy-side liquidity above it. Its high = terminus.
    2 sell-side curve              price leaves the OC downward, never trades back above the OC
                                   high, and steps lower: at least ``min_steps`` framing swing
                                   highs below the OC low (redistribution — later internal targets).
    3 smart money reversal (SMR)   the curve's low (reversal low) is put in at a HTF discount array
                                   (runs PDL / Asia low / PWL, or trades into a valid 1h/4h bullish
                                   FVG) AND purges liquidity: it runs a context level or a framing
                                   swing low on the curve (ICT: "always a purge on liquidity").
    4 market structure shift       bullish MSS on the entry TF within ``mss_within_min`` of the low.
    5 entry                        stage 1: first displacement FVG in the leg off the low;
                                   stage 2: first displacement FVG after price closes back above
                                   the lowest redistribution high ("directly across" from it).
    → gates   time → bias → pricing (entry in discount of OC high ↔ reversal low) → poi (SMR array)
              → trigger → target → risk (cost)
    → plan    limit at the FVG proximal; stop beyond the reversal low; TP1 = nearest untaken
              redistribution high (≥ ``min_tp1_r``, optionally capped); final = OC high.

Look-ahead free: the OC, curve and steps use only framing bars closed by the reversal
low's time; everything else is checked at the decision time (MSS or FVG known).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta

import numpy as np
import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import DayContext, build_context
from ict_engine.concepts.events import Event, fvgs, gap_lifecycle, structure, swings
from ict_engine.data.instruments import COST
from ict_engine.models.base import Gate, Setup, TradePlan
from ict_engine.models.model_2022 import _tf_minutes, _ts, _window_at, _window_end, bias_gate

MODEL = "mmxm"
NAMES = ("mmbm", "mmsm")                 # Setup.model / reference-case labels
SMR_LEVELS_LOW = ("pdl", "asia_low", "pwl")
SMR_LEVELS_HIGH = ("pdh", "asia_high", "pwh")


@dataclass(frozen=True)
class Params:
    frame_tf: str = "15m"                # bellwether / framing chart (MMxM PDF p. 4)
    entry_tf: str = "1m"
    windows: tuple[str, ...] = ("london_kz", "ny_premarket", "ny_am_kz", "macro_0950", "macro_1050", "ny_pm_kz")
    oc_bars: int = 4                     # original consolidation length in framing bars (15m → 1h)
    oc_range_mult: float = 2.5           # OC range ≤ mult × median framing-bar range
    curve_max_h: float = 12.0            # OC end → reversal low at most this many hours
    min_steps: int = 1                   # redistribution swing highs on the curve
    low_lookback_min: int = 120          # reversal low searched this far before the MSS
    leg_bars_after_mss: int = 3
    stage: int = 1                       # 1 | 2
    fvg_pick: str = "first"              # first (ICT: "the very 1st bullish FVG that forms") | deepest
    smr_purge: bool = True               # ICT: "smart money reversal will always be a purge on liquidity"
    entry_level: str = "proximal"
    use_bias: bool = True
    bias_rule: str = "prev_day"
    neutral_bias: str = "opening_range"
    use_pricing: bool = True
    use_poi: bool = True
    stop_buffer: float = 0.25
    min_tp1_r: float = 1.0
    tp1_cap_r: float | None = None
    max_cost_r: float | None = 0.1
    poi_tfs: tuple[str, ...] = ("1h", "4h")
    tags: dict = field(default_factory=dict, compare=False)

    @property
    def variant(self) -> str:
        d = Params()
        parts = [f"{self.frame_tf}>{self.entry_tf}", f"stage{self.stage}",
                 "+".join(w.replace("_kz", "").replace("macro_", "m") for w in self.windows)]
        for name in ("oc_bars", "oc_range_mult", "min_steps", "tp1_cap_r", "max_cost_r", "use_bias",
                     "use_pricing", "use_poi", "bias_rule", "fvg_pick", "smr_purge"):
            if getattr(self, name) != getattr(d, name):
                parts.append(f"{name}={getattr(self, name)}")
        return "-".join(parts)


# --- curve detection (pure functions, unit-tested) ------------------------------

@dataclass(frozen=True)
class Curve:
    oc_start: pd.Timestamp
    oc_end: pd.Timestamp                 # close time of the last OC bar
    oc_high: float
    oc_low: float
    steps: tuple[float, ...]             # redistribution levels, in time order (stepping toward the low)
    step_times: tuple[pd.Timestamp, ...]  # confirmation times (the swing bar itself prints the level)


def find_curve(frame: pd.DataFrame, frame_sw: list[Event], long: bool, low_ts: pd.Timestamp, low: float,
               p: Params) -> Curve | None:
    """Latest original consolidation whose curve runs into the reversal ``low`` at ``low_ts``.
    For a sell model pass ``long=False`` and the reversal *high* as ``low``."""
    known = frame[frame["close_ts"] <= low_ts]
    if len(known) < p.oc_bars + 2:
        return None
    rng = (known.high - known.low).to_numpy()
    hi, lo = known.high.to_numpy(), known.low.to_numpy()
    cl, cts = known.close.to_numpy(), known["close_ts"].to_numpy()
    earliest = low_ts - pd.Timedelta(hours=p.curve_max_h)
    for e in range(len(known) - 2, p.oc_bars - 2, -1):           # latest OC first; ≥1 bar after it
        s = e - p.oc_bars + 1
        if s < 0 or pd.Timestamp(cts[e]) < earliest:
            break
        med = float(np.median(rng[max(0, s - 20):s])) if s >= 5 else float(np.median(rng[: e + 1]))
        oc_hi, oc_lo = float(hi[s:e + 1].max()), float(lo[s:e + 1].min())
        width = oc_hi - oc_lo
        if med <= 0 or width > p.oc_range_mult * med:
            continue
        after = slice(e + 1, len(known))
        if long:
            if not (low <= oc_lo - width) or hi[after].max(initial=-np.inf) > oc_hi:
                continue
            if not (cl[after] < oc_lo).any():                     # left the OC downward
                continue
        else:
            if not (low >= oc_hi + width) or lo[after].min(initial=np.inf) < oc_lo:
                continue
            if not (cl[after] > oc_hi).any():
                continue
        t_end = pd.Timestamp(cts[e])
        kind = "swing_high" if long else "swing_low"
        st = sorted((x for x in frame_sw if x.kind == kind and t_end < x.origin_ts and x.ts <= low_ts
                     and (x.top < oc_lo if long else x.bottom > oc_hi)), key=lambda x: x.origin_ts)
        if len(st) < p.min_steps:
            continue
        return Curve(pd.Timestamp(known.index[s]), t_end, oc_hi, oc_lo,
                     tuple(x.top if long else x.bottom for x in st), tuple(x.ts for x in st))
    return None


def smr_array(ctx: DayContext, long: bool, low: float, low_ts: pd.Timestamp, curve: Curve,
              htf_gaps: list[Event], bars_1m: pd.DataFrame) -> str | None:
    """HTF array the reversal was made at: a context level run on the curve, or a 1h/4h FVG."""
    names = SMR_LEVELS_LOW if long else SMR_LEVELS_HIGH
    for n in names:
        lvl = ctx.levels.get(n)
        if lvl is None:
            continue
        if long and low < lvl < curve.oc_low or not long and curve.oc_high < lvl < low:
            return f"ran {n}"
    for g in htf_gaps:
        if g.direction != ("bull" if long else "bear") or g.ts >= low_ts:
            continue
        if g.bottom - 1e-9 <= low <= g.top + 1e-9 and gap_lifecycle(g, bars_1m, until=low_ts).valid_at(low_ts):
            return f"{g.tf} FVG {g.bottom:.2f}-{g.top:.2f}"
    return None


def smr_purge(ctx: DayContext, frame_sw: list[Event], long: bool, low: float, low_ts: pd.Timestamp,
              curve: Curve) -> str | None:
    """The reversal must run liquidity (turtle soup): trade through a context level or a framing
    swing low confirmed on the curve before the reversal."""
    for n in (SMR_LEVELS_LOW if long else SMR_LEVELS_HIGH):
        lvl = ctx.levels.get(n)
        if lvl is not None and (low < lvl if long else low > lvl) and (lvl < curve.oc_low if long else lvl > curve.oc_high):
            return f"ran {n}"
    kind = "swing_low" if long else "swing_high"
    for x in sorted(frame_sw, key=lambda e: -e.origin_ts.value):
        if x.kind != kind or x.ts > low_ts or x.origin_ts <= curve.oc_end:
            continue
        if (low < x.bottom) if long else (low > x.top):
            return f"ran {x.tf} swing {'low' if long else 'high'} {x.bottom if long else x.top:.2f}"
    return None


# --- model ------------------------------------------------------------------------

def find_setups(bars_1m: pd.DataFrame, day: date, asset: str, p: Params = Params(),
                ctx: DayContext | None = None) -> list[Setup]:
    ctx = ctx or build_context(bars_1m, day)
    d0, d1 = _ts(day, time(0)), _ts(day, time(16))
    curve_from = _ts(day - timedelta(days=1), time(18)) - pd.Timedelta(hours=p.curve_max_h)
    span = bars_1m[(bars_1m.index >= curve_from) & (bars_1m.index < d1)]
    day_1m = span[span.index >= d0].assign(close_ts=lambda x: x.index)
    if day_1m.empty:
        return []
    frame = resample(span, p.frame_tf)
    frame_sw = swings(frame, p.frame_tf)
    etf = day_1m if p.entry_tf == "1m" else resample(day_1m.drop(columns="close_ts"), p.entry_tf)
    sw = swings(etf, p.entry_tf)
    shifts = [e for e in structure(etf, p.entry_tf, sw) if e.kind == "mss"]
    gaps = [g for g in fvgs(etf, p.entry_tf) if g.meta.get("displacement")]
    hist = bars_1m[(bars_1m.index >= d0 - timedelta(days=10)) & (bars_1m.index < d1)]
    htf_gaps = [g for tf in p.poi_tfs for g in fvgs(resample(hist, tf), tf)]
    span_1m = span.assign(close_ts=lambda x: x.index)
    return [_evaluate(m, ctx, day, asset, p, day_1m, span_1m, frame, frame_sw, gaps, htf_gaps) for m in shifts]


def _evaluate(mss: Event, ctx, day, asset, p: Params, day_1m, span_1m, frame, frame_sw, gaps, htf_gaps) -> Setup:
    long = mss.direction == "bull"
    side = "long" if long else "short"
    setup = Setup(NAMES[0] if long else NAMES[1], p.variant, asset, "day", day, side, mss.ts, {"shift": mss},
                  pd_array="fvg", pd_array_tf=p.entry_tf)
    setup.tags["stage"] = p.stage

    # reversal extreme before the shift
    pre = span_1m[(span_1m.index >= mss.origin_ts - pd.Timedelta(minutes=p.low_lookback_min))
                  & (span_1m.index <= mss.origin_ts)]
    if pre.empty:
        setup.gates.append(Gate("trigger", False, "no bars before the MSS"))
        return setup
    low_ts = pre.low.idxmin() if long else pre.high.idxmax()
    low = float(pre.low.min()) if long else float(pre.high.max())

    curve = find_curve(frame, frame_sw, long, low_ts, low, p)
    if curve is None:
        setup.gates.append(Gate("trigger", False, f"no original consolidation + curve into the {'low' if long else 'high'}"))
        return setup
    setup.tags.update({"oc_high": curve.oc_high, "oc_low": curve.oc_low, "oc_start": str(curve.oc_start),
                       "steps": list(curve.steps), "reversal": low, "reversal_at": str(low_ts)})
    setup.evidence["liquidity"] = Event("sweep", "1m", "bull" if long else "bear", low_ts, low_ts, low, low,
                                        {"level": "reversal"})

    # entry FVG
    want = "bull" if long else "bear"
    if p.stage == 1:
        leg_end = mss.origin_ts + timedelta(minutes=p.leg_bars_after_mss * _tf_minutes(p.entry_tf))
        cands = [g for g in gaps if g.direction == want and low_ts < g.origin_ts <= leg_end]
        if not cands:
            fvg = None
        elif p.fvg_pick == "first":
            fvg = min(cands, key=lambda g: g.origin_ts)
        else:
            fvg = min(cands, key=lambda g: g.bottom) if long else max(cands, key=lambda g: g.top)
    else:
        level = curve.steps[-1]                                   # lowest redistribution high
        after = day_1m[day_1m.index > low_ts]
        back = after.index[after.close > level] if long else after.index[after.close < level]
        fvg = None
        if len(back):
            cands = [g for g in gaps if g.direction == want and g.origin_ts >= back[0]]
            fvg = min(cands, key=lambda g: g.origin_ts) if cands else None
    if fvg is None:
        setup.gates.append(Gate("trigger", False, f"no stage-{p.stage} displacement FVG"))
        return setup
    decided = max(mss.ts, fvg.ts)
    setup.decided_at = decided
    if not gap_lifecycle(fvg, day_1m, until=decided).valid_at(decided):
        setup.gates.append(Gate("trigger", False, "FVG already invalidated at decision time"))
        return setup
    setup.evidence["fvg"] = fvg
    entry = {"proximal": fvg.top if long else fvg.bottom, "ce": fvg.ce,
             "distal": fvg.bottom if long else fvg.top}[p.entry_level]
    stop = low - p.stop_buffer if long else low + p.stop_buffer
    if (long and not stop < entry) or (not long and not stop > entry):
        setup.gates.append(Gate("trigger", False, f"stop {stop:.2f} on wrong side of entry {entry:.2f}"))
        return setup
    risk = abs(entry - stop)

    # gates ---------------------------------------------------------------------------
    w = _window_at(decided, p.windows)
    setup.tags["window"] = w.name if w else None
    setup.gates.append(Gate("time", w is not None, w.name if w else f"{decided:%H:%M} outside {p.windows}"))
    setup.gates.append(bias_gate(ctx, long, decided, day_1m, p))
    eq = (curve.oc_high + low) / 2 if long else (curve.oc_low + low) / 2
    in_zone = entry <= eq if long else entry >= eq
    setup.gates.append(Gate("pricing", in_zone or not p.use_pricing,
                            f"entry {entry:.2f} vs curve equilibrium {eq:.2f} ({'discount' if long else 'premium'} wanted)"))
    poi = smr_array(ctx, long, low, low_ts, curve, htf_gaps, span_1m)
    purge = smr_purge(ctx, frame_sw, long, low, low_ts, curve) if p.smr_purge else "not required"
    setup.tags.update({"poi": poi, "purge": purge})
    ok = (poi is not None and purge is not None) or not p.use_poi
    setup.gates.append(Gate("poi", ok, f"{poi or 'reversal not at a HTF array'}; purge: {purge or 'none — no liquidity run at the low'}"))
    setup.gates.append(Gate("trigger", True, f"stage {p.stage}: {p.entry_tf} FVG {fvg.bottom:.2f}-{fvg.top:.2f}"))

    tp1, tp1_name = _tp1(entry, risk, long, curve, day_1m, decided, p)
    final = curve.oc_high if long else curve.oc_low
    if tp1 is None or (final - entry) * (1 if long else -1) <= 0:
        setup.gates.append(Gate("target", False, "no untaken curve level beyond the minimum TP1 distance"))
        return setup
    setup.gates.append(Gate("target", True, f"TP1 {tp1_name} {tp1:.2f}, terminus {final:.2f}"))
    if p.max_cost_r is not None:
        cost_r = COST.get(asset, 0.0) / risk
        setup.gates.append(Gate("risk", cost_r <= p.max_cost_r, f"cost {cost_r:.2f}R (max {p.max_cost_r:g}R)"))

    expires = _window_end(decided, w) if w else decided
    setup.would_plan = TradePlan(side, decided, expires, entry, stop, tp1, final, tp1_name,
                                 "oc high" if long else "oc low")
    if all(g.passed for g in setup.gates):
        setup.plan = setup.would_plan
    return setup


def _tp1(entry, risk, long, curve: Curve, day_1m, decided, p: Params):
    """Nearest curve level (redistribution steps, OC low/high) at least min_tp1_r away and untaken
    since it formed; capped at tp1_cap_r when set."""
    sign = 1 if long else -1
    reach = entry + sign * p.min_tp1_r * risk
    seen = day_1m[day_1m.index <= decided]
    cands = [(lvl, f"step {i + 1}", t) for i, (lvl, t) in enumerate(zip(curve.steps, curve.step_times))]
    cands += [(curve.oc_low if long else curve.oc_high, "oc low" if long else "oc high", curve.oc_end),
              (curve.oc_high if long else curve.oc_low, "oc high" if long else "oc low", curve.oc_end)]
    ok = []
    for lvl, name, t in cands:
        if (lvl - reach) * sign < 0:
            continue
        after = seen[seen.index > t]
        taken = (after.high.max() >= lvl) if long else (after.low.min() <= lvl)
        if after.empty or not taken:
            ok.append((lvl, name))
    if not ok:
        return None, ""
    lvl, name = min(ok, key=lambda c: abs(c[0] - entry))
    if p.tp1_cap_r is not None and abs(lvl - entry) > p.tp1_cap_r * risk:
        return entry + sign * p.tp1_cap_r * risk, f"cap {p.tp1_cap_r:g}R"
    return lvl, name
