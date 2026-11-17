"""Alt-liquidity as Sharif defined each type (alt-liquidity.md). Hand-built candles with known answers."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from alt_liquidity import fvgs, in_use, is_draw, opening_gaps, volume_imbalances

NY = ZoneInfo("America/New_York")


def mk(rows, step=3600, k=1.0):
    return [{"time": i * step, "open": o * k, "high": h * k, "low": lo * k, "close": c * k} for i, (o, h, lo, c) in enumerate(rows)]


UP = [(100, 101, 99, 100.5), (100.5, 106, 100.4, 105.5), (105.5, 107, 103, 106)]        # first high 101, third low 103: a gap 101-103
DOWN = [(100, 101, 99, 99.5), (99.5, 99.6, 94, 94.5), (94.5, 97, 93, 94)]              # first low 99, third high 97: a gap 97-99


def test_a_bisi_is_the_gap_left_by_an_up_close_candle_and_a_sibi_by_a_down_close_candle():
    b = fvgs(mk(UP))
    assert [(x["type"], x["bottom"], x["top"], x["state"]) for x in b] == [("BISI", 101, 103, "untouched")]
    s = fvgs(mk(DOWN))
    assert [(x["type"], x["bottom"], x["top"], x["state"]) for x in s] == [("SIBI", 97, 99, "untouched")]


def test_no_gap_when_the_first_and_third_candles_overlap():
    assert fvgs(mk([(100, 101, 99, 100.5), (100.5, 106, 100.4, 105.5), (105.5, 107, 100.9, 106)])) == []


def test_partly_filled_then_filled_and_no_guarantee_it_fills():
    part = fvgs(mk(UP + [(106, 106.5, 102, 104)]))[0]
    assert part["state"] == "partly" and part["filled_at"] is None
    full = fvgs(mk(UP + [(106, 106.5, 100.5, 104)]))[0]                 # a wick across the whole gap, close back above it
    assert full["state"] == "filled" and full["closed_through_at"] is None and full["ifvg"] is None
    assert fvgs(mk(UP + [(106, 110, 105, 109)]))[0]["state"] == "untouched"   # price left and never came back


def test_an_ifvg_is_an_earlier_gap_price_traded_through_which_may_then_act_the_other_way():
    c = mk(UP + [(106, 106.5, 99, 99.5)])                               # closes below the BISI
    g = fvgs(c)[0]
    assert g["closed_through_at"] == c[-1]["time"] and g["ifvg"] == "resistance"
    c = mk(DOWN + [(94, 101, 93.5, 100.5)])                             # closes above the SIBI
    assert fvgs(c)[0]["ifvg"] == "support"


def test_a_volume_imbalance_is_bodies_apart_with_wicks_overlapping():
    v = volume_imbalances(mk([(100, 102, 99, 101), (101.5, 104, 100.8, 103)]))     # bodies 100-101 and 101.5-103; the wicks overlap
    assert [(x["direction"], x["bottom"], x["top"]) for x in v] == [("up", 101, 101.5)]
    v = volume_imbalances(mk([(100, 101, 98, 99), (98.4, 99.2, 96, 97)]))
    assert [(x["direction"], x["bottom"], x["top"]) for x in v] == [("down", 98.4, 99)]
    assert volume_imbalances(mk([(100, 102, 99, 101), (103, 105, 102.5, 104)])) == []    # the wicks do not overlap: a full gap, not a volume imbalance
    assert volume_imbalances(mk([(100, 102, 99, 101), (101, 104, 100, 103)])) == []       # the bodies touch


def test_a_gap_is_a_draw_only_when_unfilled_and_price_is_already_moving_toward_it():
    above = {"bottom": 110, "top": 112, "state": "untouched"}
    assert is_draw(above, price=100, moving="up") and not is_draw(above, price=100, moving="down")
    below = {"bottom": 90, "top": 92, "state": "partly"}
    assert is_draw(below, price=100, moving="down") and not is_draw(below, price=100, moving="up")
    assert not is_draw({**above, "state": "filled"}, price=100, moving="up")


def at(day, hm):
    """A New York clock time as epoch seconds."""
    y, m, d = (int(x) for x in day.split("-"))
    h, mi = (int(x) for x in hm.split(":"))
    return int(datetime(y, m, d, h, mi, tzinfo=NY).timestamp())


def bar(day, hm, o, c):
    return {"time": at(day, hm), "open": o, "high": max(o, c), "low": min(o, c), "close": c}        # no wicks: the prices say it all


# Friday 2 Jan 2032 ... a made-up week; only the clock matters
WEEK = [bar("2032-01-02", "16:58", 100, 101), bar("2032-01-02", "16:59", 101, 102),                 # Friday's last minutes: close 102
        bar("2032-01-04", "18:00", 105, 105.5), bar("2032-01-04", "18:01", 105.5, 106),              # Sunday 6 p.m. open 105: NWOG 102-105
        bar("2032-01-05", "16:59", 106, 108),                                                        # Monday 4:59 p.m. close 108
        bar("2032-01-05", "18:00", 107, 107.2), bar("2032-01-05", "18:01", 107.2, 107.5)]            # 6 p.m. reopen 107: NDOG 107-108


def test_the_nwog_is_fridays_close_to_sundays_open_and_the_ndog_the_5pm_close_to_the_6pm_reopen():
    g = opening_gaps(WEEK)
    assert [(x["type"], x["bottom"], x["top"], x["direction"]) for x in g] == [("NWOG", 102, 105, "up"), ("NDOG", 107, 108, "down")]
    assert g[0]["close"] == 102 and g[0]["open"] == 105 and g[0]["size"] == 3 and g[1]["size"] == 1


def test_no_opening_gap_inside_a_session_or_when_the_reopen_is_at_the_close():
    inside = [bar("2032-01-05", "10:00", 100, 101), bar("2032-01-05", "10:01", 103, 104)]
    assert opening_gaps(inside) == []
    flat = [bar("2032-01-05", "16:59", 106, 108), bar("2032-01-05", "18:00", 108, 108.2)]
    assert opening_gaps(flat) == []


def test_they_normally_fill_and_a_big_one_can_fill_in_portions():
    g = opening_gaps(WEEK + [bar("2032-01-05", "18:30", 107.5, 107.9)])[1]              # reaches into the NDOG, not across
    assert g["state"] == "partly"
    g = opening_gaps(WEEK + [bar("2032-01-05", "18:30", 107.5, 108.2)])[1]
    assert g["state"] == "filled" and g["filled_at"] == at("2032-01-05", "18:30")


def test_how_long_each_is_used():
    nwog, ndog = opening_gaps(WEEK)
    assert in_use(nwog, at("2032-01-08", "11:00"))                       # Thursday of the same week
    assert not in_use(nwog, at("2032-01-11", "18:30"))                   # the next week has opened
    assert in_use(ndog, at("2032-01-08", "11:00"))                       # unfilled: the current week
    assert not in_use(ndog, at("2032-01-12", "11:00"))
    filled = {**ndog, "filled_at": at("2032-01-06", "09:00")}            # filled on Tuesday's trading day
    assert in_use(filled, at("2032-01-06", "15:00"))                     # still of use through that day
    assert not in_use(filled, at("2032-01-07", "10:00"))                 # not for the rest of the week
    assert not in_use(ndog, at("2032-01-05", "12:00"))                   # before it existed


@pytest.mark.parametrize("k", [0.0001, 1.0, 300.0])
@pytest.mark.parametrize("step", [60, 86400])
def test_the_same_shape_reads_the_same_at_any_price_scale_and_on_any_timeframe(k, step):
    g = fvgs(mk(UP, step=step, k=k))
    assert g[0]["type"] == "BISI" and g[0]["bottom"] == pytest.approx(101 * k) and g[0]["top"] == pytest.approx(103 * k)


def test_nothing_is_known_before_it_happened():
    c = mk(UP + [(106, 106.5, 99, 99.5)])
    assert fvgs(c[:2]) == []                                             # no gap until the third candle is in
    g = fvgs(c)[0]
    assert g["closed_through_at"] > g["t"] and fvgs(c[:3])[0]["ifvg"] is None


def test_only_fridays_close_to_sundays_open_is_the_nwog():
    """A weekday with no trading in between still gives an NDOG: the NWOG is Friday to Sunday, by his definition."""
    skipped_day = [bar("2032-01-06", "16:59", 100, 101), bar("2032-01-07", "18:00", 103, 103.5)]      # Tuesday's close, Wednesday evening's reopen
    assert [x["type"] for x in opening_gaps(skipped_day)] == ["NDOG"]
    assert [x["type"] for x in opening_gaps(WEEK)] == ["NWOG", "NDOG"]


def test_a_feed_with_no_459_print_uses_the_last_print_before_5pm():
    """My choice, not his: some instruments stop printing earlier in the afternoon."""
    early = [bar("2032-01-05", "16:00", 100, 101), bar("2032-01-05", "18:00", 102, 102.5)]
    g = opening_gaps(early)
    assert [(x["type"], x["bottom"], x["top"]) for x in g] == [("NDOG", 101, 102)]


def test_a_gap_whose_middle_candle_did_not_close_its_way_is_not_named():
    """His words: a BISI is formed by an up-close candle, a SIBI by a down-close candle. (Leaving the odd one unnamed is my choice.)"""
    odd = mk([(100, 101, 99, 100.5), (106, 106.5, 104, 104.5), (104.5, 107, 103, 106)])            # a gap above 101, but the middle candle closed down
    assert fvgs(odd) == []
