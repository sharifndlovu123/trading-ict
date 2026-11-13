"""Shared test setup."""

import pytest

from ict_engine.data.instruments import COST


@pytest.fixture(autouse=True)
def _synthetic_prices_have_no_costs(request, monkeypatch):
    """Modules built on the synthetic ~100-price day (tests/test_model_2022.py) set
    ``SYNTHETIC_PRICES = True``: real-world US100 costs (1 point) would be ~0.5R of their
    1–2 point stops and trip the cost gate, which is not what those tests are about."""
    if getattr(request.module, "SYNTHETIC_PRICES", False):
        monkeypatch.setitem(COST, "US100", 0.0)
