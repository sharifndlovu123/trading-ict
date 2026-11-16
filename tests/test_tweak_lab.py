"""Tweak lab (research/scripts/tweak_lab.py) on hand-built bars with known answers: the replay (stop first on the
same bar, flat at the end), a wider stop that survives, a nearer target, and a deeper entry that fills or is missed."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from tweak_lab import TWEAKS, apply, replay  # noqa: E402

# a long from 100, stop 98 (risk 2), TP 104: dips to 97, then runs to 105
HI = np.array([100.5, 99.0, 101.0, 105.0])
LO = np.array([99.5, 97.0, 98.5, 100.5])
CL = np.array([100.0, 98.0, 100.8, 104.5])


def test_as_traded_is_stopped_and_a_wider_stop_survives():
    assert replay(HI, LO, CL, True, 100, 98, 104) == (-1.0, False, True)
    s2, t2, shift = apply(TWEAKS["stop × 2, TP1 price kept"], True, 100, 98, 104, adr=20)
    assert (s2, t2, shift) == (96, 104, 0)
    r, win, stopped = replay(HI, LO, CL, True, 100, s2, t2)
    assert win and r == pytest.approx(1.0)                         # 4 points on a 4-point risk


def test_target_in_r_and_adr_floor():
    s2, t2, _ = apply(TWEAKS["TP1 at 1 R"], True, 100, 98, 104, adr=20)
    assert (s2, t2) == (98, 102)
    s3, t3, _ = apply(TWEAKS["stop ≥ 0.15 ADR, TP1 at 1 R"], True, 100, 98, 104, adr=20)
    assert (s3, t3) == (97, 103)                                   # 0.15 × 20 = 3 points
    short = apply(TWEAKS["stop × 1.5, TP1 price kept"], False, 100, 102, 96, adr=20)
    assert short[:2] == (103, 96)


def test_deeper_entry_fills_or_is_missed():
    s2, t2, shift = apply(TWEAKS["entry 0.5 R deeper (same stop, same TP1)"], True, 100, 98, 104, adr=20)
    assert replay(HI, LO, CL, True, 100, s2, t2, shift) == (-1.0, False, True)   # fills at 99, still stopped at 98
    wide = replay(HI, LO, CL, True, 100, 96, 104, 0.5)             # entry 98, stop 96: survives 97, TP 104 = +3 R
    assert wide[1] and wide[0] == pytest.approx(3.0)
    assert replay(np.array([101.0, 105.0]), np.array([99.6, 100.5]), np.array([100.5, 104.0]), True, 100, 98, 104, 0.5) is None


def test_same_bar_stop_and_target_is_the_stop_and_open_trades_close_flat():
    assert replay(np.array([105.0]), np.array([97.0]), np.array([100.0]), True, 100, 98, 104)[2]
    r, win, stopped = replay(np.array([101.0, 102.0]), np.array([99.0, 100.0]), np.array([100.5, 101.0]), True, 100, 98, 104)
    assert not win and not stopped and r == pytest.approx(0.5)


def test_level_tweaks_use_the_known_levels():
    from tweak_levels import tweak
    # a long from 100, stop 98, TP 104, ADR 20; a 4h bullish FVG 96.5–99 holds the stop; a pool at 97.5 under it
    L = {"arrays": [("4h", "fvg", 96.5, 99.0)], "pools_stop": [97.5, 80.0], "pools_tp": [102.5, 110.0]}
    assert tweak("stop beyond array", True, 100, 98, 104, 20, L) == (100, 96.5 - 0.4, 104, False)
    assert tweak("stop beyond pool", True, 100, 98, 104, 20, L) == (100, 97.5 - 0.4, 104, False)
    assert tweak("skip: pool near the stop", True, 100, 98, 104, 20, L) is None
    assert tweak("TP1 front-run the first pool", True, 100, 98, 104, 20, L) == (100, 98, 102.5 - 0.2, False)
    assert tweak("entry at the HTF array", True, 100, 98, 104, 20, L) == (99.0, 96.5 - 0.4, 104, True)
    assert tweak("skip: no HTF array at the entry", True, 100, 98, 104, 20, L) == (100, 98, 104, False)   # within 0.1 ADR
    none = {"arrays": [], "pools_stop": [], "pools_tp": []}
    for n in ("stop beyond array", "stop beyond pool", "skip: pool near the stop", "TP1 front-run the first pool", "entry at the HTF array"):
        assert tweak(n, True, 100, 98, 104, 20, none) == (100, 98, 104, False)        # nothing known → unchanged
    assert tweak("skip: no HTF array at the entry", True, 100, 98, 104, 20, none) is None
    # the short mirror
    Ls = {"arrays": [("1h", "fvg", 101.0, 103.5)], "pools_stop": [102.5], "pools_tp": [97.5]}
    assert tweak("stop beyond array", False, 100, 102, 96, 20, Ls) == (100, 103.5 + 0.4, 96, False)
    assert tweak("TP1 front-run the first pool", False, 100, 102, 96, 20, Ls) == (100, 102, 97.5 + 0.2, False)
