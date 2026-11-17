"""Equal lows swept → push → the gap's 50% (research/scripts/ndog_eql.py) on hand-built candles."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import ndog_eql as ne  # noqa: E402


def session15(lows, close_back_at=None):
    """Flat 15m candles around 100 with the given lows; highs 101, closes 100."""
    n = len(lows)
    L = np.array(lows, float)
    return np.full(n, 100.0), np.full(n, 101.0), L, np.full(n, 100.0)


def test_sweep_of_needs_two_lows_an_hour_apart_for_equal_lows():
    #            0    1    2     3    4    5    6    7     8    9   10   11   12
    lows = [99, 99, 98.0, 99, 99, 99, 99, 98.1, 99, 99, 97.0, 99, 99]          # 98.0 and 98.1, five candles apart
    O, H, L, C = session15(lows)
    sw = ne.sweep_of(O, H, L, C, target=120.0, adr=10.0, need_eql=True)
    assert sw == {"k": 10, "level": 98.0, "top": 98.1}
    lows[7] = 99                                                               # one low only → no equal lows
    O, H, L, C = session15(lows)
    assert ne.sweep_of(O, H, L, C, 120.0, 10.0, True) is None
    assert ne.sweep_of(O, H, L, C, 120.0, 10.0, False)["level"] == 98.0        # … but it is still a swept swing low


def test_sweep_of_stops_when_the_opening_gap_closes_first():
    lows = [99, 99, 98.0, 99, 99, 99, 99, 98.1, 99, 99, 97.0, 99, 99]
    O, H, L, C = session15(lows)
    H[4] = 121.0
    assert ne.sweep_of(O, H, L, C, 120.0, 10.0, True) is None


def test_fvg_entry_buys_the_50_percent_of_the_push_gap_and_lists_three_stops():
    # 1m bars, 5 per candle. Candle 0 sweeps to 95; candle 1 high 99; candle 2 displaces; candle 3 low 103 → a 5m gap
    # 99 → 103 (50% = 101), above the pool top 98; the retrace fills at 101.
    n = 40
    o = np.full(n, 100.0); h = np.full(n, 100.5); lo = np.full(n, 99.5); c = np.full(n, 100.0)
    lo[0:5] = 95.0; h[0:5] = 97.0
    lo[5:10] = 96.0; h[5:10] = 99.0
    lo[10:15] = 99.5; h[10:15] = 106.0
    lo[15:20] = 103.0; h[15:20] = 106.0
    lo[20:] = 103.5; h[20:] = 105.0; o[20:] = 104.0
    lo[26] = 100.8; o[26] = 103.0                                              # the retrace
    x = ne.fvg_entry(h, lo, c, o, None, 0, n, top=98.0, target=120.0, adr=10.0)
    assert x["j"] == 26 and x["entry"] == pytest.approx(101.0)
    assert x["stops"] == {"gap bottom": 99.0, "gap's first candle": 96.0, "sweep low": 95.0}
    h[22] = 121.0                                                              # the opening gap closed before the retrace
    assert ne.fvg_entry(h, lo, c, o, None, 0, n, 98.0, 120.0, 10.0) is None


def test_find_requires_a_displacement_when_asked():
    lows = [99, 99, 98.0, 99, 99, 99, 99, 98.1, 99, 99, 97.0, 99, 99]
    O, H, L, C = session15(lows)
    C[10] = 97.5; C[11] = 100.0                                                # candle 11 closes back above 98.1, ordinary range
    x = ne.find(O, H, L, C, 120.0, 10.0, True, False)
    assert x["k"] == 10 and x["m"] == 11 and x["entry"] == 100.0 and x["stop"] == 97.0 and not x["displacement"]
    assert ne.find(O, H, L, C, 120.0, 10.0, True, True) is None
    H[11] = 106.0; C[11] = 105.5                                               # now a wide candle closing near its high
    assert ne.find(O, H, L, C, 120.0, 10.0, True, True)["displacement"]
