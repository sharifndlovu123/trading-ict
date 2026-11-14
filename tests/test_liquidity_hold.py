"""Liquidity-hold pre-registration (research/preregistered-liquidity-hold-2026-11-15.md) on hand-built cases with known
answers: a turn that stops within 2 bp short of an untaken resting level counts (2022 model: trigger fallback and POI;
MMxM: purge); through the level, too far, already taken, unknown at the turn, or outside a window does not; no look-ahead."""

from datetime import date

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import Event, Level
from ict_engine.models import model_2022, model_mmxm
from ict_engine.models.model_2022 import held_level, hold
from tests.test_model_2022 import path_bars

NY = "America/New_York"
P = model_2022.Params(liquidity_hold_bp=2.0)        # 2 bp of 100 = 0.02


def ts(hm, d="2024-01-09"):
    return pd.Timestamp(f"{d} {hm}", tz=NY)


def day(turn_at="10:00", turn=100.03, dip=None):
    """00:00 → 12:00 from 110 down to ``turn`` (close; bar low = turn − 0.02) at ``turn_at``, back up to 106.
    ``dip``: (time, price) — an earlier excursion."""
    pts = [(ts("00:00"), 110.0)]
    if dip:
        pts += [(ts(dip[0]) - pd.Timedelta(minutes=20), 108.0), (ts(dip[0]), dip[1]), (ts(dip[0]) + pd.Timedelta(minutes=20), 108.0)]
    t = ts(turn_at)
    pts += [(t - pd.Timedelta(minutes=60), 105.0), (t, turn), (t + pd.Timedelta(minutes=30), 106.0), (ts("15:59"), 106.0)]
    b = path_bars([(str(a.tz_localize(None)), p) for a, p in pts], "2024-01-09 00:00", "2024-01-09 16:00")
    return b.assign(close_ts=b.index)


def pdl(price=100.0, at="00:00"):
    return Level("pdl", price, "low", ts(at))


def turn_of(d, start="08:00", end="10:20"):
    seg = d[(d.index >= ts(start)) & (d.index < ts(end))]
    return float(seg.low.min()), seg.low.idxmin()


def test_held_level_needs_a_turn_just_short_of_an_untaken_known_level():
    d = day()
    low, at = turn_of(d)
    assert abs(low - 100.01) < 1e-6
    assert held_level(low, at, True, [pdl()], d, ts("10:20"), 2.0).name == "pdl"            # 0.01 short of 100
    assert held_level(low, at, True, [pdl(100.02)], d, ts("10:20"), 2.0) is None           # traded through
    assert held_level(low, at, True, [pdl(99.98)], d, ts("10:20"), 2.0) is None            # 0.03 short > 2 bp
    assert held_level(low, at, True, [pdl(at="10:05")], d, ts("10:20"), 2.0) is None       # not known at the turn
    assert held_level(low, at, True, [Level("pdh", 100.0, "high", ts("00:00"))], d, ts("10:20"), 2.0) is None
    taken = day(dip=("03:00", 99.0))                                                         # PDL taken at 03:00
    assert held_level(low, at, True, [pdl()], taken, ts("10:20"), 2.0) is None


def test_short_side_mirror():
    b = path_bars([("2024-01-09 00:00", 90.0), ("2024-01-09 09:00", 95.0), ("2024-01-09 10:00", 99.97),
                   ("2024-01-09 10:30", 94.0), ("2024-01-09 15:59", 94.0)], "2024-01-09 00:00", "2024-01-09 16:00")
    hi = float(b[(b.index >= ts("08:00")) & (b.index < ts("10:20"))].high.max())
    at = b[(b.index >= ts("08:00")) & (b.index < ts("10:20"))].high.idxmax()
    assert held_level(hi, at, False, [Level("pdh", 100.0, "high", ts("00:00"))], b, ts("10:20"), 2.0).name == "pdh"


def mss(at="10:20", known="10:21"):
    return Event("mss", "1m", "bull", ts(known), ts(at), 104.0, 104.0)


def test_hold_event_stands_in_for_the_sweep_inside_a_window_only():
    h = hold(mss(), True, [pdl()], day(), P)
    assert h is not None and h.kind == "hold" and h.meta["level"] == "pdl"
    assert h.origin_ts == ts("10:00") and abs(h.bottom - 100.01) < 1e-6 and h.ts <= ts("10:21")
    assert hold(mss("12:50", "12:51"), True, [pdl()], day("12:30"), P) is None             # 12:30 is in no window
    assert model_2022._poi(h, True, [], day()) == "held pdl"


def test_hold_reads_no_bar_after_the_mss():
    d = day()
    cut = d[d.index < ts("10:20")]
    assert hold(mss(), True, [pdl()], d, P) == hold(mss(), True, [pdl()], cut, P)


def test_off_by_default():
    assert model_2022.Params().liquidity_hold_bp is None and model_mmxm.Params().liquidity_hold_bp is None
    assert "hold2bp" in P.variant


def test_mmxm_purge_accepts_a_low_that_held_just_above_pdl_or_an_older_swing():
    from ict_engine.models.model_mmxm import Curve, smr_purge
    from tests.test_model_mmxm import bars
    T = lambda hm: pd.Timestamp(f"2024-01-09 {hm}", tz=NY)
    frame = resample(bars(), "15m")
    ctx = type("C", (), {"levels": {"pdl": 95.0}})()
    curve = Curve(T("02:00"), T("04:00"), 103.1, 102.9, (101.5,), (T("05:45"),), (T("05:30"),))
    base, held = model_mmxm.Params(), model_mmxm.Params(liquidity_hold_bp=2.0)            # 2 bp of 95 = 0.019
    assert smr_purge(ctx, frame, [], True, 95.01, T("08:45"), curve, base) is None
    assert smr_purge(ctx, frame, [], True, 95.01, T("08:45"), curve, held) == "held pdl"
    assert smr_purge(ctx, frame, [], True, 95.03, T("08:45"), curve, held) is None
    assert smr_purge(ctx, frame, [], True, 94.5, T("08:45"), curve, held) == "ran pdl"     # a real purge still wins
    older = [Event("swing_low", "15m", "bull", pd.Timestamp("2024-01-08 20:30", tz=NY),
                   pd.Timestamp("2024-01-08 20:00", tz=NY), 96.0, 96.0)]
    assert smr_purge(ctx, frame, older, True, 96.015, T("08:45"), curve, held).startswith("held older 15m swing low")
    assert smr_purge(ctx, frame, older, True, 96.015, T("08:45"), curve, base) is None
