"""PD array return — ICT's live-execution form (tests/cases/ict_live_exec.yaml: 6 of 14 cases).

ICT: "the higher time frame PD arrays will draw price… the intraday lower time frame PD arrays will provide the
timing and/or price levels to enter on" (framework.md §5). In his six live examples the array is always FVG-family
(BISI / FVG on 15m, 1h, 4h) and the entry is a 1m array inside it (11-20: "buy limits in 1m BISI").
references/models.md §6 (OB / breaker / mitigation variants) are later variants of this card.

Mechanical version (bullish; bearish is the mirror):
    array      an FVG (``arrays``; or OB / breaker / mitigation block, models.md §6) on ``htf_tfs`` (15m / 1h / 4h)
               in the trade direction, formed within ``lookback_days``,
               still valid (no body close beyond its far edge, framework.md §9) when price returns to it.
    return     inside a trading window, price trades into the array (reaches its near edge).
    trigger    a ``trigger_tf`` (1m) FVG in the trade direction forms in the reaction, within ``trigger_wait_min``
               of the touch, without price closing through the array first. Decision = that FVG's completion.
    entry      limit at the 1m FVG's near edge (``entry_level``: proximal | ce).
    stop       ``stop_mode``: "reaction" = beyond the lowest low between the touch and the decision (ICT's tight
               live stops); "array" = beyond the array's far edge. Plus ``stop_buffer``.
    target     TP1 = nearest untaken liquidity (5m/15m swing highs, Asia/PD/PW highs) ≥ ``min_tp1_r`` × risk.
    invalid    the array's far edge (an HTF close through it is the exit when ``invalidate_tf`` is set).
    gates      time → bias → trigger → target → risk (cost). One trade per window (engine default).
"""

from __future__ import annotations

from dataclasses import replace, dataclass, field
from datetime import date, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import DayContext, build_context
from ict_engine.concepts.events import (BLOCK_KINDS, Event, breaker_blocks, fvgs, gap_lifecycle, inversions,
                                       order_blocks, swings)
from ict_engine.data.instruments import cost_at
from ict_engine.models.base import Gate, Setup, TradePlan
from ict_engine.models.model_2022 import _targets, _ts, _window_at, _window_end, bias_gate

MODEL = "pd_return"
NAMES = ("pd_return", "pd_array_return")          # reference cases label it pd_array_return
TF_RANK = {"15m": 1, "1h": 2, "4h": 3, "1d": 4, "1w": 5, "1M": 6}
# extra history so a weekly/monthly FVG (3 candles) can form before the lookback starts; the first, partial
# weekly/monthly bar of the history is dropped
HIST_EXTRA_DAYS = {"1w": 21, "1M": 93}


@dataclass(frozen=True)
class Params:
    windows: tuple[str, ...] = ("london_kz", "ny_premarket", "ny_am_kz", "ny_pm_kz")
    htf_tfs: tuple[str, ...] = ("15m", "1h", "4h")
    arrays: tuple[str, ...] = ("fvg",)    # fvg | ifvg | ob | breaker | mitigation (models.md §6 variants)
    ifvg_close: str = "tf"               # an HTF FVG inverts on a close of its own TF ("tf") | first 1m close ("1m")
    ifvg_bias: str = "gate"              # "override": an IFVG trade may go against the daily bias (sellers' turn)
    ob_confirm: str = "extreme"          # OB known on a close beyond its extreme (Bible p.16) | "open" (close through its open)
    ob_measure: str = "range"            # OB zone + 50% on the full range | "body" (ICT Month 04: open to close, no wicks)
    lookback_days: int = 5
    return_level: str = "proximal"       # the return = the first trade to the array's near edge | "ce" (its 50%)
    trigger_tf: str = "1m"
    trigger_wait_min: int = 30
    min_trigger_gap_bp: float = 0.2      # ignore sliver gaps (< 0.2 bp of price, e.g. < 0.3 pt on NQ)
    entry_level: str = "proximal"        # proximal | ce
    stop_mode: str = "reaction"          # reaction | array
    stop_buffer: float = 0.0
    min_tp1_r: float = 1.0
    tp1_cap_r: float | None = None
    max_cost_r: float | None = 0.1
    use_bias: bool = True
    bias_rule: str = "prev_day_dol"
    neutral_bias: str = "opening_range"
    cap_scope: str = "window"           # not stated for this model → the engine default (one per window)
    invalidate_tf: str | None = None
    news_blackout: tuple[int, int] | None = None
    target_mode: str = "default"         # targets.MODES (liquidity-targets pre-registration)
    entry_gate: str | None = None        # entry_quality.GATES (entry-quality pre-registration)
    fomc_day: str = "trade"
    partial_frac: float = 0.5
    runner_stop: str = "entry"
    tags: dict = field(default_factory=dict, compare=False)

    @property
    def variant(self) -> str:
        d = Params()
        parts = [f"pdr-{'+'.join(self.htf_tfs)}>{self.trigger_tf}"]
        for name in ("arrays", "ifvg_close", "ifvg_bias", "ob_confirm", "ob_measure", "windows", "lookback_days", "return_level", "trigger_wait_min", "min_trigger_gap_bp", "entry_level", "stop_mode", "stop_buffer",
                     "min_tp1_r", "tp1_cap_r", "max_cost_r", "use_bias", "bias_rule", "cap_scope", "invalidate_tf",
                     "news_blackout", "fomc_day", "partial_frac", "runner_stop", "target_mode", "entry_gate"):
            if getattr(self, name) != getattr(d, name):
                parts.append(f"{name}={getattr(self, name)}")
        return "-".join(parts)


# --- pieces (pure, unit-tested) ---------------------------------------------------------------

def htf_arrays(hist_1m: pd.DataFrame, tfs: tuple[str, ...], kinds: tuple[str, ...] = ("fvg",),
               ob_confirm: str = "extreme", ob_measure: str = "range", ifvg_close: str = "tf") -> list[Event]:
    """PD arrays on each higher timeframe of the history (each known from its ``ts``): FVGs, IFVGs (failed FVGs,
    inverted on a close of their own timeframe with ``ifvg_close="tf"``, else on the first 1m close), order
    blocks, breakers and/or mitigation blocks. ``ob_measure="body"`` turns each OB into its body (open-to-close
    range of its candles), so the zone, the 50% (mean threshold) and the fail level ignore wicks."""
    if ifvg_close not in ("tf", "1m"):
        raise ValueError(f"ifvg_close must be 'tf' or '1m', got {ifvg_close!r}")
    out = []
    for tf in tfs:
        bars = resample(hist_1m, tf)
        if tf in HIST_EXTRA_DAYS:
            bars = bars.iloc[1:]                     # the history starts mid-week/month: that bar is partial
        if "fvg" in kinds:
            out += fvgs(bars, tf)
        if "ifvg" in kinds:
            out += inversions(fvgs(bars, tf), hist_1m, tf_bars={tf: bars} if ifvg_close == "tf" else None)
        if "ob" in kinds:
            obs = order_blocks(bars, tf, confirm=ob_confirm)
            if ob_measure == "body":
                obs = [replace(o, top=o.meta["body"][0], bottom=o.meta["body"][1]) for o in obs]
            out += obs
        if "breaker" in kinds or "mitigation" in kinds:
            out += [b for b in breaker_blocks(bars, tf) if b.kind in kinds]
    return out


def fail_level(array: Event) -> float:
    """Where the array has failed: a body close beyond its far edge (FVG) or its 50% (blocks, Bible p.17)."""
    if array.kind in BLOCK_KINDS:
        return array.ce
    return array.bottom if array.direction == "bull" else array.top


def returns(arrays: list[Event], day_1m: pd.DataFrame, window_start: pd.Timestamp,
            level: str = "proximal") -> list[tuple[Event, pd.Timestamp]]:
    """(array, first touch) for every array that is still valid when price first trades back into it,
    with the touch on or after ``window_start`` (the day's 00:00; time windows are gated later).
    ``level`` "proximal" = the touch of the near edge; "ce" = the first trade to the array's 50%."""
    if level not in ("proximal", "ce"):
        raise ValueError(f"return level must be 'proximal' or 'ce', not {level!r}")
    out = []
    for g in arrays:
        st = gap_lifecycle(g, day_1m[day_1m.index >= g.ts])
        t = st.touched if level == "proximal" else st.ce
        if t is None or t < window_start or not st.valid_at(t):
            continue
        out.append((g, t))
    return sorted(out, key=lambda x: x[1])


def reaction_trigger(array: Event, touch: pd.Timestamp, day_1m: pd.DataFrame, ltf_gaps: list[Event],
                     wait_min: int) -> tuple[Event, float] | None:
    """First LTF FVG in the array's direction that forms in the reaction: its first candle starts at or after the
    touch and it completes within ``wait_min``, and no body closed beyond the array's far edge before it.
    Returns (fvg, reaction extreme between touch and the FVG's completion)."""
    long = array.direction == "bull"
    until = touch + pd.Timedelta(minutes=wait_min)
    for f in sorted(ltf_gaps, key=lambda g: g.ts):
        if f.direction != array.direction or f.origin_ts < touch or f.ts > until:
            continue
        seg = day_1m[(day_1m.index >= touch) & (day_1m.index <= f.ts)]
        if seg.empty:
            continue
        lvl = fail_level(array)
        broke = (seg.close < lvl).any() if long else (seg.close > lvl).any()
        if broke:
            return None                       # the array failed before the reaction showed up
        ext = float(seg.low.min()) if long else float(seg.high.max())
        return f, ext
    return None


# --- model --------------------------------------------------------------------------------------

def find_setups(bars_1m: pd.DataFrame, day: date, asset: str, p: Params = Params(),
                ctx: DayContext | None = None) -> list[Setup]:
    ctx = ctx or build_context(bars_1m, day)
    d0, d1 = _ts(day, time(0)), _ts(day, time(16, 30))
    day_1m = bars_1m[(bars_1m.index >= d0) & (bars_1m.index < d1)]
    if day_1m.empty:
        return []
    extra = max((HIST_EXTRA_DAYS.get(tf, 0) for tf in p.htf_tfs), default=0)
    hist = bars_1m[(bars_1m.index >= d0 - timedelta(days=p.lookback_days + 2 + extra)) & (bars_1m.index < d1)]
    arrays = [g for g in htf_arrays(hist, p.htf_tfs, p.arrays, p.ob_confirm, p.ob_measure, p.ifvg_close)
              if g.ts >= d0 - timedelta(days=p.lookback_days)]
    ref = float(day_1m.close.iloc[0])
    ltf = fvgs(resample(day_1m, p.trigger_tf), p.trigger_tf, min_size=ref * p.min_trigger_gap_bp / 1e4)
    swing_pts = swings(resample(day_1m, "5m"), "5m") + swings(resample(day_1m, "15m"), "15m")
    out, seen = [], set()
    # bigger timeframes first, so one reaction is credited to the largest array it came from
    for g, touch in sorted(returns(arrays, day_1m, d0, p.return_level), key=lambda x: (x[1], -TF_RANK.get(x[0].tf, 0))):
        s = _evaluate(g, touch, ctx, day, asset, p, day_1m, ltf, swing_pts, bars_1m=bars_1m)
        key = (s.side, s.decided_at)
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _evaluate(g: Event, touch, ctx, day, asset, p: Params, day_1m, ltf, swing_pts, bars_1m=None) -> Setup:
    long = g.direction == "bull"
    side = "long" if long else "short"
    name = g.kind.upper() if g.kind != "mitigation" else "MB"
    ret = Event("return", g.tf, g.direction, touch, g.origin_ts, g.top, g.bottom,
                {"level": f"{g.tf} {name} {g.bottom:.2f}-{g.top:.2f}"})
    setup = Setup(MODEL, p.variant, asset, "day", day, side, touch, {"poi": g, "liquidity": ret},
                  pd_array="fvg", pd_array_tf=p.trigger_tf)
    setup.tags.update({"array_tf": g.tf, "array_kind": g.kind, "array": f"{g.bottom:.2f}-{g.top:.2f}",
                       "poi": f"{g.tf} {name}"})
    trig = reaction_trigger(g, touch, day_1m, ltf, p.trigger_wait_min)
    decided = trig[0].ts if trig else touch
    setup.decided_at = decided
    w = _window_at(decided, p.windows)
    setup.tags["window"] = w.name if w else None
    setup.gates.append(Gate("time", w is not None, w.name if w else f"{decided:%H:%M} outside {p.windows}"))
    bias = bias_gate(ctx, long, decided, day_1m, p)
    if g.kind == "ifvg" and p.ifvg_bias == "override" and not bias.passed:
        bias = Gate("bias", True, f"IFVG overrides the bias (counter-bias leg); {bias.detail}")
    setup.gates.append(bias)
    if trig is None:
        setup.gates.append(Gate("trigger", False, f"no {p.trigger_tf} FVG within {p.trigger_wait_min}m of the "
                                                  f"return to the {g.tf} {name} (or the array failed first)"))
        return setup
    f, ext = trig
    setup.evidence["fvg"] = f
    entry = {"proximal": f.top if long else f.bottom, "ce": f.ce}[p.entry_level]
    anchor = ext if p.stop_mode == "reaction" else (g.bottom if long else g.top)   # array: beyond the whole zone
    stop = anchor - p.stop_buffer if long else anchor + p.stop_buffer
    if (long and not stop < entry) or (not long and not stop > entry):
        setup.gates.append(Gate("trigger", False, f"stop {stop:.2f} on wrong side of entry {entry:.2f}"))
        return setup
    risk = abs(entry - stop)
    setup.gates.append(Gate("trigger", True, f"returned to {g.tf} {name} {g.bottom:.2f}-{g.top:.2f} at {touch:%H:%M}; "
                                             f"{p.trigger_tf} FVG {f.bottom:.2f}-{f.top:.2f}"))
    tp1, tp1_name, final, final_name = _targets(entry, long, ctx, day_1m, decided, swing_pts,
                                                min_dist=p.min_tp1_r * risk)
    if tp1 is None:
        setup.gates.append(Gate("target", False, f"no untaken liquidity ≥ {p.min_tp1_r:g}R"))
        return setup
    if p.tp1_cap_r is not None and abs(tp1 - entry) > p.tp1_cap_r * risk:
        tp1, tp1_name = entry + (1 if long else -1) * p.tp1_cap_r * risk, f"cap {p.tp1_cap_r:g}R"
    from ict_engine.models import targets
    tp1, tp1_name, final, final_name, t_exit = targets.apply(
        p.target_mode, entry=entry, stop=stop, long=long, tp1=tp1, tp1_name=tp1_name, final=final, final_name=final_name,
        bars_1m=day_1m if bars_1m is None else bars_1m, decided=decided, ctx=ctx, day=day, min_tp1=p.min_tp1_r * risk)
    setup.tags["dol"] = final_name
    setup.gates.append(Gate("target", True, f"TP1 {tp1_name} {tp1:.2f}, final {final_name} {final:.2f}"))
    if p.max_cost_r is not None:
        cost_r = cost_at(asset, entry, decided) / risk
        setup.gates.append(Gate("risk", cost_r <= p.max_cost_r, f"cost {cost_r:.2f}R (max {p.max_cost_r:g}R)"))
    expires = _window_end(decided, w) if w else decided
    setup.would_plan = TradePlan(side, decided, expires, entry, stop, tp1, final, tp1_name, final_name,
                                 invalid_level=fail_level(g), invalid_tf=p.invalidate_tf, time_exit=t_exit)
    if all(x.passed for x in setup.gates):
        setup.plan = setup.would_plan
    return setup
