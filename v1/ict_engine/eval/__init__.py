"""Evaluation: measure engine trades against reference (golden) trades.

Trades are snowflakes — no two are identical — so comparison is by
similarity of traits, never exact equality.
"""

from ict_engine.eval.similarity import (
    TradeSnapshot,
    Comparison,
    DayReport,
    compare,
    match_day,
)
from ict_engine.eval.cases import ReferenceCase, load_cases

__all__ = [
    "TradeSnapshot",
    "Comparison",
    "DayReport",
    "compare",
    "match_day",
    "ReferenceCase",
    "load_cases",
]
