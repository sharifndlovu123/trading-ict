"""Bias the way Sharif re-taught it on 17 Nov 2026: the break, the level behind it (a close through it is the change),
the level ahead. Hand-built candles only, with known answers; no prices or dates from any real chart.

What these cover: a break sets the bias; a new swing the other way is not a change (both directions); failing at the
level ahead changes nothing; breaking it moves the level behind up; a close through the level behind is the change and
a wick is not; nothing is known before it happened; a swing of the timeframe being read is not significant by itself;
the candle still forming is never read. There is no "weak close = range" rule with a margin: he taught "level below:
break = change", and "range" stays a hand judgement until he teaches how he decides it."""
import pytest

from bias import bias_levels, swings

N = 5                                    # candles of the timeframe read per candle of the timeframe above


def path(points, step=3600, k=1.0, wick=0.5):
    """Candles walking through (price, candles to get there) waypoints."""
    out, px, t = [], points[0][0], 0
    for target, n in points[1:]:
        for i in range(1, n + 1):
            nxt = px + (target - px) / (n - i + 1)
            out.append({"time": t, "open": px * k, "high": (max(px, nxt) + wick) * k, "low": (min(px, nxt) - wick) * k, "close": nxt * k})
            px, t = nxt, t + step
    return out


def above(c, n=N):
    """The timeframe above: every ``n`` candles made into one."""
    return [{"time": g[0]["time"], "open": g[0]["open"], "high": max(x["high"] for x in g), "low": min(x["low"] for x in g), "close": g[-1]["close"]}
            for g in (c[i:i + n] for i in range(0, len(c) - len(c) % n, n))]


def read(points, **kw):
    c = path(points, **kw)
    return bias_levels(c, above(c))


RISE = [(100, 0), (100, 3), (140, 20), (120, 15), (170, 25)]   # 3 flat candles so the turns fall inside a candle of the timeframe above                 # a high, a pullback, a close through the high


def test_the_break_sets_the_bias_and_the_pullback_it_was_built_on_is_the_level_behind():
    r = read(RISE)
    assert r["side"] == "bull" and r["events"][0]["kind"] == "first"
    assert r["break"]["price"] == pytest.approx(140.5)              # the high that was closed through
    assert r["change"]["price"] == pytest.approx(119.5)             # the low of the pullback before the break


def test_a_new_swing_the_other_way_is_not_a_change():
    """A fall that breaks the small lows of this timeframe but closes above the level behind the bias: still bull."""
    r = read(RISE + [(150, 15), (160, 6), (130, 12), (138, 5), (124, 8)])
    assert r["side"] == "bull" and r["change"]["price"] == pytest.approx(119.5)
    assert [e["kind"] for e in r["events"]] == ["first"]


def test_failing_at_the_level_ahead_changes_nothing():
    r = read(RISE + [(150, 15), (168, 12), (152, 12), (169, 12), (155, 10)])
    assert r["side"] == "bull" and r["change"]["price"] == pytest.approx(119.5)
    assert r["ahead"]["price"] == pytest.approx(170.5)              # tried twice, never closed above


def test_breaking_the_level_ahead_moves_the_level_behind_up_to_the_newest_pullback():
    r = read(RISE + [(150, 15), (190, 20)])
    assert r["side"] == "bull" and [e["kind"] for e in r["events"]] == ["first", "continue"]
    assert r["break"]["price"] == pytest.approx(170.5) and r["change"]["price"] == pytest.approx(149.5)


def test_a_close_through_the_level_behind_is_the_change_and_a_wick_is_not():
    up = path(RISE + [(150, 15), (190, 20), (160, 12)])
    last = up[-1]
    wick = up + [{"time": last["time"] + 3600, "open": 160, "high": 161, "low": 140, "close": 158}]      # trades under 149.5, closes back above
    assert bias_levels(wick, above(wick))["side"] == "bull"
    close = up + [{"time": last["time"] + 3600, "open": 160, "high": 161, "low": 140, "close": 147}]
    r = bias_levels(close, above(close))
    assert r["side"] == "bear" and r["events"][-1]["kind"] == "change" and r["since"] == close[-1]["time"]
    assert r["change"]["price"] == pytest.approx(190.5)             # the high that break down was built on: a close above it changes it back


def test_the_mirror_for_a_fall():
    r = read([(200, 0), (200, 3), (160, 20), (180, 15), (130, 25), (150, 15), (140, 6), (170, 12)])
    assert r["side"] == "bear" and r["change"]["price"] == pytest.approx(180.5)     # the rally broke small highs only


@pytest.mark.parametrize("k", [0.0001, 1.0, 250.0])
@pytest.mark.parametrize("step", [60, 3600, 604800])
def test_the_same_shape_reads_the_same_at_any_price_scale_and_on_any_timeframe(k, step):
    r = read(RISE + [(150, 15), (190, 20)], k=k, step=step)
    assert r["side"] == "bull" and r["change"]["price"] == pytest.approx(149.5 * k)


def test_nothing_is_known_before_it_happened():
    c = path(RISE + [(150, 15), (190, 20), (140, 20)])
    full = bias_levels(c, above(c))
    for e in full["events"]:                                         # every event is found, at the same candle, with only the candles up to it
        i = next(j for j, x in enumerate(c) if x["time"] == e["t"])
        part = c[: i + 1]
        assert bias_levels(part, above(part))["events"][-1] == e
    hi, _ = swings(above(c))
    assert all(h["known"] > h["t"] for h in hi)                      # a swing of the timeframe above is known only after the next candle closes


def test_a_high_of_this_timeframe_alone_is_not_significant():
    """Small swings with no swing on the timeframe above: nothing to break, so no bias is claimed."""
    c = path([(100, 0), (101, 3), (100, 2), (102, 3), (101, 2), (103, 3)])
    flat_above = [{"time": 0, "open": 100, "high": 103.5, "low": 99.5, "close": 103}]
    assert bias_levels(c, flat_above)["side"] == "neutral"


def test_a_wick_past_the_level_ahead_is_not_the_break_but_the_later_close_is():
    up = path(RISE + [(150, 15), (165, 10)])
    t = up[-1]["time"]
    poke = up + [{"time": t + 3600, "open": 165, "high": 173, "low": 164, "close": 166}]                 # trades above 170.5, closes back under
    assert [e["kind"] for e in bias_levels(poke, above(poke))["events"]] == ["first"]
    more = poke + path([(166, 0), (160, 4), (176, 6)])[0:0] + [{"time": t + 3600 * (i + 2), "open": 166 + 2 * i, "high": 169 + 2 * i, "low": 165 + 2 * i, "close": 168 + 2 * i} for i in range(4)]
    r = bias_levels(more, above(more))
    assert [e["kind"] for e in r["events"]] == ["first", "continue"] and r["change"]["price"] == pytest.approx(149.5)


def test_a_new_swing_up_in_a_fall_is_not_a_change_either():
    """Highs of this timeframe are broken on the way up; the level behind holds, so nothing changes."""
    r = read([(200, 0), (200, 3), (160, 20), (180, 15), (130, 25), (150, 15), (140, 6), (160, 10), (150, 5), (172, 10)])
    assert r["side"] == "bear" and [e["kind"] for e in r["events"]] == ["first"]


def test_the_candle_still_forming_is_never_read():
    """The caller passes completed candles; `completed` drops one that has not closed yet."""
    from bias import completed
    c = path(RISE)
    forming = c + [{"time": c[-1]["time"] + 3600, "open": 170, "high": 171, "low": 100, "close": 101}]     # mid-candle, far under the level behind
    now = forming[-1]["time"] + 1800
    assert completed(forming, now) == c and bias_levels(completed(forming, now), above(c))["side"] == "bull"
    assert completed(forming, forming[-1]["time"] + 3600) == forming


def test_a_body_beyond_the_level_is_a_break_even_when_the_candle_opened_past_it():
    """His words: "if we have a body candle under or above that zone, it's a break." A candle that opens already
    under the level behind (a gap) never crosses it, and it is still the change: the body is beyond the level."""
    up = path(RISE + [(150, 15), (190, 20), (160, 12)])
    t = up[-1]["time"]
    gapped = up + [{"time": t + 3600, "open": 146, "high": 148, "low": 141, "close": 143}]        # opens and closes under 149.5: the whole body is below
    r = bias_levels(gapped, above(gapped))
    assert r["side"] == "bear" and r["events"][-1]["kind"] == "change"
    wick_only = up + [{"time": t + 3600, "open": 158, "high": 159, "low": 141, "close": 156}]     # a wick under it, the body above
    assert bias_levels(wick_only, above(wick_only))["side"] == "bull"
