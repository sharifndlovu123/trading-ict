"""The tools backtest: a call is made from what the tools see, and it comes true, is undone or stays unresolved when it
should. Hand-built candles and reads only; no price, date or instrument from any real chart."""
import pytest

from calls import calls, merged, read, resolve


def bar(t, o, h, lo, c):
    return {"time": t, "open": o, "high": h, "low": lo, "close": c}


def a_read(k=1.0, side="bull"):
    """What the tools might see: price in the middle, liquidity and an imbalance each side, the bias's two levels."""
    bull = side == "bull"
    return {"side": side, "price": 100 * k, "near": 0.5 * k, "behind": (90 if bull else 110) * k, "ahead": (120 if bull else 80) * k,
            "buyside": 110 * k, "sellside": 95 * k, "imbalance_above": (105 * k, 107 * k, "BISI"), "imbalance_below": (96 * k, 98 * k, "SIBI")}


def walk(prices, step=3600, start=0, wick=0.0):
    """One candle per step from each price to the next."""
    out = []
    for i, (a, b) in enumerate(zip(prices, prices[1:])):
        up = b >= a                                   # the candle going into a turn carries the longer wick, so the turn is one candle
        out.append(bar(start + i * step, a, max(a, b) + (wick if up else wick / 2), min(a, b) - (wick / 2 if up else wick), b))
    return out


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
def test_a_bull_read_calls_the_buyside_the_level_ahead_and_the_imbalance_above(k):
    by = {c["kind"]: c for c in calls(a_read(k))}
    assert by["liquidity"]["target"] == (110 * k, "eat")
    assert by["liquidity"]["undo"] == [(95 * k, "eat"), (90 * k, "close")]
    assert by["bias"]["target"] == (120 * k, "close") and by["bias"]["undo"] == [(90 * k, "close")]
    assert by["imbalance"]["target"] == (105 * k, "trade")


def test_a_bear_read_is_the_mirror():
    by = {c["kind"]: c for c in calls(a_read(side="bear"))}
    assert by["liquidity"]["target"] == (95, "eat") and by["liquidity"]["undo"] == [(110, "eat"), (110, "close")]
    assert by["bias"]["target"] == (80, "close") and by["imbalance"]["target"] == (98, "trade")


def test_each_call_says_which_was_nearer_the_target_or_what_undoes_it():
    """The nearer level usually goes first whatever the bias says, so every result has to be split by this."""
    by = {c["kind"]: c for c in calls(a_read())}
    assert by["liquidity"]["nearer"] == "undo"            # the sellside is 5 away, the buyside 10
    assert by["bias"]["nearer"] == "undo"                 # the level behind is 10 away, the level ahead 20
    assert by["imbalance"]["nearer"] == "target"          # the imbalance is 5 away, the level behind 10


def test_no_call_is_made_about_something_that_is_not_there():
    r = a_read() | {"buyside": None, "imbalance_above": None}
    assert [c["kind"] for c in calls(r)] == ["bias"]
    r = a_read() | {"sellside": None}                      # nothing resting on the other side: only the level behind undoes it
    assert {c["kind"]: c for c in calls(r)}["liquidity"]["undo"] == [(90, "close")]


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
@pytest.mark.parametrize("step", [3600, 14400, 86400])
def test_liquidity_is_reached_only_when_price_goes_clearly_past_it(k, step):
    call = {c["kind"]: c for c in calls(a_read(k))}["liquidity"]
    touch = walk([100 * k, 104 * k, 110.3 * k, 106 * k], step)          # a little over: within "very close", so not eaten
    assert resolve(call, touch, [], 20)["outcome"] == "open"
    past = walk([100 * k, 104 * k, 111 * k], step)
    assert resolve(call, past, [], 20) == {"outcome": "true", "at": step, "candles": 0}


def test_the_other_side_being_eaten_first_undoes_the_call():
    call = {c["kind"]: c for c in calls(a_read())}["liquidity"]
    assert resolve(call, walk([100, 97, 94, 112]), [], 20)["outcome"] == "undone"


def test_a_wick_under_the_level_behind_undoes_nothing_but_a_body_close_does():
    call = {c["kind"]: c for c in calls(a_read() | {"sellside": None})}["liquidity"]
    fine = walk([100, 92, 89, 92, 96])                                   # trades under 90 and comes back
    assert resolve(call, fine, [(4 * 3600, 96.0)], 20)["outcome"] == "open"          # the candle of its own timeframe closed above
    assert resolve(call, fine, [(4 * 3600, 89.5)], 20)["outcome"] == "undone"        # the same move, but the body closed under


def test_the_bias_call_is_decided_by_body_closes_only():
    call = {c["kind"]: c for c in calls(a_read())}["bias"]
    fine = walk([100, 110, 121, 115])                                    # trades above the level ahead
    assert resolve(call, fine, [(3 * 3600, 115.0)], 20)["outcome"] == "open"
    assert resolve(call, fine, [(3 * 3600, 121.5)], 20)["outcome"] == "true"


def test_an_imbalance_is_reached_when_price_trades_into_it():
    call = {c["kind"]: c for c in calls(a_read())}["imbalance"]
    assert resolve(call, walk([100, 103, 105]), [], 20)["outcome"] == "true"
    assert resolve(call, walk([100, 103, 104.9]), [], 20)["outcome"] == "open"


def test_when_both_are_reached_inside_one_candle_the_order_is_not_claimed():
    call = {c["kind"]: c for c in calls(a_read())}["liquidity"]
    both = [bar(0, 100, 111, 94, 100)]
    assert resolve(call, both, [], 20)["outcome"] == "same candle"


def test_a_call_is_left_unresolved_after_its_number_of_candles_and_open_if_the_data_ends():
    call = {c["kind"]: c for c in calls(a_read())}["liquidity"]
    quiet = walk([100, 101] * 30)                                        # nothing happens
    two_closes = [(10 * 3600, 100.0), (20 * 3600, 100.0)]
    assert resolve(call, quiet, two_closes, horizon=2) == {"outcome": "unresolved", "at": 20 * 3600, "candles": 2}
    assert resolve(call, quiet, two_closes, horizon=5)["outcome"] == "open"


def test_what_happened_to_a_call_is_not_known_before_it_happened():
    """No look-ahead: an outcome never changes when later candles are added, and it is not known one candle early."""
    call = {c["kind"]: c for c in calls(a_read())}["liquidity"]
    fine = walk([100, 104, 108, 111, 90, 80])
    whole = resolve(call, fine, [], 20)
    assert whole["outcome"] == "true" and resolve(call, fine[:3], [], 20) == whole
    assert resolve(call, fine[:2], [], 20)["outcome"] == "open"


# ---- the read itself, on candles: a rise that leaves a high, a pullback, then price in the middle
def a_chart(k=1.0, step=3600):
    up = walk([p * k for p in (100, 106, 110, 107, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140)], step, wick=0.3 * k)
    down = walk([140 * k, 136 * k, 132 * k, 128 * k, 124 * k, 120 * k], step, start=len(up) * step, wick=0.3 * k)
    back = walk([120 * k, 124 * k, 128 * k, 130 * k], step, start=(len(up) + len(down)) * step, wick=0.3 * k)
    return up + down + back


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
@pytest.mark.parametrize("step", [3600, 14400, 86400])
def test_the_read_finds_the_resting_high_above_price(k, step):
    c = a_chart(k, step)
    r = read(c)
    assert r is not None and r["buyside"] == pytest.approx(140.3 * k) and r["price"] == pytest.approx(130 * k)


def test_a_level_the_forming_candle_has_already_taken_is_not_called():
    """Relative to now: the candles that have closed still show the high as resting, but since they closed price has
    gone clearly past it. It is used up, so no call is made on it, and price now is where that move has reached."""
    c = a_chart()
    since = walk([130, 138, 143, 141], start=len(c) * 3600)
    r = read(c, forming=since)
    assert r["buyside"] is None and r["price"] == 141


def test_the_forming_candle_changes_price_now_but_never_the_bias_or_its_levels():
    """A candle still forming is never read as a candle of its timeframe: what it has done so far moves "price now"
    and can use up a level, but the bias, the level behind and the level ahead come from closed candles only."""
    c = a_chart()
    quiet = walk([130, 131, 129], start=len(c) * 3600)
    plain, with_forming = read(c), read(c, forming=quiet)
    assert {k: with_forming[k] for k in ("side", "behind", "ahead")} == {k: plain[k] for k in ("side", "behind", "ahead")}
    assert with_forming["price"] == 129 and with_forming["buyside"] == plain["buyside"]


# ---- two timeframes read together (his correction, 20 Nov 2026: "there's a mix of timeframes to provide a result")
def above_read(k=1.0, side="bull", **change):
    """The timeframe above: its own liquidity and imbalances lie farther out than this timeframe's."""
    bull = side == "bull"
    return {"side": side, "price": 100 * k, "near": 2 * k, "behind": (60 if bull else 140) * k, "ahead": (150 if bull else 50) * k,
            "buyside": 130 * k, "sellside": 80 * k, "imbalance_above": (125 * k, 128 * k, "SIBI"), "imbalance_below": (84 * k, 88 * k, "BISI"),
            "inside": None} | change


def test_no_merged_call_without_a_timeframe_above():
    assert merged(a_read(), None) is None


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
def test_when_the_two_agree_the_target_is_whatever_is_nearest_that_way_on_either_timeframe(k):
    m = merged(a_read(k), above_read(k))
    assert (m["merge"], m["side"]) == ("agree", "bull")
    assert m["target"] == (105 * k, "trade") and (m["what"], m["whose"]) == ("BISI", "own")       # the imbalance, nearer than the buyside
    near_above = merged(a_read(k), above_read(k, imbalance_above=(102 * k, 103 * k, "SIBI")))
    assert near_above["target"] == (102 * k, "trade") and near_above["whose"] == "above"            # the timeframe above's is nearer still


def test_when_they_disagree_the_momentum_of_this_timeframe_is_the_way_looked():
    """Disagreeing is normal: the lower timeframe's selling inside a bull timeframe above is looked at, not ignored."""
    m = merged(a_read(side="bear"), above_read(side="bull"))
    assert (m["merge"], m["side"]) == ("momentum", "bear")
    assert m["target"] == (98, "trade")                                   # nearest below price, not the far buyside above
    assert m["undo"] == [(110, "eat"), (110, "close")]                    # nearest liquidity the other way, and this timeframe's level behind


def test_inside_a_higher_timeframes_area_and_against_it_nothing_is_called():
    """His: "if we are inside the area, watch what happens to build confidence for a buy or sell"."""
    m = merged(a_read(side="bear"), above_read(side="bull", inside=(97, 101, "BISI")))
    assert (m["merge"], m["target"], m["area_i"]) == ("watch", None, 0)
    against = merged(a_read(side="bear"), above_read(side="bull", inside=(97, 101, "SIBI")))
    assert against["merge"] == "momentum"                                  # an imbalance against the bias above is not its area


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
def test_inside_the_area_once_this_timeframe_has_turned_its_way_the_call_is_from_the_area(k):
    m = merged(a_read(k, side="bull"), above_read(k, side="bull", inside=(97 * k, 101 * k, "BISI")))
    assert (m["merge"], m["side"], m["area_i"]) == ("from area", "bull", 0)
    assert m["target"] == (105 * k, "trade")                               # the nearest thing that way, as before


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
def test_outside_the_area_and_against_the_higher_bias_the_call_goes_into_the_area(k):
    """His: "if we are just above the interesting area, sell into it". The target is the area's near edge, not a
    small nearer thing of this timeframe."""
    m = merged(a_read(k, side="bear"), above_read(k, side="bull", area=(84 * k, 88 * k, "BISI")))
    assert (m["merge"], m["side"]) == ("into area", "bear")
    assert m["target"] == (88 * k, "trade") and (m["what"], m["whose"], m["whose_i"], m["area_i"]) == ("BISI", "above", 0, 0)
    behind_price = merged(a_read(k, side="bear"), above_read(k, side="bull", area=(120 * k, 125 * k, "BISI")))
    assert behind_price["merge"] == "momentum"                             # an area the move is not heading for is not a target
    wrong_side = merged(a_read(k, side="bear"), above_read(k, side="bull", area=(84 * k, 88 * k, "SIBI")))
    assert wrong_side["merge"] == "momentum"
    agreeing = merged(a_read(k, side="bull"), above_read(k, side="bull", area=(84 * k, 88 * k, "BISI")))
    assert agreeing["merge"] == "agree"                                    # nothing is retracing against the timeframe above


def test_with_areas_on_two_timeframes_the_highest_one_inside_is_watched_and_the_nearest_one_ahead_is_the_target():
    top = above_read(side="bull", inside=(90, 102, "BISI"))
    mid = above_read(side="bull", inside=(97, 101, "BISI"))
    assert merged(a_read(side="bear"), [top, mid])["area_i"] == 0
    assert merged(a_read(side="bear"), [above_read(side="bull"), mid])["area_i"] == 1
    far, near = above_read(side="bull", area=(70, 75, "BISI")), above_read(side="bull", area=(84, 88, "BISI"))
    m = merged(a_read(side="bear"), [far, near])
    assert (m["merge"], m["target"], m["area_i"]) == ("into area", (88, "trade"), 1)


def test_a_close_of_the_areas_own_timeframe_is_judged_on_that_timeframes_candles_only():
    """His (23 Nov 2026): "a close through that imbalance, relative to the timeframe of the break and the imbalance
    itself"; wicks, and closes of a lower timeframe, are not a break."""
    m = {"side": "bull", "near": 0.5, "target": (105, "trade"), "undo": [(97, "close area")]}
    fine = walk([100, 96, 95, 99, 105.5])                                  # trades under the area, comes back, reaches the target
    own_closes = [(2 * 3600, 96.0), (3 * 3600, 95.0)]                      # lower-timeframe bodies close under the area
    assert resolve(m, fine, own_closes, 20, [])["outcome"] == "true"       # ...and the area still stands
    assert resolve(m, fine, own_closes, 20, [(3 * 3600, 95.0)])["outcome"] == "undone"       # its own timeframe closed under it
    assert resolve(m, fine, own_closes, 20, [(3 * 3600, 99.0)])["outcome"] == "true"         # closed back inside: a wick


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
def test_the_whole_ladder_above_is_read_top_to_bottom(k):
    """Every timeframe above has its say. They are passed highest first; one with no read is None."""
    top, mid = above_read(k, side="bull"), above_read(k, side="bull")
    assert merged(a_read(k), [top, mid])["merge"] == "agree"
    assert merged(a_read(k), [None, mid])["merge"] == "agree"             # a timeframe with no read yet has no say
    assert merged(a_read(k), [None, None]) is None
    split = merged(a_read(k), [above_read(k, side="bear"), mid])          # the one directly above agrees, a higher one does not
    assert (split["merge"], split["side"]) == ("momentum", "bull")
    far = above_read(k, side="bull", imbalance_above=(101 * k, 102 * k, "SIBI"))
    m = merged(a_read(k), [far, mid])
    assert m["target"] == (101 * k, "trade") and (m["whose"], m["whose_i"]) == ("above", 0)      # the nearest thing, on whichever timeframe


def test_no_merged_call_when_nothing_lies_that_way():
    r = a_read() | {"buyside": None, "imbalance_above": None}
    assert merged(r, above_read(buyside=None, imbalance_above=None)) is None


def test_the_read_says_when_price_is_inside_an_unfilled_fvg():
    """Three candles leave a gap between the first one's high and the third one's low; price comes back into it."""
    c = walk([100, 101, 102, 101, 100, 101, 102, 103, 104, 105, 104, 103, 104, 105, 106], wick=0.2)
    t = len(c) * 3600
    c += [bar(t, 106, 107, 105.8, 107), bar(t + 3600, 107, 112, 107, 112), bar(t + 7200, 112, 113, 110, 112.5),
          bar(t + 10800, 112.5, 112.6, 108.5, 109)]
    r = read(c)
    assert r is not None and r["inside"] == (107, 110, "BISI")
    assert read(c[:-1])["inside"] is None                                 # one candle earlier price had not come back into it


@pytest.mark.parametrize("k", [1.0, 0.01, 250.0])
def test_a_zone_stands_through_wicks_and_ends_when_a_candle_of_its_timeframe_closes_beyond_it(k):
    """Price trades right through the gap and closes back inside: it still stands. A body closing beyond it ends it."""
    c = walk([100, 101, 102, 101, 100, 101, 102, 103, 104, 105, 104, 103, 104, 105, 106], wick=0.2)
    t = len(c) * 3600
    c += [bar(t, 106, 107, 105.8, 107), bar(t + 3600, 107, 112, 107, 112), bar(t + 7200, 112, 113, 110, 112.5),
          bar(t + 10800, 112.5, 112.6, 106, 109)]                         # a wick under the whole gap, a close inside it
    c = [{**x, **{f: x[f] * k for f in ("open", "high", "low", "close")}} for x in c]
    assert read(c)["inside"] == (107 * k, 110 * k, "BISI")
    after = c + [bar(t + 14400, 109 * k, 109.5 * k, 105 * k, 106 * k), bar(t + 18000, 106 * k, 108.5 * k, 105.5 * k, 108 * k)]
    r = read(after)                                                        # a body closed under it, then price came back up into it
    assert r is not None and r["inside"] is None


# ---- did the bias play out (his way of judging a call, 23 Nov 2026)
from calls import played_out  # noqa: E402


@pytest.mark.parametrize("k, step", [(1.0, 3600), (0.0001, 900), (300.0, 14400)])
def test_the_bias_plays_out_when_the_area_is_reached_by_whatever_route(k, step):
    """Price drops well under where the call was made, closing lower candle after candle, then reaches the area. No
    candle closed beyond the level behind, so the bias never changed: "our bias still played out"."""
    fine = walk([100 * k, 96 * k, 92 * k, 90 * k, 95 * k, 101 * k, 106 * k], step=step)
    closes = [(x["time"] + step, x["close"]) for x in fine]
    got = played_out("bull", (105 * k, "trade"), 85 * k, 0.5 * k, fine, 0, closes, 0)
    assert got == {"played": "true", "played_at": fine[-1]["time"]}


def test_a_change_of_bias_ends_the_idea_and_a_wick_through_the_level_does_not():
    under = walk([100, 96, 90, 84, 83])                                    # a body closes under the level behind
    assert played_out("bull", (105, "trade"), 85, 0.5, under, 0, [(x["time"] + 3600, x["close"]) for x in under], 0)["played"] == "ended"
    wick = [bar(0, 100, 100, 99, 99.5), bar(3600, 99.5, 100, 80, 98), bar(7200, 98, 106, 98, 105.5)]     # trades under it, closes back above
    assert played_out("bull", (105, "trade"), 85, 0.5, wick, 0, [(x["time"] + 3600, x["close"]) for x in wick], 0)["played"] == "true"
    mirror = walk([100, 104, 110, 116, 117])
    assert played_out("bear", (95, "trade"), 115, 0.5, mirror, 0, [(x["time"] + 3600, x["close"]) for x in mirror], 0)["played"] == "ended"


def test_the_change_is_judged_on_the_closes_of_the_stated_timeframe_only_and_nothing_is_known_early():
    fine = walk([100, 96, 90, 84, 83, 90, 106])                            # lower-timeframe bodies close under the level and come back
    higher = [(7 * 3600, 106.0)]                                           # the stated timeframe's one candle closes after all of it
    assert played_out("bull", (105, "trade"), 85, 0.5, fine, 0, higher, 0)["played"] == "true"
    assert played_out("bull", (105, "trade"), 85, 0.5, fine[:4], 0, higher, 0) == {"played": "open", "played_at": None}
    assert played_out("bull", (105, "trade"), 85, 0.5, fine, 5, higher, 0)["played"] == "true"   # followed from a later moment


@pytest.mark.parametrize("k", [1.0, 0.01, 250.0])
def test_the_read_names_the_standing_area_price_would_retrace_into(k):
    """Bull: the nearest BISI under price that no candle has closed beyond. Once price is back inside it, it is
    ``inside`` and no longer ahead."""
    c = walk([100, 101, 102, 101, 100, 101, 102, 103, 104, 105, 104, 103, 104, 105, 106], wick=0.2)
    t = len(c) * 3600
    c += [bar(t, 106, 107, 105.8, 107), bar(t + 3600, 107, 112, 107, 112), bar(t + 7200, 112, 113, 110, 112.5),
          bar(t + 10800, 112.5, 114, 112, 113.5)]
    scaled = lambda cs: [{**x, **{f: x[f] * k for f in ("open", "high", "low", "close")}} for x in cs]      # noqa: E731
    r = read(scaled(c))
    assert r["side"] == "bull"
    assert r["area"][2] == "BISI" and r["area"][:2] == pytest.approx((107 * k, 110 * k)) and r["inside"] is None
    back = read(scaled(c + [bar(t + 14400, 113.5, 113.6, 108.5, 109)]))
    assert back["inside"][:2] == pytest.approx((107 * k, 110 * k))
    assert back["area"] is None or back["area"][1] <= 107 * k * 1.000001     # the area ahead is now a lower one, if any


# ---- a bias followed as a story (his, 23 Nov 2026: "it's not really hit or miss")
from calls import story  # noqa: E402


def cl(fine, step=3600):
    return [(x["time"] + step, x["close"]) for x in fine]


@pytest.mark.parametrize("k", [1.0, 0.0001, 300.0])
def test_a_bias_that_breaks_its_level_with_no_zone_failing_went_straight(k):
    fine = walk([100 * k, 97 * k, 99 * k, 104 * k, 111 * k])              # dips into the zone, holds, breaks the level
    got = story("bull", 110 * k, 85 * k, [("z", 95 * k, 98 * k)], fine, 0, cl(fine), 0, {"z": (cl(fine), 0)})
    assert (got["story"], got["reached"], got["failed"]) == ("straight", 1, 0)
    assert [e[1] for e in got["events"]] == ["reached", "level broken"]


def test_when_the_first_zone_fails_and_price_goes_from_a_deeper_one_it_is_told_that_way():
    """His: "if that interesting zone fails… what else is interesting below"; "there's another area price could buy
    from". The first zone is closed through on its own timeframe; the deeper one holds; the level then breaks."""
    fine = walk([100, 97, 93, 90, 96, 104, 111])
    got = story("bull", 110, 85, [("z", 95, 98), ("z", 88, 91)], fine, 0, cl(fine), 0, {"z": (cl(fine), 0)})
    assert (got["story"], got["reached"], got["failed"]) == ("deeper", 2, 1)
    assert [e[1] for e in got["events"]] == ["reached", "closed through", "reached", "level broken"]


def test_a_zone_fails_only_on_a_close_of_its_own_timeframe():
    fine = walk([100, 97, 93, 96, 104, 111])                               # lower-timeframe bodies close under the zone and come back
    higher = [(6 * 3600, 111.0)]                                           # the zone's own timeframe closes once, after all of it
    got = story("bull", 110, 85, [("up", 95, 98)], fine, 0, cl(fine), 0, {"up": (higher, 0)})
    assert (got["story"], got["failed"]) == ("straight", 0)


def test_a_flipped_bias_says_whether_an_area_on_its_side_still_stood():
    fine = walk([100, 96, 90, 84, 83])
    higher = [(9 * 3600, 83.0)]                                            # the higher timeframe has not closed yet
    left = story("bull", 110, 85, [("up", 80, 92)], fine, 0, cl(fine), 0, {"up": (higher, 0)})
    assert left["story"] == "flipped, areas left" and left["events"][-1][1] == "bias flipped"
    none = story("bull", 110, 85, [("z", 95, 98)], fine, 0, cl(fine), 0, {"z": (cl(fine), 0)})
    assert none["story"] == "flipped"
    mirror = walk([100, 104, 110, 116, 117])
    assert story("bear", 90, 115, [], mirror, 0, cl(mirror), 0, {})["story"] == "flipped"


def test_nothing_about_a_story_is_known_before_it_happens():
    fine = walk([100, 97, 99, 104, 111])
    early = story("bull", 110, 85, [("z", 95, 98)], fine[:3], 0, cl(fine[:3]), 0, {"z": (cl(fine[:3]), 0)})
    assert (early["story"], early["story_at"]) == ("open", None) and [e[1] for e in early["events"]] == ["reached"]
