"""Trading cost scales with price (basis points), so the cost gate means the same thing at any price level."""

import pytest

from ict_engine.data.instruments import COST_BPS, cost_at


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
