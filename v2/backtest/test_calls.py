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


def test_inside_the_key_area_of_the_timeframe_above_the_way_looked_is_its_bias():
    """Price has retraced into an imbalance on the side of the bias above: the goal might be something nearby its way."""
    m = merged(a_read(side="bear"), above_read(side="bull", inside=(97, 101, "BISI")))
    assert (m["merge"], m["side"]) == ("key area", "bull")
    assert m["target"] == (105, "trade")
    assert m["undo"] == [(97, "close")]                                   # only a body close beyond the area undoes it
    against = merged(a_read(side="bear"), above_read(side="bull", inside=(97, 101, "SIBI")))
    assert against["merge"] == "momentum"                                  # an imbalance against the bias above is not its key area


def test_a_merged_call_is_followed_like_any_other_and_a_wick_through_the_area_undoes_nothing():
    m = merged(a_read(side="bear"), above_read(side="bull", inside=(97, 101, "BISI")))
    fine = walk([100, 96, 95, 99, 105.5])                                  # trades under the area, comes back, reaches the target
    assert resolve(m, fine, [(4 * 3600, 105.5)], 20)["outcome"] == "true"
    assert resolve(m, walk([100, 96, 95]), [(2 * 3600, 95.0)], 20)["outcome"] == "undone"       # a body closed under it


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
