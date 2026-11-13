from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from ict_engine.eval import compare, load_cases
from ict_engine.eval.basis import Anchor, Offset, estimate_offset, level
from ict_engine.eval.cases import ReferenceCase

NY = "America/New_York"
CASES_FILE = "tests/cases/ict_live_exec.yaml"


def _bars():
    """Synthetic 1m bars Mon 2024-01-08 18:00 → Tue 2024-01-09 12:00, flat at 100
    with a few planted levels."""
    idx = pd.date_range("2024-01-07 18:00", "2024-01-09 12:00", freq="1min", tz=NY)
    df = pd.DataFrame({"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0}, index=idx)
    df.loc[pd.Timestamp("2024-01-08 10:00", tz=NY), "high"] = 110.0   # PDH (Mon session)
    df.loc[pd.Timestamp("2024-01-08 21:30", tz=NY), "high"] = 105.0   # Asia high
    df.loc[pd.Timestamp("2024-01-09 05:01", tz=NY), "high"] = 103.0   # "05:00 high", 1 min late
    return df


def test_levels():
    b, d = _bars(), date(2024, 1, 9)
    assert level(b, d, "pdh") == 110.0
    assert level(b, d, "asia_high") == 105.0
    assert level(b, d, "high@05:00") == 103.0     # ±3 min slack finds the swing
    assert level(b, d, "low@05:00") == 99.5


def test_offset_is_median_of_anchor_differences():
    b, d = _bars(), date(2024, 1, 9)
    # reference chart is 20 points higher than our feed on every level
    off = estimate_offset(b, d, [Anchor("pdh", 130.0), Anchor("asia_high", 125.0), Anchor("high@05:00", 123.0)])
    assert off.value == -20.0 and off.n == 3 and off.spread == 0.0


def test_unknown_anchor_rejected():
    with pytest.raises(ValueError):
        level(_bars(), date(2024, 1, 9), "midnight_high")


def test_case_kwargs_use_offset_and_uncertainty():
    case = next(c for c in load_cases(CASES_FILE) if c.id == "2024-01-09-nq-macro-pdh")
    kw = case.compare_kwargs(Offset(-157.4, [0.4, -0.4], 2))
    assert kw["price_offset"] == -157.4 and kw["price_unc"] >= 2.0     # floor = half the NQ default
    # a CFD trade at the shifted entry is a match
    t = case.trade
    from dataclasses import replace
    cfd = replace(t, entry_price=t.entry_price - 157.4, stop=t.stop - 157.4, tp1=t.tp1 - 157.4)
    assert compare(cfd, t, **kw).verdict == "match"


def test_no_anchors_on_another_feed_drops_entry_trait():
    case = next(c for c in load_cases(CASES_FILE) if c.id == "2023-11-30-nq-housing-short")
    kw = case.compare_kwargs(Offset(None, [], 0))
    assert kw["weights"]["entry"] == 0.0


# --- real data (skipped until `fetch` has been run) ------------------------------

def _real_bars(market, day):
    from ict_engine.data.dukascopy import load
    from ict_engine.data.instruments import get
    try:
        return load(get(market).name, day - timedelta(days=4), day)
    except FileNotFoundError:
        pytest.skip("Dukascopy data not downloaded")


@pytest.mark.parametrize("case", [c for c in load_cases(CASES_FILE)
                                  if c.anchors and c.confidence != "low" and (c.trade.entry_time or c.trade.entry_window)],
                         ids=lambda c: c.id)
def test_shifted_reference_entry_lands_in_cfd_bars(case):
    """Anchors are independent of the entry; after shifting, ICT's entry should sit
    inside (or within 1R / 3 pts of) the CFD bars around the entry time."""
    t = case.trade
    bars = _real_bars(t.market, t.day)
    off = estimate_offset(bars, t.day, list(case.anchors))
    lo, hi = t.entry_window or (t.entry_time, t.entry_time)
    a = pd.Timestamp(datetime.combine(t.day, lo), tz=NY) - pd.Timedelta(minutes=3)
    b = pd.Timestamp(datetime.combine(t.day, hi), tz=NY) + pd.Timedelta(minutes=3)
    w = bars[(bars.index >= a) & (bars.index <= b)]
    shifted = t.entry_price + off.value
    miss = max(0.0, w["low"].min() - shifted, shifted - w["high"].max())
    assert miss <= max(3.0, t.risk or 0), f"miss {miss:.2f}"
