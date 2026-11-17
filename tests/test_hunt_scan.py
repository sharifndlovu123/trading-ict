"""The brain's eyes (research/scripts/hunt_scan.py) on hand-built candles.

Sharif 2026-11-17: his chart examples are illustrations, never exact values to find again. So nothing here uses a real
day's prices or times. Each idea is built by hand, and the same candles are read under different timeframe labels and
at a different price scale to show the code holds no favourite timeframe and no fixed number."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import hunt_scan as hs  # noqa: E402


def mk(rows, step=300, k=1.0):
    return [{"time": i * step, "open": o * k, "high": h * k, "low": lo * k, "close": c * k} for i, (o, h, lo, c) in enumerate(rows)]


QUIET = [(100, 101, 99, 100.5), (100.5, 101.5, 99.5, 100), (100, 101, 99, 100.6), (100.6, 101.4, 99.8, 100.2)] * 3   # twelve small two-way candles
GAP_UP = [(100, 101, 99.5, 100.8), (101, 106, 100.9, 105.8), (105.8, 107, 104, 106.5)]                            # leaves a bullish gap 101–104


@pytest.mark.parametrize("tf", ["1m", "15m", "4h"])
@pytest.mark.parametrize("k", [1.0, 0.01, 250.0])
def test_a_gap_is_read_by_how_its_own_timeframe_treats_it(tf, k):
    def state(after):
        c = mk(QUIET + GAP_UP + after, k=k)
        g = [x for x in hs.gaps(c, tf, c[-1]["close"]) if x["side"] == "bull" and abs(x["bottom"] - 101 * k) < 1e-6 * k + 1e-9]
        return g[0]["type"] if g else None
    assert state([(106.5, 107.5, 105, 107)]) == "gap.untouched"
    assert state([(106.5, 107, 103, 106)]) == "gap.wicked"                                   # a wick in, the body stays out
    assert state([(106.5, 107, 102.5, 103.5)]) == "gap.body_inside"                          # a body in, no close through
    assert state([(106.5, 107, 100, 100.5)]) == "gap.flipped"                                # a close through
    assert state([(106.5, 107, 100, 100.5), (100.5, 101.6, 100, 100.3)]) == "gap.flipped_retest"   # then tested from below, no close back
    assert state([(106.5, 107, 100, 100.5), (100.5, 106, 100, 105)]) is None                 # closed back through: it says nothing now


@pytest.mark.parametrize("tf", ["5m", "1h"])
def test_equal_highs_are_created_then_eaten_by_a_wick_or_by_a_body(tf):
    base = QUIET + [(100, 105, 99.8, 101), (101, 102, 100, 100.5), (100.5, 105.1, 100.2, 101), (101, 102, 100, 100.6), (100.6, 101.5, 100, 100.8)]
    c = mk(base)
    made = [x for x in hs.liquidity(c, tf, 100.8) if x["side"] == "highs" and x["count"] == 2]
    assert made and made[0]["type"] == "liq.created" and made[0]["top"] == 105.1
    wick = [x for x in hs.liquidity(mk(base + [(100.8, 106, 100.5, 102), (102, 103, 101, 102)]), tf, 102) if x["type"] == "liq.eaten" and x["top"] == 105.1]
    assert wick and wick[0]["closed_back"] is True                                            # taken, closed back under: a wick
    body = [x for x in hs.liquidity(mk(base + [(100.8, 107, 100.5, 106.5), (106.5, 107, 106, 106.6)]), tf, 106.6) if x["type"] == "liq.eaten" and x["top"] == 105.1]
    assert body and body[0]["closed_back"] is False                                           # taken and closed beyond: a body


def test_liquidity_built_against_a_higher_timeframes_gap_and_swept_into_it():
    gap = {"type": "gap.wicked", "tf": "4h", "side": "bear", "bottom": 105.2, "top": 109.0, "mid": 107.1}
    base = QUIET + [(100, 105, 99.8, 101), (101, 102, 100, 100.5), (100.5, 105.1, 100.2, 101), (101, 102, 100, 100.6), (100.6, 101.5, 100, 100.8)]
    liq = hs.liquidity(mk(base), "15m", 100.8)
    a = hs.against_areas(liq, [gap], {"15m": 2.0})
    assert [x["type"] for x in a] == ["liq.created_against_area"] and a[0]["area_tf"] == "4h"
    liq = hs.liquidity(mk(base + [(100.8, 106, 100.5, 102), (102, 103, 101, 102)]), "15m", 102)
    assert "liq.swept_into_area" in [x["type"] for x in hs.against_areas(liq, [gap], {"15m": 2.0})]
    assert hs.against_areas(liq, [{**gap, "tf": "5m"}], {"15m": 2.0}) == []                    # only a HIGHER timeframe's area counts
    assert hs.against_areas(liq, [{**gap, "type": "gap.flipped"}], {"15m": 2.0}) == []         # and only one that still stands


@pytest.mark.parametrize("tf", ["1m", "5m", "1D"])
@pytest.mark.parametrize("k", [1.0, 0.01])
def test_a_displacement_is_judged_against_its_own_timeframes_usual_candle(tf, k):
    c = mk(QUIET + [(100.2, 100.4, 92, 92.3), (92.3, 93, 91.5, 92), (92, 92.5, 91, 91.5)], k=k)   # one candle far larger than the rest, down
    d = hs.displacements(c, tf, [], [])
    kinds = [x["type"] for x in d]
    assert "displacement" in kinds and d[0]["side"] == "down" and d[0]["bos"] is True and d[0]["times_usual"] > 5
    assert "displacement.left_gap" in kinds                                                    # 99 (the low before) down to 93 (the high after)
    calm = mk(QUIET + [(100.2, 101, 99.4, 99.7), (99.7, 100.5, 99, 100), (100, 101, 99.5, 100.4)], k=k)
    assert hs.displacements(calm, tf, [], []) == []


def test_an_order_block_is_the_engulfed_candles_body_and_a_same_timeframe_close_inside_weakens_it():
    rows = QUIET + [(100, 104.5, 99.8, 104), (104, 104.2, 98, 98.5), (98.5, 99, 97, 97.5)]     # an up candle, engulfed by the next: a sell block 100–104
    def state(after):
        b = [x for x in hs.blocks(mk(rows + after + [(0, 0, 0, 0)]), "1h", 99) if x["side"] == "sell" and x["bottom"] == 100]
        return (b[0]["type"], b[0]["grade"]) if b else None
    assert state([]) == ("block.untouched", "clean")
    assert state([(97.5, 100.8, 97, 98)]) == ("block.wicked", "clean")
    assert state([(97.5, 102.5, 97, 98)]) == ("block.middle_hit", "clean")
    assert state([(97.5, 102.5, 97, 101)]) == ("block.weakened", "clean")                      # a candle of its own timeframe closed inside
    assert state([(97.5, 105, 97, 104.6)]) is None                                             # closed beyond its far edge: gone


def test_choppy_and_clean_are_told_apart_and_the_judgements_cover_all_five():
    up = mk([(100 + i, 101.2 + i, 99.9 + i, 101 + i) for i in range(30)])
    assert hs.conditions(up, "5m")["type"] == "cond.clean"
    assert hs.conditions(mk(QUIET * 3), "5m")["type"] == "cond.choppy"
    doc = {"now": "Tue 2026-01-06 09:42", "assets": {"X": {"last": up[-1]["close"], "adr": 50.0, "candles": {"5m": up, "1D": mk([(90, 131, 89, 130)] * 8, step=86400)}}}}
    j = hs.judgements(hs.scan(doc, "X"), up[-1]["close"])
    assert set(j) == {"choppy", "bias", "areas", "displacement", "volatile", "liquidity"} and "5m clean" in j["choppy"][0]


def test_equal_highs_belong_to_one_sub_group_not_to_a_price_level():
    """Sharif 2026-11-17: "EQHs are relative to a sub group, not for an area... always relative to the group"."""
    peak = [(100, 105, 99.8, 101), (101, 102, 100, 100.5)]
    near = mk(QUIET + peak + peak + QUIET[:4])                       # two highs at 105, a couple of candles apart: one group
    g = [x for x in hs.liquidity(near, "1D", 100.5) if x["side"] == "highs" and x["top"] == 105]
    assert len(g) == 1 and g[0]["count"] == 2 and g[0]["t_end"] <= near[-1]["time"]
    far = mk(QUIET + peak + QUIET * 4 + peak + QUIET[:4])           # the same two highs, dozens of candles apart: two stories, no group
    assert [x for x in hs.liquidity(far, "1D", 100.5) if x["side"] == "highs" and x["top"] == 105] == []
    broken = mk(QUIET + peak + [(100.5, 108, 100, 101)] + peak + QUIET[:4])    # a higher high between them: the first was already taken
    assert [x for x in hs.liquidity(broken, "1D", 100.5) if x["top"] == 105 and x["count"] == 2] == []


def test_only_what_is_near_price_now_is_kept():
    peak = [(100, 105, 99.8, 101), (101, 102, 100, 100.5)]
    c = mk(QUIET + peak + peak + QUIET[:4])
    assert [x for x in hs.liquidity(c, "5m", 100.5, reach=10) if x["top"] == 105]           # 4.5 away: kept
    assert not [x for x in hs.liquidity(c, "5m", 100.5, reach=2) if x["top"] == 105]         # farther than we are looking: dropped
    assert not [x for x in hs.gaps(mk(QUIET + GAP_UP + [(106.5, 107.5, 105, 107)]), "5m", 140.0, reach=5)]


def test_an_earlier_group_being_swept_says_nothing_about_a_later_group_at_the_same_price():
    """Sharif: "the highs that were EQHs in April were swept: it has nothing to do with July's EQHs"."""
    peak = [(100, 105, 99.8, 101), (101, 102, 100, 100.5)]
    sweep = [(100.5, 106.5, 100.2, 101)]                             # takes the first pair of highs, closes back
    c = mk(QUIET + peak + peak + sweep + QUIET * 2 + peak + peak + QUIET[:4])
    g = [x for x in hs.liquidity(c, "1D", 100.5) if x["side"] == "highs" and x["top"] == 105]
    assert [x["type"] for x in g] == ["liq.created"] and g[0]["count"] == 2          # only the later group is resting; the earlier one is old news
    assert g[0]["t0"] > c[len(QUIET) + 5]["time"]                                    # and it is the later stretch of candles


def test_bias_is_the_structure_rule_he_taught_not_the_last_two_swings():
    """Bias comes from `context.weekly_structure_state` (protected intermediate-term level; a close, not a wick, turns
    it), read the same way on any timeframe. Here a hand-built fall, a rally that stays under the protected high (a
    shift, not a change), then a close through it (the change)."""
    import math
    rows, px = [], 600.0
    for i in range(160):                                             # a falling market with pullbacks of uneven size
        px += -2.0 + 6 * math.sin(i / 3.1) + 3 * math.sin(i / 1.3)
        rows.append((px + 1, px + 4, px - 4, px - 1))
    fall = mk(rows, step=3600)
    b = hs.bias(fall, "1h")
    assert b["type"] == "bias.bear" and b["guard"] > fall[-1]["close"] and "protected lower high" in b["text"]
    assert hs.bias(fall, "1D")["type"] == "bias.bear"                 # the same candles under another timeframe's name: the same reading
    last = fall[-1]["close"]
    under = fall + mk([(last + k, last + k + 3, last + k - 3, last + k + 1) for k in range(1, 6)], step=3600)   # higher highs, still under the guard
    assert under[-1]["high"] < b["guard"] and hs.bias(under, "1h")["type"] == "bias.bear"
    g = b["guard"]
    broke = fall + mk([(g - 5, g + 60, g - 6, g + 55), (g + 55, g + 70, g + 50, g + 65)], step=3600)             # a strong close above the protected high
    assert hs.bias(broke, "1h")["type"] == "bias.bull"
    wick = fall + mk([(g - 30, g + 20, g - 32, g - 28), (g - 28, g - 20, g - 35, g - 30)], step=3600)             # only a wick above it, the close back under
    assert hs.bias(wick, "1h")["type"] == "bias.bear"
