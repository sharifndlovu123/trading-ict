"""Pre-registered order-flow tests, step 1: run the five models (+ 2022 model at market) on CME NQ 1m bars,
2024, futures cost basis. Writes reports/nqcme/<label>.parquet."""
import os, sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path
os.environ["ICT_COST_BASIS"] = "futures"
OUT = Path("reports/nqcme")
START, END = date(2024, 1, 2), date(2024, 12, 31)
RUNS = [("2022_model", {}), ("2022_model", {"entry_mode": "market"}), ("cameron", {}), ("mmxm", {}),
        ("silver_bullet", {}), ("pd_return", {})]


def one(job):
    model, kw = job
    from ict_engine.eval.backtest import load_range, run
    from ict_engine.models.registry import modules
    p = modules()[model].Params(**kw)
    df = run(load_range("NQCME", START, END), START, END, "NQCME", p)
    df["family"], df["cost_basis"] = model, "futures"
    df["variant_label"] = "market" if kw else "default"
    name = model + ("-market" if kw else "")
    df.to_parquet(OUT / f"{name}.parquet")
    t = df[df.status == "traded"]
    return f"{name}: {len(df)} setups, {len(t)} trades, exp {t.r.mean():+.3f}R"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(6) as ex:
        for line in ex.map(one, RUNS):
            print(line, flush=True)
