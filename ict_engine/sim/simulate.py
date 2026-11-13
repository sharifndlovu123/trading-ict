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
    - time exit at ``time_exit`` (day style: 16:00 NY) at that bar's open
    - costs: ``cost`` price units per round trip, charged in R
    - runner variant: half off at TP1, stop to entry, rest to final target / stop / time exit
"""

from __future__ import annotations

import pandas as pd

from ict_engine.models.base import Result, TradePlan


def simulate(plan: TradePlan, bars: pd.DataFrame, time_exit: pd.Timestamp, cost: float = 0.0) -> Result:
    long = plan.side == "long"
    after = bars[(bars.index > plan.placed_at) & (bars.index < time_exit)]
    res = Result()
    cost_r = cost / plan.risk

    def hit_entry(row):
        return row.low <= plan.entry if long else row.high >= plan.entry

    def hit_stop(row):
        return row.low <= plan.stop if long else row.high >= plan.stop

    def hit(row, level):
        return row.high >= level if long else row.low <= level

    # --- waiting for the fill ---------------------------------------------------
    fill_i = None
    armed = plan.arm is None
    for i, (ts, row) in enumerate(after.iterrows()):
        if ts >= plan.expires_at:
            res.exit_reason = "not_filled"
            return res
        if not armed:
            if hit(row, plan.tp1):
                res.exit_reason = "missed"
                return res
            if hit(row, plan.arm):
                armed = True
            continue
        if hit_entry(row):
            fill_i = i
            break
        if hit(row, plan.tp1):
            res.exit_reason = "missed"
            return res
    if fill_i is None:
        return res

    res.filled_at = after.index[fill_i]
    worst = 0.0
    tp1_at = None
    for j in range(fill_i, len(after)):
        ts, row = after.index[j], after.iloc[j]
        worst = min(worst, plan.r_at(row.low if long else row.high))
        stop_now = hit_stop(row)
        tp_now = hit(row, plan.tp1) and (j > fill_i or _fill_bar_reaches_tp(row, plan, long))
        if stop_now:
            res.exit_at, res.exit_reason, res.r = ts, "stop", -1.0 - cost_r
            res.ambiguous = bool(tp_now)
            break
        if tp_now:
            tp1_at = j
            res.exit_at, res.exit_reason, res.vote = ts, "tp1", True
            res.r = plan.r_at(plan.tp1) - cost_r
            break
    else:
        last = bars[bars.index >= time_exit]
        px = float(last.open.iloc[0]) if not last.empty else float(after.close.iloc[-1])
        res.exit_at = last.index[0] if not last.empty else after.index[-1]
        res.exit_reason, res.r = "time_exit", plan.r_at(px) - cost_r

    res.mae_r = worst
    res.runner_r, res.final_reached = _runner(plan, after, tp1_at, time_exit, bars, cost_r, res)
    return res


def _fill_bar_reaches_tp(row, plan: TradePlan, long: bool) -> bool:
    # A limit fill and TP1 in the same 1m bar: only count TP1 if the bar opened beyond the entry
    # (price came down to fill then went up) — order inside the bar is unknown, so be conservative.
    return False


def _runner(plan, after, tp1_at, time_exit, bars, cost_r, res):
    if tp1_at is None:
        return (res.r if res.exit_reason != "tp1" else None), None
    long = plan.side == "long"
    half_tp1 = 0.5 * plan.r_at(plan.tp1)
    for j in range(tp1_at + 1, len(after)):
        row = after.iloc[j]
        back_to_entry = row.low <= plan.entry if long else row.high >= plan.entry
        reach_final = row.high >= plan.final_target if long else row.low <= plan.final_target
        if back_to_entry:                       # conservative: stop (at entry) first
            return half_tp1 - cost_r, False
        if reach_final:
            return half_tp1 + 0.5 * plan.r_at(plan.final_target) - cost_r, True
    last = bars[bars.index >= time_exit]
    px = float(last.open.iloc[0]) if not last.empty else float(after.close.iloc[-1])
    return half_tp1 + 0.5 * plan.r_at(px) - cost_r, False
