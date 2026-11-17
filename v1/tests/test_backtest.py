"""Backtest table: one row per setup, real vs shadow results, hindsight columns kept apart."""

from datetime import timedelta

from ict_engine.eval.backtest import run
from ict_engine.models.model_2022 import Params
from tests.test_model_2022 import DAY, bars

SYNTHETIC_PRICES = True                  # conftest: no costs on the ~100-price synthetic day


def test_traded_row_has_result_and_matching_shadow():
    df = run(bars(), DAY, DAY, "US100")
    t = df[df.status == "traded"]
    assert len(t) >= 1
    row = t.iloc[0]
    assert row.vote and row.r > 0 and row.window == "ny_am_kz" and row.weekday == DAY.strftime("%a")
    assert row.shadow_vote == row.vote and row.shadow_r == row.r          # same plan, same bars
    assert row.outcome in ("bull_hit", "bear_hit", "none", "ambiguous")


def test_blocked_setup_keeps_its_shadow_result():
    df = run(bars(), DAY, DAY, "US100", Params(windows=("ny_pm_kz",)))
    b = df[(df.status == "blocked@time") & df.entry.notna()]
    assert len(b) and b.r.isna().all() and b.shadow_exit.notna().all()
    assert (b.failed_gate == "time").all()


def test_columns_for_post_analysis_exist():
    df = run(bars(), DAY, DAY, "US100")
    need = {"model", "variant", "asset", "day", "side", "decided_at", "weekday", "hour", "window", "month",
            "bias", "outcome", "status", "failed_gate", "gates", "risk", "tp1_r", "r", "vote", "mae_r",
            "shadow_r", "shadow_vote", "liquidity", "poi", "news", "news_event", "news_mins", "news_today"}
    assert need <= set(df.columns)


def test_weekends_and_days_without_history_are_skipped():
    df = run(bars(), DAY - timedelta(days=30), DAY, "US100")                 # fixture has ~1 week of bars
    assert len(df) and (df.day.dt.day_of_week < 5).all()
    assert df.day.min().date() > DAY - timedelta(days=10)                   # no-history days skipped, no crash


def test_counterfactuals_change_one_factor():
    import pandas as pd
    from ict_engine.eval.backtest import counterfactuals
    from ict_engine.models.base import TradePlan
    t = lambda m: pd.Timestamp("2024-01-09 10:00", tz="America/New_York") + pd.Timedelta(minutes=m)
    idx = pd.date_range(t(0), periods=4, freq="1min")
    # long 100, stop 98, TP1 104: dips to 97.5 (stopped; 1.5× stop = 97 survives), then 104.5
    b = pd.DataFrame([(101, 101, 101, 101), (101, 101, 99.5, 100), (100, 100, 97.5, 98), (98, 104.5, 98, 104)],
                     columns=["open", "high", "low", "close"], index=idx, dtype=float)
    plan = TradePlan("long", t(0), t(30), 100, 98, 104, 108)
    cf = counterfactuals(plan, b, t(60), 0.0)
    assert cf["cf_wide_stop_vote"] is True                  # wider stop would have survived
    assert cf["cf_tp1_1r_vote"] is False                    # stop hit before 102
    assert cf["cf_flip_vote"] is False                      # short 100 stop 102 → stopped at 104.5
    assert counterfactuals(None, b, t(60), 0.0) == {}


def test_news_columns_come_from_the_calendar():
    from datetime import date
    import pandas as pd
    from ict_engine.eval.backtest import news_cols
    t = pd.Timestamp("2024-02-13 08:15", tz="America/New_York")          # hot CPI day, 15 min before
    c = news_cols(t)
    assert c["news"] == "before release (≤30m)" and c["news_event"] == "CPI" and c["news_mins"] == 15
    assert news_cols(pd.Timestamp("2024-01-09 10:00", tz="America/New_York"))["news_today"] == "none"
