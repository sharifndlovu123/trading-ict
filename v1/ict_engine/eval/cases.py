"""Load reference (golden) trades from YAML."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from ict_engine.eval.basis import Anchor, Offset
from ict_engine.eval.similarity import WEIGHTS, TradeSnapshot, parse_time

# Default price unit per market when a reference has no stop (so no R).
DEFAULT_PRICE_TOL = {"NQ": 10.0, "ES": 2.5, "YM": 25.0}
# Basis uncertainty when only one anchor (no spread to measure) or none.
DEFAULT_BASIS_UNC = {"NQ": 4.0, "ES": 1.0, "YM": 10.0}


@dataclass(frozen=True)
class ReferenceCase:
    id: str
    trade: TradeSnapshot
    contract: str            # e.g. NQZ23 — the engine must use the contract live that day
    author: str              # ict | sharif
    confidence: str          # high | medium | low — how well the chart shows the trade
    source: str              # file + section the case came from
    notes: str = ""
    final_reached: bool | None = None
    anchors: tuple[Anchor, ...] = ()   # named chart levels used to estimate feed basis

    def compare_kwargs(self, offset: "Offset | None" = None) -> dict:
        """Arguments for ``compare``. Pass the Offset estimated from this case's anchors
        on the candidate's feed; None means same feed (no basis)."""
        default_unc = DEFAULT_BASIS_UNC.get(self.trade.market, 0.0)
        if offset is None:
            value, unc = 0.0, 0.0
        elif offset.value is None:          # different feed but no anchors: very unsure
            value, unc = 0.0, float("inf")
        else:
            value = offset.value
            unc = offset.spread if offset.n > 1 else default_unc
            unc = max(unc, default_unc / 2)
        kw = {"price_offset": value, "price_tol": DEFAULT_PRICE_TOL.get(self.trade.market),
              "price_unc": unc}
        if unc == float("inf"):
            kw["weights"] = {**WEIGHTS, "entry": 0.0}   # can't compare absolute entry location
        return kw


def _trade(d: dict) -> TradeSnapshot:
    win = d.get("entry_window")
    return TradeSnapshot(
        day=d["day"] if isinstance(d["day"], date) else date.fromisoformat(d["day"]),
        market=d["market"],
        side=d["side"],
        entry_time=parse_time(d["entry_time"]) if d.get("entry_time") else None,
        entry_window=(parse_time(win[0]), parse_time(win[1])) if win else None,
        entry_price=d.get("entry_price"),
        stop=d.get("stop"),
        tp1=d.get("tp1"),
        final_target=d.get("final_target"),
        pd_array=d.get("pd_array"),
        pd_array_tf=d.get("pd_array_tf"),
        liquidity_taken=frozenset(d.get("liquidity_taken") or ()),
        model=d.get("model"),
        outcome=d.get("outcome"),
    )


def load_cases(path: str | Path) -> list[ReferenceCase]:
    raw = yaml.safe_load(Path(path).read_text())
    return [
        ReferenceCase(
            id=c["id"],
            trade=_trade(c),
            contract=c["contract"],
            author=c.get("author", "ict"),
            confidence=c.get("confidence", "medium"),
            source=c["source"],
            notes=c.get("notes", ""),
            final_reached=c.get("final_reached"),
            anchors=tuple(Anchor(a["level"], float(a["price"])) for a in c.get("anchors") or ()),
        )
        for c in raw["cases"]
    ]
