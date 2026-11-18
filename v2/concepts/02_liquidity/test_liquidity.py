"""Liquidity as Sharif taught it (lesson.md). Hand-built candles with known answers; no real chart's values."""
import pytest

from liquidity import eaten_since, equal, equal_sets, highs_lows, near_from_view, previous_period, resting


def mk(rows, step=3600, k=1.0):
    """(open, high, low, close) rows into candles."""
    return [{"time": i * step, "open": o * k, "high": h * k, "low": lo * k, "close": c * k} for i, (o, h, lo, c) in enumerate(rows)]


#        0 up        1 HIGH 110   2 down       3 LOW 95     4 up        5 HIGH 108   6 down      7 last
BASE = [(100, 104, 99, 103), (103, 110, 102, 106), (106, 107, 98, 99), (99, 100, 95, 97), (97, 105, 96, 104),
        (104, 108, 103, 105), (105, 106, 101, 102), (102, 103, 100, 101)]


def test_old_highs_and_lows_are_found_and_each_says_whether_it_was_eaten():
    got = {(x["side"], x["price"]): x["eaten_at"] for x in highs_lows(mk(BASE))}
    assert got == {("high", 110): None, ("low", 95): None, ("high", 108): None}


def test_a_high_is_eaten_when_a_later_candle_trades_above_it_a_wick_is_enough():
    c = mk(BASE + [(101, 109, 100, 102)])                              # trades above 108, closes back under: eaten all the same
    got = {(x["side"], x["price"]): x["eaten_at"] for x in highs_lows(c)}
    assert got[("high", 108)] == c[-1]["time"] and got[("high", 110)] is None


def test_what_is_resting_is_only_what_was_not_eaten_however_far_it_is():
    far = mk([(500, 520, 495, 500), (500, 600, 499, 510), (510, 515, 400, 405)] + [(405, 410, 100 + i, 104 + i) for i in range(3)] + BASE)
    r = resting(far)
    assert 600 in [x["price"] for x in r["buyside"]]                    # far above and old, but never eaten: it stays
    c = mk(BASE + [(101, 109, 100, 102)])
    assert [x["price"] for x in resting(c)["buyside"]] == [110]          # 108 was eaten: gone, though it is the nearer one
    assert [x["price"] for x in resting(mk(BASE))["buyside"]] == [108, 110]   # nearest first
    assert [x["price"] for x in resting(mk(BASE))["sellside"]] == [95]


def test_what_the_present_move_has_eaten():
    c = mk(BASE + [(101, 109, 100, 102), (102, 103, 94, 95)])
    got = eaten_since(c, since=c[-2]["time"])
    assert [(x["side"], x["price"]) for x in got] == [("low", 95), ("high", 108)]      # newest first
    assert eaten_since(c, since=c[-1]["time"] + 1) == []


def test_equal_highs_are_highs_very_close_by_and_how_close_is_the_callers_call():
    lv = [{"side": "high", "price": p, "t": i} for i, p in enumerate([110.0, 110.4, 113.0, 118.0, 118.2, 118.5])]
    lv += [{"side": "low", "price": p, "t": 9} for p in (90.0, 90.3)]
    g = equal(lv, near=0.5)
    assert [(x["side"], x["bottom"], x["top"], x["count"]) for x in g] == [("high", 110.0, 110.4, 2), ("high", 118.0, 118.5, 3), ("low", 90.0, 90.3, 2)]
    assert equal(lv, near=0.1) == []                                     # a stricter eye sees none
    assert [x["count"] for x in equal(lv, near=3.0) if x["side"] == "high"] == [3, 3]   # a looser eye joins 113 to the lower pair


def test_highs_and_lows_are_never_grouped_together():
    lv = [{"side": "high", "price": 100.0, "t": 0}, {"side": "low", "price": 100.1, "t": 1}]
    assert equal(lv, near=1.0) == []


def test_previous_day_or_week_high_and_low_left_uneaten_or_not():
    days = mk([(100, 110, 95, 105), (105, 120, 101, 118)], step=86400)
    today = mk([(118, 119, 112, 113), (113, 121, 111, 115)], step=3600)
    p = previous_period(days, today)
    assert p["high"]["price"] == 120 and p["high"]["eaten_at"] == today[1]["time"]
    assert p["low"]["price"] == 101 and p["low"]["eaten_at"] is None
    assert previous_period(days, [])["high"]["eaten_at"] is None         # nothing traded yet: both rest


@pytest.mark.parametrize("k", [0.0001, 1.0, 300.0])
@pytest.mark.parametrize("step", [60, 3600, 604800])
def test_the_same_shape_reads_the_same_at_any_price_scale_and_on_any_timeframe(k, step):
    r = resting(mk(BASE, step=step, k=k))
    assert [x["price"] for x in r["buyside"]] == pytest.approx([108 * k, 110 * k]) and [x["price"] for x in r["sellside"]] == pytest.approx([95 * k])


def test_nothing_is_known_before_it_happened():
    c = mk(BASE + [(101, 109, 100, 102)])
    assert all(x["eaten_at"] is None or x["eaten_at"] > x["t"] for x in highs_lows(c))
    assert ("high", 108) not in {(x["side"], x["price"]) for x in highs_lows(c[:6])}    # the high is not a high until the next candle is in


# a high, then a second high a hair above it, then a candle clearly past both, then a new pair of highs up there
SET = [(100, 104, 99, 103), (103, 110, 102, 106), (106, 107, 100, 101), (101, 110.3, 100, 104), (104, 105, 99, 100),
       (100, 121, 99, 118), (118, 120.8, 112, 114), (114, 116, 110, 111)]


def test_a_high_that_lands_a_hair_above_an_earlier_one_joins_it_and_does_not_eat_it():
    """His correction: the second high "couldn't have been eaten, it's still relatively close"; the two "created EQH"."""
    c = mk(SET[:5])
    literal = {x["price"]: x["eaten_at"] for x in highs_lows(c) if x["side"] == "high"}
    assert literal[110] == c[3]["time"]                                   # read to the letter, a hair above counts as eaten: wrong
    close = [x for x in highs_lows(c, near=0.5) if x["side"] == "high" and x["eaten_at"] is None]
    assert [x["price"] for x in close] == [110, 110.3]                    # read his way, both rest
    assert [(g["bottom"], g["top"], g["count"]) for g in equal(close, near=0.5)] == [(110, 110.3, 2)]     # and they are one set of equal highs


def test_what_eats_the_set_is_the_high_that_goes_clearly_past_it_and_a_new_set_can_form_there():
    c = mk(SET)
    hs = {x["price"]: x["eaten_at"] for x in highs_lows(c, near=0.5) if x["side"] == "high"}
    assert hs[110] == c[5]["time"] and hs[110.3] == c[5]["time"]          # both taken by the same candle: the set is eaten as one
    left = resting(c, near=0.5)["buyside"]
    assert [x["price"] for x in left] == [121]                            # the eaten set is gone from what is resting
    c2 = mk(SET + [(111, 120.9, 110, 112), (112, 113, 108, 109)])          # a second high up there, a hair under the first
    top = resting(c2, near=0.5)["buyside"]
    assert [x["price"] for x in top] == [120.9, 121] and equal(top, near=0.5)[0]["count"] == 2     # its own small set


def test_the_same_holds_for_lows():
    c = mk([(100, 101, 96, 97), (97, 98, 90, 93), (93, 99, 92, 98), (98, 99, 89.8, 95), (95, 100, 94, 99), (99, 100, 80, 82), (82, 85, 81, 84)])
    assert [x["price"] for x in resting(c[:5], near=0.5)["sellside"]] == [90, 89.8]
    assert all(x["eaten_at"] == c[5]["time"] for x in highs_lows(c, near=0.5) if x["side"] == "low" and x["price"] > 85)


def test_very_close_is_a_share_of_the_height_of_the_picture_being_looked_at():
    view = mk([(100, 150, 90, 120), (120, 130, 50, 60)])                  # the picture is 100 tall (50 to 150)
    assert near_from_view(view, 0.01) == pytest.approx(1.0)
    assert near_from_view(view, 0.0) == 0 and near_from_view([], 0.01) == 0
    tall = mk([(100, 150, 90, 120), (120, 130, 50, 60)], k=40)             # the same picture at forty times the price
    assert near_from_view(tall, 0.01) == pytest.approx(40.0)              # the eye's tolerance grows with it


def test_with_no_share_given_his_own_setting_is_used():
    from liquidity import HIS_EYE
    view = mk([(100, 150, 90, 120), (120, 130, 50, 60)])                  # 100 tall
    assert near_from_view(view) == pytest.approx(100 * HIS_EYE) and 0 < HIS_EYE < 0.05


def test_the_same_highs_are_equal_from_far_and_separate_up_close():
    c = mk(SET[:5])                                                        # two highs 0.3 apart; the stretch is about 11 tall
    far = equal_sets(c, near_from_view(c, 0.05))                           # an eye that cannot tell 5% of the picture apart
    assert [(g["side"], g["count"]) for g in far] == [("high", 2)]
    close_up = equal_sets(c, near_from_view(c, 0.01))                      # a sharper eye: 0.3 is more than 1% of the picture
    assert close_up == []


@pytest.mark.parametrize("k", [0.0001, 1.0, 300.0])
def test_the_eye_gives_the_same_sets_at_any_price_scale(k):
    c = mk(SET[:5], k=k)
    g = equal_sets(c, near_from_view(c, 0.05))
    assert len(g) == 1 and g[0]["count"] == 2 and g[0]["top"] == pytest.approx(110.3 * k)
