"""Shared types for models — pipeline stages 5 (gates), 6 (mark) and 8 (record).

A model turns events into **setups**. Every setup is kept (trade or not):
its gate trace says which check stopped it. A setup that passes every enabled
gate gets a frozen **TradePlan**; the simulator turns the plan into a result.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ict_engine.concepts.events import Event
from ict_engine.eval.similarity import TradeSnapshot

GATE_ORDER = ("time", "bias", "pricing", "poi", "trigger")


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class TradePlan:
    """Written before the fill and never edited (pipeline stage 6)."""
    side: str                    # long | short
    placed_at: pd.Timestamp      # when the limit order is placed (decision time)
    expires_at: pd.Timestamp     # end of the model's time window
    entry: float
    stop: float
    tp1: float
    final_target: float
    tp1_name: str = ""
    final_name: str = ""
    arm: float | None = None     # order is live only after price trades here (entry then sits in
                                 # discount/premium of the finished leg); None = live at once
    # Invalidation: the retest area must hold. A finished ``invalid_tf`` candle closing beyond
    # ``invalid_level`` (the area's far edge) ends the idea → exit at the next bar's open.
    invalid_level: float | None = None
    invalid_tf: str | None = None    # e.g. "5m", "15m"; None = hold to stop/TP1 (no invalidation)
    # Partials (runner_r): close ``partial_frac`` at TP1; the rest runs to the final target with its
    # stop at "entry" (breakeven), "lock_half" (halfway entry→TP1) or "original" (initial stop).
    partial_frac: float = 0.5
    runner_stop: str = "entry"
    # "limit": rest at ``entry`` until filled. "market": fill at the open of the first bar after ``placed_at``
    # (``entry`` is then the decision price, for reference); R and costs use the actual fill.
    order: str = "limit"
    # Session-close exit for a day trade held for hours (liquidity-targets amendment 1): overrides the caller's
    # time exit (16:00). None = the caller's. Exit at the open of the first bar at/after it within 5 minutes, else at
    # the close of the last bar before it (CFD indices halt at 16:15).
    time_exit: pd.Timestamp | None = None
    # Runner only: ride past the trade's time exit until this time (trailed runner, preregistered-timeframes-trail);
    # None = the trade's time exit. The part before TP1 keeps its own time exit.
    runner_until: pd.Timestamp | None = None
    # A resting limit is cancelled ("missed") once price has run this many R our way without filling: the move
    # left, a later fill is a stale idea (trade reviews 2026-11-16). None = rest until TP1 trades or the window
    # ends. Not applied to ``arm`` orders, which expect the run before the retrace.
    cancel_run_r: float | None = None

    @property
    def risk(self) -> float:
        return abs(self.entry - self.stop)

    def r_at(self, price: float) -> float:
        sign = 1 if self.side == "long" else -1
        return sign * (price - self.entry) / self.risk


@dataclass
class Result:
    filled_at: pd.Timestamp | None = None
    exit_at: pd.Timestamp | None = None
    exit_reason: str = "not_filled"   # not_filled, missed (TP1 before fill), cancelled, stop, tp1, invalidated, time_exit
    r: float = 0.0                    # R of the all-out-at-TP1 variant, after costs
    vote: bool = False                # TP1 reached before the stop
    ambiguous: bool = False           # stop and TP1 inside one 1m bar (counted as stop)
    final_reached: bool | None = None # runner: final target before stop (after TP1)
    runner_r: float | None = None     # partial_frac at TP1 + the rest as a runner (plan.runner_stop)
    mae_r: float | None = None        # worst excursion before exit (R)
    fill_price: float | None = None   # actual fill (= plan.entry for limits; the next open for market orders)


@dataclass
class Setup:
    """A model's candidate, with its evidence and gate trace (the trade card)."""
    model: str
    variant: str
    asset: str
    style: str
    day: object
    side: str
    decided_at: pd.Timestamp
    evidence: dict[str, Event]                   # step name -> event (the "why")
    gates: list[Gate] = field(default_factory=list)
    plan: TradePlan | None = None
    would_plan: TradePlan | None = None          # the plan it WOULD have had, even when a gate blocked it
    result: Result | None = None
    tags: dict[str, object] = field(default_factory=dict)
    pd_array: str = "fvg"
    pd_array_tf: str = "1m"

    @property
    def traded(self) -> bool:
        return self.plan is not None and self.result is not None and self.result.filled_at is not None

    @property
    def failed_gate(self) -> str | None:
        return next((g.name for g in self.gates if not g.passed), None)

    def snapshot(self, market: str) -> TradeSnapshot:
        """Traits in the shape the evaluator compares (ict_engine/eval/similarity.py)."""
        p = self.plan or self.would_plan
        when = (self.result.filled_at if self.result and self.result.filled_at else self.decided_at)
        liq = self.evidence.get("liquidity")
        return TradeSnapshot(
            day=self.day, market=market, side=self.side,
            entry_time=when.time().replace(second=0, microsecond=0),
            entry_price=p.entry if p else None,
            stop=p.stop if p else None,
            tp1=p.tp1 if p else None,
            final_target=p.final_target if p else None,
            pd_array=self.pd_array, pd_array_tf=self.pd_array_tf,
            liquidity_taken=frozenset({"ssl" if self.side == "long" else "bsl"}) if liq else frozenset(),
            model=self.model,
            outcome=("win" if self.result.vote else "loss") if self.traded else None,
        )
