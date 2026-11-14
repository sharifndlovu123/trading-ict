"""Benchmark assets and their Dukascopy ids (v1 data = Dukascopy 1-minute CFD/spot)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

# Which killzone set applies (framework.md §6, ICT Bible p. 9):
#   "futures" — index futures/CFDs: London 02–05, NY AM 08:30–11, NY PM 13:30–16
#   "fx"      — FX, dollar index, metals: Asia 20–00, London 02–05, NY 07–10, London close 10–12
ClockSet = Literal["futures", "fx"]


@dataclass(frozen=True)
class Asset:
    name: str            # our name
    dukascopy_id: str    # dukascopy-node instrument id
    futures_root: str    # what ICT trades / reference cases use
    clock: ClockSet
    tick: float          # display/rounding unit
    source: str = "dukascopy"   # "dukascopy" (CFD/spot 1m) | "cme" (Databento CME 1m OHLCV, ict_engine.data.orderflow)


ASSETS: dict[str, Asset] = {
    a.name: a
    for a in [
        Asset("US100", "usatechidxusd", "NQ", "futures", 0.25),
        Asset("US500", "usa500idxusd", "ES", "futures", 0.25),
        Asset("US30", "usa30idxusd", "YM", "futures", 1.0),
        Asset("XAUUSD", "xauusd", "GC", "fx", 0.1),       # gold: FX clock by default (param)
        Asset("XAGUSD", "xagusd", "SI", "fx", 0.005),
        Asset("DXY", "dollaridxusd", "DX", "fx", 0.005),
        Asset("EURUSD", "eurusd", "6E", "fx", 0.00005),   # Euro index proxy
        # real CME futures (Databento NQ.v.0, continuous front month): order-flow tests. Not the root lookup
        # for "NQ" (that stays US100, which the reference cases use).
        Asset("NQCME", "", "NQ", "futures", 0.25, source="cme"),
    ]
}

BY_FUTURES_ROOT = {a.futures_root: a for a in ASSETS.values() if a.source == "dukascopy"}


def get(name_or_root: str) -> Asset:
    """Look up by our name (US100) or futures root (NQ)."""
    key = name_or_root.upper()
    if key in ASSETS:
        return ASSETS[key]
    if key in BY_FUTURES_ROOT:
        return BY_FUTURES_ROOT[key]
    raise KeyError(f"unknown asset {name_or_root!r}; known: {sorted(ASSETS)}")


# Round-trip spread + slippage in basis points of price (v1 guesses). Set from the old fixed costs
# (US100 1.0, US500 0.5, US30 2.0, gold 0.4, silver 0.03 price units) at typical 2023 prices. Basis
# points keep the cost gate meaning the same thing when price doubles (gold ~$1,900 → $3,500+).
COST_BPS: dict[str, float] = {"NQCME": 0.71, "US100": 0.71, "US500": 1.16, "US30": 0.59, "XAUUSD": 2.05, "XAGUSD": 12.8}


# Futures round trip in the CFD's price units (US100≈NQ, US500≈ES, US30≈YM, XAUUSD≈GC, XAGUSD≈SI points):
# 1 tick of spread + commission/fees of ~$4.50 per contract round trip ÷ the contract's $ per point.
# Assumption (2026-11-13): a retail/prop futures account; 1 tick even pre-market; no extra slippage.
FUTURES_TICK = {"NQCME": 0.25, "US100": 0.25, "US500": 0.25, "US30": 1.0, "XAUUSD": 0.10, "XAGUSD": 0.005}
FUTURES_POINT_VALUE = {"NQCME": 20.0, "US100": 20.0, "US500": 50.0, "US30": 5.0, "XAUUSD": 100.0, "XAGUSD": 5000.0}
FUTURES_FEE_USD = 4.5
COST_BASES = ("cfd", "futures")


def cost_basis() -> str:
    """Which cost model trades pay: ``futures`` (1 tick + commission; default since 2026-11-14, Sharif: "skip cfds, focus
    on futures") or ``cfd`` (measured Dukascopy spreads).
    Set with the env var ICT_COST_BASIS (the backtest CLI's ``--cost`` sets it, so worker processes inherit it)."""
    b = os.environ.get("ICT_COST_BASIS", "futures")
    if b not in COST_BASES:
        raise ValueError(f"ICT_COST_BASIS must be one of {COST_BASES}, got {b!r}")
    return b


def futures_cost(asset: str) -> float:
    return FUTURES_TICK[asset] + FUTURES_FEE_USD / FUTURES_POINT_VALUE[asset]


def cost_at(asset: str, price: float, ts=None) -> float:
    """Round-trip cost in price units for one trade at ``price`` decided at ``ts``.

    Futures basis: 1 tick + commission (``futures_cost``). CFD basis: with ``ts`` and a measured spread table
    (``ict_engine.data.spreads``, Dukascopy ask − bid) the expected spread for that half-hour, from the
    previous 5 trading days only (no look-ahead); otherwise the basis-point estimate below."""
    if cost_basis() == "futures" and asset in FUTURES_TICK:
        return futures_cost(asset)
    if ts is not None:
        from ict_engine.data import spreads
        s = spreads.book().spread(asset, ts)
        if s is not None:
            return s
    return COST_BPS.get(asset, 0.0) * abs(price) / 1e4
