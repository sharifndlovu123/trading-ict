"""Shared test setup."""

import pytest

from ict_engine.data.instruments import COST_BPS


@pytest.fixture(autouse=True)
def _synthetic_prices_have_no_costs(request, monkeypatch):
    """Modules built on the synthetic ~100-price day (tests/test_model_2022.py) set
    ``SYNTHETIC_PRICES = True``: real-world US100 costs (0.71 bp of price) would be ~0.5R of their
    1–2 point stops and trip the cost gate, which is not what those tests are about."""
    if getattr(request.module, "SYNTHETIC_PRICES", False):
        monkeypatch.setitem(COST_BPS, "US100", 0.0)
        monkeypatch.setenv("ICT_COST_BASIS", "cfd")                                  # CFD basis (zeroed), never futures
        from ict_engine.data import spreads
        monkeypatch.setattr(spreads, "book", lambda: spreads.SpreadBook({}))      # no measured spreads either
