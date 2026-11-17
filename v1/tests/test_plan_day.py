"""Intraday / smaller-target options for the engine plan replays (research/scripts/plan_build + plan_sweep). Sharif
2026-11-16: "hold a trade for the day and that's it". Hand-built 1m candles with known answers: flat at 16:55 NY, no fill
after 15:00, a stop beyond the array, the displacement-qualified confirmation, partial fractions, the TP1 rules, and the
array version of ``manage`` giving the same answers as the loop. Defaults stay the first plan's (test_plan_confirm)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from plan_build import day_window, manage, replay, replay_confirm, wall, zone_stop  # noqa: E402
from plan_sweep import excursions, manage_np, stats, tp1_price, wilson  # noqa: E402

NY = "America/New_York"
AT = pd.Timestamp("2023-03-15 08:30", tz=NY)
# a short from the array 100–102: entry 100, range stop 105, TP1 90, final 85 (as tests/test_plan_confirm.py)
PLAN = {"side": "short", "entry": 100.0, "stop": 105.0, "tp1": 90.0, "final": 85.0, "rtf": "1h", "adr": 10.0,
        "array": {"bottom": 100.0, "top": 102.0}, "range": {"lo": 90.0, "hi": 104.5}, "pools_against": [110.0, 115.0]}


def day(events: dict, base: float = 97.0, until: str = "2023-03-16 12:00") -> pd.DataFrame:
    """1m candles from 08:30, flat at ``base`` except the given {"HH:MM" or full ts: (o, h, l, c)} bars."""
    idx = pd.date_range(AT, pd.Timestamp(until, tz=NY), freq="1min")
    df = pd.DataFrame({"open": base, "high": base, "low": base, "close": base}, index=idx, dtype=float)
    for k, v in events.items():
        ts = pd.Timestamp(k if len(k) > 5 else f"2023-03-15 {k}", tz=NY)
        df.loc[ts] = v
    return df


def five(rows, start=AT):
    out = []
    for o, h, l, c in rows:
        out += [(o, h, o, h), (h, h, l, l), (l, max(l, c), l, c), (c, c, c, c), (c, c, c, c)]
    idx = pd.date_range(start, periods=len(out), freq="1min", tz=NY)
    return pd.DataFrame(out, columns=["open", "high", "low", "close"], index=idx, dtype=float)


def test_day_window_is_1655_flat_and_1500_last_entry():
    flat, last = day_window(AT)
    assert flat == pd.Timestamp("2023-03-15 16:55", tz=NY) and last == pd.Timestamp("2023-03-15 15:00", tz=NY)


def test_day_only_closes_at_the_last_close_before_1655():
    b = day({"10:00": (97, 100.5, 97, 99), "16:54": (97, 97, 96, 96), "16:55": (96, 96, 80, 80)})   # 16:55 collapse: not ours
    r = replay(b, AT, PLAN, day_only=True)
    assert r["filled"] == wall(pd.Timestamp("2023-03-15 10:00", tz=NY))
    assert r["exit"] == "open" and r["runner_r"] == pytest.approx((100 - 96) / 5)      # closed 96 at 16:54, risk 5
    multi = replay(b, AT, PLAN)                                                       # the default still holds overnight
    assert "TP1" in multi["outcome"]


def test_day_only_takes_no_fill_after_1500():
    b = day({"15:01": (97, 100.5, 97, 99)})
    assert replay(b, AT, PLAN, day_only=True)["outcome"] == "not filled before the entry cutoff"
    assert "filled" in replay(b, AT, PLAN)
    assert "filled" in replay(day({"15:00": (97, 100.5, 97, 99)}), AT, PLAN, day_only=True)       # 15:00 itself is allowed


def test_zone_stop_sits_beyond_the_array_and_the_range_stop_still_cancels():
    assert zone_stop(PLAN) == pytest.approx(102.5)                                    # top 102 + 0.05 ADR
    thin = PLAN | {"array": {"bottom": 100.0, "top": 100.2}}
    assert zone_stop(thin) == pytest.approx(101.0)                                    # never tighter than 0.1 ADR
    b = day({"10:00": (97, 100.5, 97, 99), "10:05": (99, 103, 99, 99)})              # 103: past the zone, inside the range
    assert replay(b, AT, PLAN, day_only=True, stop_at="zone")["runner_r"] == -1.0
    assert replay(b, AT, PLAN, day_only=True)["exit"] == "open"                       # range stop 105 not hit
    gone = day({"10:00": (97, 99, 97, 99), "10:01": (99, 99, 99, 99)})
    gone.loc[pd.Timestamp("2023-03-15 10:02", tz=NY)] = (104, 106, 104, 106)          # gaps over the zone: fill + stop same bar
    assert replay(gone, AT, PLAN, stop_at="zone")["runner_r"] == -1.0
    with pytest.raises(ValueError):
        replay(b, AT, PLAN, stop_at="nope")


QUIET = [(97, 97.2, 96.9, 97.2), (97.2, 97.3, 97, 97)] * 7                            # 14 small 5m candles, body 0.2
SUPPORT = QUIET + [(97, 99, 96.5, 99), (99, 101, 99, 100.5),                          # touches 100 → armed
                   (100.5, 101.5, 99.5, 99.8),
                   (99.8, 99.9, 97, 97.5),                                            # the displacement: body 2.3
                   (97.5, 98.5, 95, 95.5),                                            # bear FVG 98.5–99.5
                   (95.5, 98.6, 95.5, 97), (97, 97, 89, 89.5), (89.5, 89.5, 84, 85)]


def test_displacement_confirmation_needs_a_big_middle_candle():
    b = five(SUPPORT)
    plain = replay_confirm(b, AT, PLAN)
    disp = replay_confirm(b, AT, PLAN, min_disp=1.5)      # mean body of the 14 before = 6.4 / 14 = 0.46 → 2.3 ≥ 0.69
    assert plain["stage"] == disp["stage"] == "support" and disp["entry"] == plain["entry"] == 98.5
    assert disp["confirmed"] == wall(AT + pd.Timedelta(minutes=5 * 19))               # the FVG's third candle close
    weak = replay_confirm(b, AT, PLAN, min_disp=6.0)      # 2.3 < 6 × 0.46 → not a displacement → no support trade
    assert weak["stage"] == "armed" and weak["runner_r"] == 0.0


def test_displacement_without_history_is_not_confirmed():
    r = replay_confirm(five(SUPPORT[14:]), AT, PLAN, min_disp=1.5)                    # < 5 candles of history: unknown
    assert r["stage"] == "armed"


def test_confirm_day_only_drops_a_late_confirmation():
    late = pd.Timestamp("2023-03-15 14:40", tz=NY)                                    # the FVG closes 15:05, retest later
    b = pd.concat([day({}).loc[:late - pd.Timedelta(minutes=1)], five(SUPPORT[14:], late)])
    r = replay_confirm(b, AT, PLAN, day_only=True)
    assert r["stage"] == "support" and r["outcome"] == "support no retest before the entry cutoff"
    assert replay_confirm(b, AT, PLAN)["outcome"].startswith("support: TP1")          # default: still traded


def test_min_rr_zero_lets_a_close_target_through():
    near = PLAN | {"tp1": 94.9, "final": 94.8}                                        # 3.6 from the 98.5 entry, risk 4
    b = five(SUPPORT)
    assert replay_confirm(b, AT, near)["outcome"] == "support but < 1 R to the targets"
    assert replay_confirm(b, AT, near, min_rr=0.0).get("filled")


def test_partial_fraction_and_all_out():
    idx = pd.date_range(AT, periods=3, freq="1min", tz=NY)
    b = pd.DataFrame([(100, 100, 95, 95), (95, 96, 89, 90), (90, 101, 90, 100)], columns=["open", "high", "low", "close"],
                     index=idx, dtype=float)                                          # TP1 90, then back to entry
    assert manage(b, 100, 105, 90, 85, long=False)["runner_r"] == pytest.approx(1.0)            # 50 % × 2 R, rest BE
    assert manage(b, 100, 105, 90, 85, long=False, partial=0.75)["runner_r"] == pytest.approx(1.5)
    assert manage(b, 100, 105, 90, 85, long=False, partial=1.0)["runner_r"] == pytest.approx(2.0)


def test_manage_np_matches_manage_on_random_paths():
    rng = np.random.default_rng(7)
    for k in range(300):
        n = int(rng.integers(5, 400))
        c = 100 + np.cumsum(rng.normal(0, 0.6, n))
        o = np.r_[100.0, c[:-1]]
        h, l = np.maximum(o, c) + rng.random(n) * 0.5, np.minimum(o, c) - rng.random(n) * 0.5
        b = pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=pd.date_range(AT, periods=n, freq="1min", tz=NY))
        long = bool(k % 2)
        sg = 1 if long else -1
        e, s, t1, fn = 100.0, 100 - sg * 3.0, 100 + sg * float(rng.choice([1.5, 3, 6])), 100 + sg * 9.0
        for part in (0.5, 0.75, 1.0):
            a, m = manage(b, e, s, t1, fn, long, partial=part), manage_np(h, l, c, e, s, t1, fn, long, part)
            assert m["r"] == pytest.approx(a["runner_r"], abs=0.006), (k, part)
            assert m["win"] == a["outcome"].startswith("TP1")


def test_manage_np_stop_first_on_the_same_bar():
    h, l, c = np.array([106.0]), np.array([89.0]), np.array([95.0])
    assert manage_np(h, l, c, 100, 105, 90, 85, long=False) == {"r": -1.0, "win": False, "exit": "stop", "i": 0}


def test_tp1_rules():
    pools = [99.0, 97.0, 93.0, 80.0]                                                  # short from 100, stop 104 (risk 4)
    assert tp1_price("1R", 100, 104, False, 90, pools) == 96.0
    assert tp1_price("1.5R", 100, 104, False, 90, pools) == 94.0
    assert tp1_price("plan", 100, 104, False, 90, pools) == 90
    assert tp1_price("plan", 100, 104, False, 97, pools) is None                      # < 1 R: no structural target
    assert tp1_price("pool", 100, 104, False, 90, pools) == 93.0                      # the nearest pool ≥ 1 R
    assert tp1_price("pool05", 100, 104, False, 90, pools) == 97.0                    # ≥ 0.5 R
    assert tp1_price("pool", 100, 104, False, 90, [99.0]) is None
    assert tp1_price("2R", 100, 96, True, 120, []) == 108.0


def test_excursions_in_r():
    h, l = np.array([101.0, 100.5, 105.0, 100.0]), np.array([97.0, 99.0, 100.0, 88.0])
    x = excursions(h, l, 100, 104, False, 90)                                         # short, risk 4, stop on bar 2
    assert x["mfe_r"] == pytest.approx(0.75) and x["stopped"] and x["mins_to_stop"] == 2
    assert x["tp_after_stop"] is True and x["mfe_after_stop_r"] == pytest.approx(3.0)


def test_wilson_and_stats():
    lo, hi = wilson(50, 100)
    assert lo == pytest.approx(0.404, abs=0.002) and hi == pytest.approx(0.596, abs=0.002)
    g = pd.DataFrame({"day": ["a", "a", "b", "c", "d"], "r": [1, -1, 12, -1, 1.0], "win": [True, False, True, False, True]})
    g["r_net"] = g.r
    s = stats(g)
    assert s["n"] == 5 and s["win%"] == 60.0 and s["sum_R"] == 12.0 and s["cap10"] == 10.0 and s["ex3"] == -2.0
