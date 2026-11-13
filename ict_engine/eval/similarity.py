"""Compare two trades by similarity of traits.

Trades are snowflakes: an engine trade will almost never equal a reference
trade exactly. So each trait is scored 0..1 and combined into a weighted
score. Only side and date are hard gates; everything else can be partly right.

Prices are compared in R (units of the reference trade's risk), so the
comparison works across feeds (Dukascopy CFD vs futures) and contract months.
An optional ``price_offset`` removes a known basis between the two feeds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Iterable, Literal

Side = Literal["long", "short"]

# --- trait vocabularies -------------------------------------------------------

# PD arrays grouped into families; same family = partial credit.
_PD_FAMILY = {
    "fvg": "gap", "bisi": "gap", "sibi": "gap", "ifvg": "gap",
    "vi": "gap", "volume_imbalance": "gap", "liquidity_void": "gap",
    "ndog": "opening_gap", "nwog": "opening_gap", "org": "opening_gap",
    "ob": "block", "order_block": "block", "breaker": "block",
    "mitigation": "block", "rejection_block": "block",
}
# BISI/SIBI are FVGs with a direction — treat as FVG for type matching.
_PD_CANON = {"bisi": "fvg", "sibi": "fvg", "volume_imbalance": "vi", "order_block": "ob"}

_TF_MINUTES = {"1m": 1, "2m": 2, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
               "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}

# Models that share most of their sequence get partial credit.
_MODEL_KIN = [
    {"2022_model", "mmbm", "mmsm", "po3_day"},
    {"silver_bullet", "2022_model"},
    {"pd_array_return", "ote"},
]

# Default weights. Missing traits are dropped and the rest renormalised.
WEIGHTS = {
    "time": 0.25,
    "entry": 0.20,
    "pd_array": 0.15,
    "liquidity": 0.10,
    "risk": 0.10,
    "tp1": 0.10,
    "model": 0.05,
    "market": 0.05,
}

MATCH, SIMILAR = 0.80, 0.60  # verdict thresholds
TIME_SIGMA_MIN = 15.0        # minutes for ~0.6 time similarity
ENTRY_SIGMA_R = 0.5          # entry distance (in R) for ~0.6 similarity
TP1_SIGMA_R = 1.0


@dataclass(frozen=True)
class TradeSnapshot:
    """The traits of one trade — the shape the pipeline emits and cases use.

    Any field may be None when unknown (e.g. ICT's stop not drawn on a chart).
    ``entry_window`` lets a reference say "entered somewhere in 09:33–09:50".
    """

    day: date
    market: str                      # root: NQ, ES, YM, XAU, ...
    side: Side
    entry_time: time | None = None
    entry_window: tuple[time, time] | None = None
    entry_price: float | None = None
    stop: float | None = None
    tp1: float | None = None
    final_target: float | None = None
    pd_array: str | None = None      # fvg, ifvg, ob, breaker, vi, ...
    pd_array_tf: str | None = None   # 1m, 5m, 1h, ...
    liquidity_taken: frozenset[str] = field(default_factory=frozenset)  # ssl, bsl, pdh, asia_low...
    model: str | None = None
    outcome: str | None = None       # win, loss, partial, time_exit

    @property
    def risk(self) -> float | None:
        if self.entry_price is None or self.stop is None:
            return None
        r = abs(self.entry_price - self.stop)
        return r or None

    def tp1_r(self) -> float | None:
        if self.tp1 is None or self.risk is None:
            return None
        sign = 1 if self.side == "long" else -1
        return sign * (self.tp1 - self.entry_price) / self.risk


@dataclass
class Comparison:
    score: float                     # 0..1, weighted over traits that could be compared
    verdict: str                     # match | similar | different
    coverage: float                  # share of total weight that was comparable
    traits: dict[str, float]         # per-trait similarity
    shared: list[str]                # human-readable traits in common
    differences: list[str]


# --- trait scorers ------------------------------------------------------------

def _gauss(d: float, sigma: float) -> float:
    return math.exp(-0.5 * (d / sigma) ** 2)


def _minutes(t: time) -> float:
    return t.hour * 60 + t.minute + t.second / 60


def _time_sim(cand: TradeSnapshot, ref: TradeSnapshot) -> float | None:
    if cand.entry_time is None:
        return None
    c = _minutes(cand.entry_time)
    if ref.entry_window is not None:
        lo, hi = (_minutes(t) for t in ref.entry_window)
        d = 0.0 if lo <= c <= hi else min(abs(c - lo), abs(c - hi))
    elif ref.entry_time is not None:
        d = abs(c - _minutes(ref.entry_time))
    else:
        return None
    return _gauss(d, TIME_SIGMA_MIN)


def _price_scale(ref: TradeSnapshot, price_tol: float | None) -> float | None:
    """Unit for price distances: reference risk (R), else a per-case tolerance."""
    return ref.risk or price_tol


def _entry_sim(cand, ref, offset, price_tol, price_unc):
    if cand.entry_price is None or ref.entry_price is None:
        return None
    unit = _price_scale(ref, price_tol)
    if unit is None:
        return None
    d = abs((cand.entry_price - offset) - ref.entry_price) / unit
    # widen tolerance by how unsure the offset is (both in R units)
    sigma = math.hypot(ENTRY_SIGMA_R, price_unc / unit)
    return _gauss(d, sigma)


def _risk_sim(cand, ref):
    a, b = cand.risk, ref.risk
    if a is None or b is None:
        return None
    return min(a, b) / max(a, b)


def _tp1_sim(cand, ref):
    a, b = cand.tp1_r(), ref.tp1_r()
    if a is None or b is None:
        return None
    return _gauss(a - b, TP1_SIGMA_R)


def _pd_sim(cand, ref):
    if cand.pd_array is None or ref.pd_array is None:
        return None
    a = _PD_CANON.get(cand.pd_array, cand.pd_array)
    b = _PD_CANON.get(ref.pd_array, ref.pd_array)
    if a == b:
        type_sim = 1.0
    elif _PD_FAMILY.get(a) and _PD_FAMILY.get(a) == _PD_FAMILY.get(b):
        type_sim = 0.6
    else:
        type_sim = 0.0
    ta, tb = _TF_MINUTES.get(cand.pd_array_tf or ""), _TF_MINUTES.get(ref.pd_array_tf or "")
    if ta and tb:
        # one "step" per factor of ~3 in timeframe size
        steps = abs(math.log(ta / tb)) / math.log(3)
        tf_sim = max(0.0, 1 - 0.25 * steps)
        return type_sim * (0.75 + 0.25 * tf_sim)
    return type_sim


def _liq_sim(cand, ref):
    a, b = cand.liquidity_taken, ref.liquidity_taken
    if not a or not b:
        return None
    return len(a & b) / len(a | b)


def _model_sim(cand, ref):
    if cand.model is None or ref.model is None:
        return None
    if cand.model == ref.model:
        return 1.0
    if any({cand.model, ref.model} <= kin for kin in _MODEL_KIN):
        return 0.5
    return 0.0


def _market_sim(cand, ref):
    if cand.market == ref.market:
        return 1.0
    # NQ/ES/YM move together (SMT pairs) — a related market is half a match.
    if {cand.market, ref.market} <= {"NQ", "ES", "YM"}:
        return 0.5
    return 0.0


# --- public API ---------------------------------------------------------------

def compare(
    cand: TradeSnapshot,
    ref: TradeSnapshot,
    *,
    price_offset: float = 0.0,
    price_tol: float | None = None,
    price_unc: float = 0.0,
    weights: dict[str, float] = WEIGHTS,
) -> Comparison:
    """Score how much ``cand`` (engine trade) resembles ``ref`` (reference trade).

    price_offset: candidate-feed price minus reference-feed price (basis), if known.
    price_tol:    price unit to use when the reference has no stop (so no R).
    price_unc:    uncertainty of price_offset in price units (from basis anchors).
    """
    if cand.side != ref.side or cand.day != ref.day:
        why = "opposite side" if cand.side != ref.side else "different day"
        return Comparison(0.0, "different", 0.0, {}, [], [why])

    raw = {
        "time": _time_sim(cand, ref),
        "entry": _entry_sim(cand, ref, price_offset, price_tol, price_unc),
        "pd_array": _pd_sim(cand, ref),
        "liquidity": _liq_sim(cand, ref),
        "risk": _risk_sim(cand, ref),
        "tp1": _tp1_sim(cand, ref),
        "model": _model_sim(cand, ref),
        "market": _market_sim(cand, ref),
    }
    traits = {k: v for k, v in raw.items() if v is not None}
    total_w = sum(weights.values())
    used_w = sum(weights[k] for k in traits)
    score = sum(weights[k] * v for k, v in traits.items()) / used_w if used_w else 0.0
    verdict = "match" if score >= MATCH else "similar" if score >= SIMILAR else "different"

    shared, diffs = [f"same side ({ref.side})"], []
    for k, v in traits.items():
        (shared if v >= 0.7 else diffs).append(_describe(k, v, cand, ref))
    missing = [k for k, v in raw.items() if v is None]
    if missing:
        diffs.append("not comparable: " + ", ".join(missing))

    return Comparison(round(score, 3), verdict, round(used_w / total_w, 3),
                      {k: round(v, 3) for k, v in traits.items()}, shared, diffs)


def _describe(trait: str, v: float, cand: TradeSnapshot, ref: TradeSnapshot) -> str:
    detail = {
        "time": f"entry {cand.entry_time} vs {ref.entry_time or ref.entry_window}",
        "pd_array": f"{cand.pd_array_tf or ''} {cand.pd_array} vs {ref.pd_array_tf or ''} {ref.pd_array}",
        "liquidity": f"{sorted(cand.liquidity_taken)} vs {sorted(ref.liquidity_taken)}",
        "model": f"{cand.model} vs {ref.model}",
        "market": f"{cand.market} vs {ref.market}",
        "tp1": f"TP1 {cand.tp1_r():.1f}R vs {ref.tp1_r():.1f}R" if cand.tp1_r() is not None and ref.tp1_r() is not None else "TP1",
        "risk": f"risk {cand.risk:g} vs {ref.risk:g}" if cand.risk and ref.risk else "risk",
        "entry": "entry location",
    }[trait]
    return f"{trait} {v:.2f}: {detail}"


@dataclass
class DayReport:
    """Best engine match for each reference trade on one day."""

    best: dict[str, tuple[int | None, Comparison | None]]  # ref id -> (cand index, comparison)
    unmatched_candidates: list[int]                        # engine trades resembling no reference

    def found(self, level: str = "similar") -> list[str]:
        ok = {"match"} if level == "match" else {"match", "similar"}
        return [rid for rid, (_, c) in self.best.items() if c and c.verdict in ok]


def match_day(
    candidates: list[TradeSnapshot],
    references: Iterable[tuple[str, TradeSnapshot, dict]],
) -> DayReport:
    """For each reference (id, snapshot, compare-kwargs) find the most similar candidate.

    Engine trades that resemble no reference are not wrong — ICT didn't take
    every valid setup — they are listed for review.
    """
    best: dict[str, tuple[int | None, Comparison | None]] = {}
    used: set[int] = set()
    for rid, ref, kw in references:
        top: tuple[int | None, Comparison | None] = (None, None)
        for i, cand in enumerate(candidates):
            c = compare(cand, ref, **kw)
            if top[1] is None or c.score > top[1].score:
                top = (i, c)
        best[rid] = top
        if top[1] and top[1].verdict != "different":
            used.add(top[0])
    unmatched = [i for i in range(len(candidates)) if i not in used]
    return DayReport(best, unmatched)


def parse_time(s: str) -> time:
    return datetime.strptime(s, "%H:%M").time()
