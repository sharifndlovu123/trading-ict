"""Bar-by-bar simulation of a frozen TradePlan on 1m bars — pipeline stage 7.

Rules (pipeline.md §7):
    - limit order: fills when price trades to the entry after ``placed_at`` and before ``expires_at``
    - if the plan has an ``arm`` level the order only goes live after a bar trades there (longs:
      high ≥ arm); it can fill from the NEXT bar (order inside a bar is unknown)
    - before the fill, the order is cancelled if the stop level trades first ("cancelled")
      or if TP1 trades first ("missed" — the move left without us)
    - the fill bar itself may also hit the stop (counted); it can't also hit TP1 unless the
      bar trades through both — then the stop is assumed first and the trade is flagged ambiguous
    - after the fill: stop and TP1 in the same bar → stop first, ambiguous=True
    - invalidation (plan.invalid_tf set): after the fill, when a ``invalid_tf`` candle finishes with
      its close beyond ``invalid_level`` (the retest area did not hold), exit at the next 1m bar's
      open ("invalidated"). Stop/TP1 inside that last bar come first. Only finished candles count.
    - time exit at ``time_exit`` (day style: 16:00 NY) at that bar's open
    - costs: ``cost`` price units per round trip, charged in R
    - runner variant: ``partial_frac`` off at TP1, the rest to final target / runner stop / time exit
      (runner stop: entry | lock_half = halfway entry→TP1 | original); a bar touching both the
      runner stop and the final target counts the stop first
    - market order (plan.order == "market"): fills at the open of the first bar after ``placed_at``; R and cost
      are measured from that fill. TP1 may count on the fill bar (the open came first); stop and TP1 in that bar
      → stop first. If the open is already through TP1 ("missed") or the stop ("cancelled"), no trade
"""

from __future__ import annotations

import pandas as pd

from ict_engine.models.base import Result, TradePlan


def simulate(plan: TradePlan, bars: pd.DataFrame, time_exit: pd.Timestamp, cost: float = 0.0) -> Result:
    long = plan.side == "long"
    if plan.time_exit is not None:
        time_exit = plan.time_exit
    after = bars[(bars.index > plan.placed_at) & (bars.index < time_exit)]
    res = Result()
    if plan.order == "market":
        return _market(plan, after, bars, time_exit, cost, res)
    cost_r = cost / plan.risk

    def hit_entry(row):
        return row.low <= plan.entry if long else row.high >= plan.entry

    def hit_stop(row):
        return row.low <= plan.stop if long else row.high >= plan.stop

    def hit(row, level):
        return row.high >= level if long else row.low <= level

    # --- waiting for the fill ---------------------------------------------------
    run_level = None
    if plan.cancel_run_r is not None and plan.arm is None:
        run_level = plan.entry + (1 if long else -1) * plan.cancel_run_r * plan.risk
    fill_i = None
    armed = plan.arm is None
    for i, (ts, row) in enumerate(after.iterrows()):
        if ts >= plan.expires_at:
            res.exit_reason = "not_filled"
            return res
        if not armed:
            if hit(row, plan.tp1):
                res.exit_at, res.exit_reason = ts, "missed"      # order cancelled; slot is free again
                return res
            if hit(row, plan.arm):
                armed = True
            continue
        if hit_entry(row):
            fill_i = i
            break
        if hit(row, plan.tp1) or (run_level is not None and hit(row, run_level)):
            res.exit_at, res.exit_reason = ts, "missed"
            return res
    if fill_i is None:
        return res

    return _after_fill(plan, after, bars, time_exit, fill_i, cost_r, res, tp_on_fill_bar=False)


def _market(plan: TradePlan, after: pd.DataFrame, bars: pd.DataFrame, time_exit, cost: float, res: Result) -> Result:
    """Market order: fill at the first bar's open. No trade if that open is already at/through the stop or TP1."""
    if after.empty:
        res.exit_reason = "not_filled"
        return res
    from dataclasses import replace
    long = plan.side == "long"
    px = float(after.open.iloc[0])
    if (long and (px <= plan.stop or px >= plan.tp1)) or (not long and (px >= plan.stop or px <= plan.tp1)):
        res.exit_at = after.index[0]
        res.exit_reason = "missed" if (px >= plan.tp1 if long else px <= plan.tp1) else "cancelled"
        return res
    filled = replace(plan, entry=px, arm=None)
    return _after_fill(filled, after, bars, time_exit, 0, cost / filled.risk, res, tp_on_fill_bar=True)


def _after_fill(plan: TradePlan, after: pd.DataFrame, bars: pd.DataFrame, time_exit, fill_i: int, cost_r: float,
                res: Result, tp_on_fill_bar: bool) -> Result:
    long = plan.side == "long"

    def hit_stop(row):
        return row.low <= plan.stop if long else row.high >= plan.stop

    def hit(row, level):
        return row.high >= level if long else row.low <= level

    res.filled_at = after.index[fill_i]
    res.fill_price = plan.entry
    worst = 0.0
    tp1_at = None
    tf_min = _tf_minutes(plan.invalid_tf) if plan.invalid_tf and plan.invalid_level is not None else None
    exit_next = False
    for j in range(fill_i, len(after)):
        ts, row = after.index[j], after.iloc[j]
        if exit_next:                                   # the HTF close beyond the area was known at this open
            px = float(row.open)
            worst = min(worst, plan.r_at(px))
            res.exit_at, res.exit_reason, res.r = ts, "invalidated", plan.r_at(px) - cost_r
            break
        worst = min(worst, plan.r_at(row.low if long else row.high))
        stop_now = hit_stop(row)
        tp_now = hit(row, plan.tp1) and (j > fill_i or tp_on_fill_bar or _fill_bar_reaches_tp(row, plan, long))
        if stop_now:
            res.exit_at, res.exit_reason, res.r = ts, "stop", -1.0 - cost_r
            res.ambiguous = bool(tp_now)
            break
        if tp_now:
            tp1_at = j
            res.exit_at, res.exit_reason, res.vote = ts, "tp1", True
            res.r = plan.r_at(plan.tp1) - cost_r
            break
        if tf_min and _bucket_ends(after.index, j, tf_min):
            exit_next = row.close < plan.invalid_level if long else row.close > plan.invalid_level
    else:
        last = _exit_bars(bars, time_exit, plan)
        px = float(last.open.iloc[0]) if not last.empty else float(after.close.iloc[-1])
        res.exit_at = last.index[0] if not last.empty else after.index[-1]
        res.exit_reason, res.r = "time_exit", plan.r_at(px) - cost_r

    res.mae_r = worst
    res.runner_r, res.final_reached = _runner(plan, after, tp1_at, time_exit, bars, cost_r, res)
    return res


def _tf_minutes(tf: str) -> int:
    n, unit = int(tf[:-1]), tf[-1]
    return n * {"m": 1, "h": 60}[unit]


def _bucket_ends(idx: pd.DatetimeIndex, j: int, tf_min: int) -> bool:
    """Bar j is the last 1m bar of its ``tf_min`` candle (buckets aligned to NY midnight): either
    the next minute starts a new bucket, or the next bar we have lies in another bucket (data gap)."""
    def bucket(ts):
        return (ts.hour * 60 + ts.minute) // tf_min
    ts = idx[j]
    if (ts.hour * 60 + ts.minute + 1) % tf_min == 0:
        return True
    return j + 1 < len(idx) and (bucket(idx[j + 1]) != bucket(ts) or idx[j + 1].date() != ts.date())


def _fill_bar_reaches_tp(row, plan: TradePlan, long: bool) -> bool:
    # A limit fill and TP1 in the same 1m bar: only count TP1 if the bar opened beyond the entry
    # (price came down to fill then went up) — order inside the bar is unknown, so be conservative.
    return False


RUNNER_STOPS = ("entry", "lock_half", "original", "trail_5m", "trail_15m")


def _trail_tf(runner_stop: str) -> int | None:
    return _tf_minutes(runner_stop[6:]) if runner_stop.startswith("trail_") else None


def _runner(plan, after, tp1_at, time_exit, bars, cost_r, res):
    if plan.runner_stop not in RUNNER_STOPS:
        raise ValueError(f"runner_stop must be one of {RUNNER_STOPS}, not {plan.runner_stop!r}")
    if tp1_at is None:
        return (res.r if res.exit_reason != "tp1" else None), None
    long = plan.side == "long"
    f = plan.partial_frac
    banked = f * plan.r_at(plan.tp1)
    trail = _trail_tf(plan.runner_stop)
    if trail:
        return _trailed(plan, after, tp1_at, time_exit, bars, cost_r, res, trail, banked)
    stop_px = {"entry": plan.entry, "original": plan.stop,
               "lock_half": plan.entry + (plan.tp1 - plan.entry) / 2}[plan.runner_stop]
    for j in range(tp1_at + 1, len(after)):
        row = after.iloc[j]
        stopped = row.low <= stop_px if long else row.high >= stop_px
        reach_final = row.high >= plan.final_target if long else row.low <= plan.final_target
        if stopped:                             # conservative: runner stop first
            return banked + (1 - f) * plan.r_at(stop_px) - cost_r, False
        if reach_final:
            return banked + (1 - f) * plan.r_at(plan.final_target) - cost_r, True
    last = _exit_bars(bars, time_exit, plan)
    px = float(last.open.iloc[0]) if not last.empty else float(after.close.iloc[-1])
    return banked + (1 - f) * plan.r_at(px) - cost_r, False


def _trailed(plan, after, tp1_at, time_exit, bars, cost_r, res, tf_min, banked):
    """Runner with no fixed target: stop at entry, then after every finished ``tf_min`` candle it moves to the newest
    confirmed swing (a candle low with a higher low on each side; highs for shorts), never back. Rides until stopped
    or ``plan.runner_until`` (else the trade's time exit). Swings come from candles formed since the fill."""
    long = plan.side == "long"
    f = plan.partial_frac
    until = plan.runner_until or time_exit
    seg = bars[(bars.index >= res.filled_at) & (bars.index < until)]
    tp_ts = after.index[tp1_at]
    stop_px, swing = plan.entry, None
    hi = lo = None
    ext = []                                    # finished candles' lows (long) or highs (short)
    for j in range(len(seg)):
        ts, row = seg.index[j], seg.iloc[j]
        if ts > tp_ts and (row.low <= stop_px if long else row.high >= stop_px):
            return banked + (1 - f) * plan.r_at(stop_px) - cost_r, False
        hi = row.high if hi is None else max(hi, row.high)
        lo = row.low if lo is None else min(lo, row.low)
        if _bucket_ends(seg.index, j, tf_min):
            ext.append(lo if long else hi)
            hi = lo = None
            if len(ext) >= 3:
                a, b, c = ext[-3:]
                if (b < a and b < c) if long else (b > a and b > c):
                    swing = b
        if ts >= tp_ts and swing is not None and ((swing > stop_px) if long else (swing < stop_px)):
            stop_px = swing
    last = bars[(bars.index >= until) & (bars.index < until + pd.Timedelta(minutes=5))]
    px = float(last.open.iloc[0]) if not last.empty else float(seg.close.iloc[-1])
    return banked + (1 - f) * plan.r_at(px) - cost_r, False


def _exit_bars(bars: pd.DataFrame, time_exit: pd.Timestamp, plan: TradePlan) -> pd.DataFrame:
    """Bars from the time exit on. A session-close exit (``plan.time_exit``) only uses a bar within 5 minutes of it,
    so a market that halted earlier exits at its last bar, not at the next session's open."""
    if plan.time_exit is None:
        return bars[bars.index >= time_exit]
    return bars[(bars.index >= time_exit) & (bars.index < time_exit + pd.Timedelta(minutes=5))]
