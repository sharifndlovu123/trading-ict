"""Score daily-bias rules by hit rate (bias is a strategy: scored, never traded).

For every trading day D the rule's call (made from daily bars completed before D's
context — the same cut ``build_context`` uses, as_of = 00:00 NY of D) is compared
with what D did between 18:00 NY the evening before and 16:00 NY:

    bull_hit   price reached PDH before PDL (or PDH and never PDL)
    bear_hit   mirror
    none       neither PDH nor PDL reached
    ambiguous  both first reached inside the same 1m bar (order unknown)

A bull call is correct on a bull_hit day, a bear call on a bear_hit day. Neutral calls
and days without a directional outcome (none / ambiguous) are counted separately and
left out of the hit rate.

CLI:
    uv run python -m ict_engine.eval.bias US100 2023-01-01 2024-06-30
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.clock import trading_day
from ict_engine.concepts.context import BIAS_RULES, completed_daily

NY = "America/New_York"
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri")
OUTCOME_END = time(16)


def _ts(d: date, t: time) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d, t), tz=NY)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (95% by default)."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def day_outcome(bars_1m: pd.DataFrame, day: date, pdh: float, pdl: float) -> str:
    """What ``day`` did versus the previous day's range (see module doc)."""
    w = bars_1m[(bars_1m.index >= _ts(day - timedelta(days=1), time(18)))
                & (bars_1m.index < _ts(day, OUTCOME_END))]
    up, dn = w.index[w.high >= pdh], w.index[w.low <= pdl]
    if up.empty and dn.empty:
        return "none"
    if dn.empty or (not up.empty and up[0] < dn[0]):
        return "bull_hit"
    if up.empty or dn[0] < up[0]:
        return "bear_hit"
    return "ambiguous"


@dataclass(frozen=True)
class DayRecord:
    day: date
    outcome: str
    calls: dict[str, str]          # rule name -> bull | bear | neutral


def label_days(bars_1m: pd.DataFrame, min_history: int = 20) -> list[DayRecord]:
    """One record per trading day that has ``min_history`` completed days before it."""
    daily = resample(bars_1m, "1d")
    days = sorted(set(trading_day(daily.index)))
    out = []
    for d in days:
        past = completed_daily(daily, d)
        if len(past) < min_history:
            continue
        prev = past.iloc[-1]
        outcome = day_outcome(bars_1m, d, float(prev.high), float(prev.low))
        out.append(DayRecord(d, outcome, {name: rule(past)[0] for name, rule in BIAS_RULES.items()}))
    return out


@dataclass
class RuleScore:
    rule: str
    calls: int = 0                 # directional calls on days with a directional outcome
    correct: int = 0
    bull_calls: int = 0
    bear_calls: int = 0
    neutral: int = 0               # neutral calls (all days)
    no_outcome: int = 0            # directional calls on none/ambiguous days
    by_weekday: dict[str, list[int]] = field(default_factory=lambda: {w: [0, 0] for w in WEEKDAYS})

    @property
    def hit_rate(self) -> float:
        return self.correct / self.calls if self.calls else float("nan")

    def expected(self, base_bull: float) -> float:
        """Hit rate of random calls with this rule's bull/bear mix (the edge baseline)."""
        if not self.calls:
            return float("nan")
        return (self.bull_calls * base_bull + self.bear_calls * (1 - base_bull)) / self.calls


def score(records: list[DayRecord], rule: str) -> RuleScore:
    s = RuleScore(rule)
    for r in records:
        call = r.calls[rule]
        if call == "neutral":
            s.neutral += 1
            continue
        if r.outcome not in ("bull_hit", "bear_hit"):
            s.no_outcome += 1
            continue
        s.calls += 1
        s.bull_calls += call == "bull"
        s.bear_calls += call == "bear"
        hit = (call == "bull") == (r.outcome == "bull_hit")
        s.correct += hit
        wd = r.day.weekday()
        if wd < 5:
            s.by_weekday[WEEKDAYS[wd]][0] += hit
            s.by_weekday[WEEKDAYS[wd]][1] += 1
    return s


def base_rate(records: list[DayRecord]) -> tuple[int, int]:
    """(bull_hit days, days with a directional outcome)."""
    n = sum(r.outcome in ("bull_hit", "bear_hit") for r in records)
    return sum(r.outcome == "bull_hit" for r in records), n


def report(records: list[DayRecord], title: str = "") -> str:
    k, n = base_rate(records)
    base = k / n if n else float("nan")
    counts = {o: sum(r.outcome == o for r in records) for o in ("bull_hit", "bear_hit", "none", "ambiguous")}
    lo, hi = wilson(k, n)
    lines = [
        f"{title}  days={len(records)}  " + "  ".join(f"{o}={c}" for o, c in counts.items()),
        f"base rate (bull_hit share) = {base:.1%}  [{lo:.1%}, {hi:.1%}]   always-bull hit rate = {base:.1%}",
        "",
        f"{'rule':<10}{'calls':>6}{'bull/bear':>11}{'correct':>8}{'hit':>7}{'wilson95':>17}"
        f"{'expect':>8}{'edge':>7}{'neutral':>8}{'no-out':>7}",
    ]
    scores = [score(records, r) for r in BIAS_RULES]
    always = RuleScore("always_bull", calls=n, correct=k, bull_calls=n)
    for s in scores + [always]:
        lo, hi = wilson(s.correct, s.calls)
        exp = s.expected(base)
        lines.append(
            f"{s.rule:<10}{s.calls:>6}{f'{s.bull_calls}/{s.bear_calls}':>11}{s.correct:>8}{s.hit_rate:>7.1%}"
            f"{f'[{lo:.1%}, {hi:.1%}]':>17}{exp:>8.1%}{s.hit_rate - exp:>+7.1%}{s.neutral:>8}{s.no_outcome:>7}")
    lines += ["", "hit rate by weekday (correct/calls)",
              f"{'rule':<10}" + "".join(f"{w:>12}" for w in WEEKDAYS)]
    for s in scores:
        cells = "".join(f"{(f'{c/t:.0%} {c}/{t}' if t else '-'):>12}" for c, t in s.by_weekday.values())
        lines.append(f"{s.rule:<10}{cells}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    from ict_engine.data.dukascopy import load

    ap = argparse.ArgumentParser(description="Hit rate of every daily-bias rule.")
    ap.add_argument("asset")
    ap.add_argument("start", type=date.fromisoformat)
    ap.add_argument("end", type=date.fromisoformat)
    a = ap.parse_args(argv)
    bars = load(a.asset, a.start, a.end)
    print(report(label_days(bars), f"{a.asset} {a.start}..{a.end}"))


if __name__ == "__main__":
    main()
