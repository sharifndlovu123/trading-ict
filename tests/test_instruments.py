"""Trading cost scales with price (basis points), so the cost gate means the same thing at any price level."""

import pytest

from ict_engine.data.instruments import COST_BPS, cost_at


@pytest.fixture(autouse=True)
def _cfd_basis(monkeypatch):
    """These tests are about the CFD cost model; the default basis is futures since 2026-11-14."""
    monkeypatch.setenv("ICT_COST_BASIS", "cfd")


def test_cost_is_basis_points_of_price():
    assert cost_at("XAUUSD", 2000) == pytest.approx(2000 * COST_BPS["XAUUSD"] / 1e4)
    assert cost_at("XAUUSD", 4000) == pytest.approx(2 * cost_at("XAUUSD", 2000))     # doubles with price


def test_v1_costs_kept_at_2023_price_levels():
    # the old fixed costs (price units) are reproduced at typical 2023 prices
    for asset, price, old in (("US100", 14000, 1.0), ("US500", 4300, 0.5), ("US30", 34000, 2.0),
                              ("XAUUSD", 1950, 0.4), ("XAGUSD", 23.5, 0.03)):
        assert cost_at(asset, price) == pytest.approx(old, rel=0.05)


def test_unknown_asset_costs_nothing():
    assert cost_at("EURUSD", 1.1) == 0.0


def test_measured_spread_is_used_when_a_time_is_given(monkeypatch):
    import pandas as pd
    from ict_engine.data import spreads
    t = pd.Timestamp("2025-03-04 03:10", tz="America/New_York")
    table = pd.DataFrame({"date": [t.date()], "hour": [3.0], "expected": [3.45]})
    monkeypatch.setattr(spreads, "book", lambda: spreads.SpreadBook({"US100": table}))
    assert cost_at("US100", 20000, t) == 3.45                                  # measured
    assert cost_at("US100", 20000, t + pd.Timedelta(hours=7)) == cost_at("US100", 20000)   # no data → bps


def test_futures_cost_basis_is_one_tick_plus_commission(monkeypatch):
    """ICT trades futures: under the futures basis a round trip costs 1 tick + commission, in index points,
    whatever the time of day (no CFD session spread)."""
    import pandas as pd
    from ict_engine.data import instruments as ins
    monkeypatch.setenv("ICT_COST_BASIS", "futures")
    ts = pd.Timestamp("2024-01-09 07:10", tz="America/New_York")
    assert ins.cost_at("US100", 16000.0, ts) == pytest.approx(0.25 + 4.5 / 20)
    assert ins.cost_at("US500", 4500.0, ts) == pytest.approx(0.25 + 4.5 / 50)
    assert ins.cost_at("XAUUSD", 2000.0) == pytest.approx(0.10 + 4.5 / 100)
    assert ins.cost_basis() == "futures"


def test_cost_basis_defaults_to_futures_and_rejects_unknown(monkeypatch):
    from ict_engine.data import instruments as ins
    monkeypatch.delenv("ICT_COST_BASIS", raising=False)
    assert ins.cost_basis() == "futures"
    monkeypatch.setenv("ICT_COST_BASIS", "spot")
    with pytest.raises(ValueError):
        ins.cost_basis()
