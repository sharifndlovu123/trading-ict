# Trading costs: measured spreads replace guesses (2026-11-13)

Source: Dukascopy 1m bid and ask, 2021-10 → 2026-11. Spread = ask.close − bid.close, median per NY half-hour.
A trade pays the expected spread for its half-hour, from the previous 5 trading days only (`ict_engine/data/spreads.py`).

| asset | old fixed guess | before 09:30 (London / premarket) | after 09:30 | note |
|---|---|---|---|---|
| US100 | 1.0 | 3.45 | 1.45 | fixed session steps, not % of price |
| US30 | 2.0 | 3.98 | 2.48 | same |
| US500 | 0.5 | 0.70 (2022) → 0.51 | 0.51 | |
| XAUUSD | 0.40 | 0.36 (2022) → 0.57 (2025) | same | scales with price |
| XAGUSD | 0.03 | 0.03 | 0.03 | flat |

Consequence: London/premarket trades on US100/US30 were charged 2.5–3.5× too little before this change.
Results from commits before this one overstate those windows.
