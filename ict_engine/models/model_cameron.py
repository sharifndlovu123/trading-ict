"""Cameron's Model — ICT (Twitter Space), as taught to his son; references/models.md, setups.md §5.

Mechanical version (bullish; bearish is the mirror):
    draw        the nearest untaken ``draw_tf`` (1h) candle high from the last ``draw_lookback_h``
                hours, at least ``min_tp1_r`` × risk above entry. Price must already be running
                to it (``require_running``): the last finished draw-TF candle closed above the
                one before. No 1h draw → ``fallback_tf`` (15m) candle highs.
    trigger     on ``trigger_tf`` (5m): a confirmed swing low is taken by a later candle (even by
                a tick), and the NEXT candle closes up and back above the swept low. Decision =
                that candle's close.
    entry       the first ``entry_tf`` (1m) FVG formed in the move after the sweep (by the decision
                + ``fvg_wait_min``), at its proximal edge; still valid when the order is placed.
    stop        beyond the swept extreme (+ ``stop_buffer``).
    target      TP1 = the draw (ICT: "the swing high / intraday candle being drawn to").
    time        not stated by the source → the standard windows, each scored as its own bucket
                (time is checked first: decisions outside every window are logged, never traded).
    cap         one trade per day (Cameron rules, ruling #1).
    gates       time → bias (off by default; the draw replaces it) → trigger → target → risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import DayContext, build_context
from ict_engine.concepts.events import Event, fvgs, gap_lifecycle, swings
from ict_engine.data.instruments import cost_at
from ict_engine.models.base import Gate, Setup, TradePlan
from ict_engine.models.model_2022 import _ts, _window_at, _window_end, bias_gate

MODEL = "cameron"
TF_MIN = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}


@dataclass(frozen=True)
class Params:
    windows: tuple[str, ...] = ("london_kz", "ny_premarket", "ny_am_kz", "ny_pm_kz")
    trigger_tf: str = "5m"
    entry_tf: str = "1m"                 # one timeframe lower than the trigger
    draw_tf: str = "1h"
    fallback_tf: str = "15m"
    draw_lookback_h: int = 8
    require_running: bool = True
    fvg_wait_min: int = 10               # the FVG may complete up to this long after the decision
    entry_level: str = "proximal"        # proximal | ce
    stop_buffer: float = 0.25
    min_tp1_r: float = 1.0
    tp1_cap_r: float | None = None
    max_cost_r: float | None = 0.1
    use_bias: bool = False               # not in the source; the draw sets the direction
    bias_rule: str = "prev_day_dol"
    neutral_bias: str = "opening_range"
    cap_scope: str = "day"               # one trade per day (Cameron rules, ruling #1)
    invalidate_tf: str | None = None
    news_blackout: tuple[int, int] | None = None
    fomc_day: str = "trade"
    partial_frac: float = 0.5
    runner_stop: str = "entry"
    tags: dict = field(default_factory=dict, compare=False)

    @property
    def variant(self) -> str:
        d = Params()
        parts = [f"cam-{self.trigger_tf}>{self.entry_tf}-draw{self.draw_tf}"]
        for name in ("windows", "require_running", "draw_lookback_h", "fvg_wait_min", "entry_level", "min_tp1_r",
                     "tp1_cap_r", "max_cost_r", "use_bias", "bias_rule", "cap_scope", "invalidate_tf",
                     "news_blackout", "fomc_day", "partial_frac", "runner_stop"):
            if getattr(self, name) != getattr(d, name):
                parts.append(f"{name}={getattr(self, name)}")
        return "-".join(parts)


# --- pieces (pure, unit-tested) ---------------------------------------------------------------

def finished(htf: pd.DataFrame, tf: str, now: pd.Timestamp) -> pd.DataFrame:
    """Candles of ``htf`` (resampled, index = candle start) fully closed by ``now`` (a 1m bar start)."""
    return htf[htf.index + pd.Timedelta(minutes=TF_MIN[tf]) <= now + pd.Timedelta(minutes=1)]


def running_toward(done: pd.DataFrame, long: bool) -> bool:
    """The last finished candle closed beyond the one before, in the trade's direction."""
    if len(done) < 2:
        return False
    a, b = float(done.close.iloc[-2]), float(done.close.iloc[-1])
    return b > a if long else b < a


def draw_level(hist_1m: pd.DataFrame, now: pd.Timestamp, long: bool, entry: float, min_dist: float,
               p: Params) -> tuple[float, str] | None:
    """Nearest untaken draw-TF (else fallback-TF) candle extreme beyond entry by ≥ ``min_dist``."""
    seen = hist_1m[hist_1m.index <= now]
    since = now - pd.Timedelta(hours=p.draw_lookback_h)
    for tf in (p.draw_tf, p.fallback_tf):
        done = finished(resample(seen[seen.index >= since - pd.Timedelta(hours=1)], tf), tf, now)
        done = done[done.index >= since]
        cands = []
        for start, c in done.iterrows():
            lvl = float(c.high if long else c.low)
            after = seen[seen.index >= start + pd.Timedelta(minutes=TF_MIN[tf])]
            untaken = after.empty or (after.high.max() < lvl if long else after.low.min() > lvl)
            far = (lvl - entry if long else entry - lvl) >= min_dist
            if untaken and far:
                cands.append((lvl, f"{tf} high {start:%H:%M}" if long else f"{tf} low {start:%H:%M}"))
        if cands:
            return min(cands, key=lambda x: abs(x[0] - entry))
    return None


def triggers(trig: pd.DataFrame, tf: str) -> list[dict]:
    """Swing taken by one candle; the next candle closes back beyond it in the reversal direction."""
    out = []
    rows = trig.reset_index().rename(columns={trig.index.name or "index": "start"})
    for s in swings(trig, tf):
        long = s.kind == "swing_low"
        lvl = s.bottom if long else s.top
        later = rows[rows.start > s.origin_ts]
        later = later[later.close_ts > s.ts]                     # only after the swing is confirmed
        hit = later[later.low < lvl] if long else later[later.high > lvl]
        if hit.empty:
            continue
        k = hit.index[0]
        if k + 1 not in rows.index:
            continue
        nxt = rows.loc[k + 1]
        ok = (nxt.close > nxt.open and nxt.close > lvl) if long else (nxt.close < nxt.open and nxt.close < lvl)
        if not ok:
            continue
        ext = min(rows.loc[k].low, nxt.low) if long else max(rows.loc[k].high, nxt.high)
        out.append({"long": long, "level": float(lvl), "swing": s, "sweep_start": rows.loc[k].start,
                    "decided": nxt.close_ts, "extreme": float(ext)})
    return sorted(out, key=lambda x: x["decided"])


# --- model --------------------------------------------------------------------------------------

def find_setups(bars_1m: pd.DataFrame, day: date, asset: str, p: Params = Params(),
                ctx: DayContext | None = None) -> list[Setup]:
    ctx = ctx or build_context(bars_1m, day)
    d0, d1 = _ts(day, time(0)), _ts(day, time(16, 30))
    day_1m = bars_1m[(bars_1m.index >= d0) & (bars_1m.index < d1)]
    if day_1m.empty:
        return []
    hist = bars_1m[(bars_1m.index >= d0 - timedelta(hours=p.draw_lookback_h + 2)) & (bars_1m.index < d1)]
    trig = resample(day_1m, p.trigger_tf)
    gaps = fvgs(resample(day_1m, p.entry_tf), p.entry_tf)
    return [_evaluate(t, ctx, day, asset, p, day_1m, hist, gaps) for t in triggers(trig, p.trigger_tf)]


def _evaluate(t: dict, ctx, day, asset, p: Params, day_1m, hist, gaps) -> Setup:
    long = t["long"]
    side = "long" if long else "short"
    decided = pd.Timestamp(t["decided"])
    want = "bull" if long else "bear"
    sweep = Event("sweep", p.trigger_tf, want, decided, t["sweep_start"], t["level"], t["level"],
                  {"level": f"{p.trigger_tf} swing {'low' if long else 'high'}"})
    setup = Setup(MODEL, p.variant, asset, "day", day, side, decided, {"liquidity": sweep},
                  pd_array="fvg", pd_array_tf=p.entry_tf)
    setup.tags.update({"swept": t["level"]})

    # entry FVG: first one formed in the move after the sweep, complete by decided + wait
    wait_until = decided + pd.Timedelta(minutes=p.fvg_wait_min)
    cands = [g for g in gaps if g.direction == want and g.origin_ts >= t["sweep_start"] and g.ts <= wait_until]
    fvg = min(cands, key=lambda g: g.origin_ts) if cands else None
    if fvg is not None:
        decided = max(decided, fvg.ts)
        setup.decided_at = decided
    w = _window_at(decided, p.windows)
    setup.tags["window"] = w.name if w else None
    setup.gates.append(Gate("time", w is not None, w.name if w else f"{decided:%H:%M} outside {p.windows}"))
    if p.use_bias:
        setup.gates.append(bias_gate(ctx, long, decided, day_1m, p))
    if fvg is None:
        setup.gates.append(Gate("trigger", False, "no FVG after the sweep"))
        return setup
    if not gap_lifecycle(fvg, day_1m, until=decided).valid_at(decided):
        setup.gates.append(Gate("trigger", False, "FVG already invalidated at the decision"))
        return setup
    setup.evidence["fvg"] = fvg
    entry = {"proximal": fvg.top if long else fvg.bottom, "ce": fvg.ce}[p.entry_level]
    stop = t["extreme"] - p.stop_buffer if long else t["extreme"] + p.stop_buffer
    if (long and not stop < entry) or (not long and not stop > entry):
        setup.gates.append(Gate("trigger", False, f"stop {stop:.2f} on wrong side of entry {entry:.2f}"))
        return setup
    risk = abs(entry - stop)

    # running toward the draw (finished draw-TF candles only)
    done = finished(resample(hist[hist.index <= decided], p.draw_tf), p.draw_tf, decided)
    run_ok = running_toward(done, long)
    setup.gates.append(Gate("trigger", run_ok or not p.require_running,
                            f"{p.trigger_tf} swing {t['level']:.2f} swept, next candle closed back; "
                            f"{p.entry_tf} FVG {fvg.bottom:.2f}-{fvg.top:.2f}; "
                            f"{p.draw_tf} {'running toward the draw' if run_ok else 'not running toward the draw'}"))

    draw = draw_level(hist, decided, long, entry, p.min_tp1_r * risk, p)
    if draw is None:
        setup.gates.append(Gate("target", False, f"no untaken {p.draw_tf}/{p.fallback_tf} draw ≥ {p.min_tp1_r:g}R"))
        return setup
    tp1, tp1_name = draw
    final, final_name = tp1, tp1_name
    if p.tp1_cap_r is not None and abs(tp1 - entry) > p.tp1_cap_r * risk:
        tp1, tp1_name = entry + (1 if long else -1) * p.tp1_cap_r * risk, f"cap {p.tp1_cap_r:g}R"
    setup.tags["dol"] = final_name
    setup.gates.append(Gate("target", True, f"draw {final_name} {final:.2f}"))
    if p.max_cost_r is not None:
        cost_r = cost_at(asset, entry, decided) / risk
        setup.gates.append(Gate("risk", cost_r <= p.max_cost_r, f"cost {cost_r:.2f}R (max {p.max_cost_r:g}R)"))

    expires = _window_end(decided, w) if w else decided
    setup.would_plan = TradePlan(side, decided, expires, entry, stop, tp1, final, tp1_name, final_name,
                                 invalid_level=fvg.bottom if long else fvg.top, invalid_tf=p.invalidate_tf)
    if all(g.passed for g in setup.gates):
        setup.plan = setup.would_plan
    return setup
