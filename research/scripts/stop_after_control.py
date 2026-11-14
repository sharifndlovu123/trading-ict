"""Control for stop_then_tp1: after a stop-out, P(TP1 trades before session end) vs P(the mirror level trades:
entry ∓ the TP1 distance on the stop side, i.e. the same distance further against the trade)."""
import sys
import pandas as pd
from ict_engine.eval.backtest import load_range
p = pd.read_parquet(f"reports/gaps-{sys.argv[1]}.parquet")
L = p[(p.status == "traded") & p.gap.isin(["stop_then_tp1", "fast_loss", "slow_loss", "near_miss"])]
rows = []
for a, g in L.groupby("asset"):
    b = load_range(a, pd.Timestamp("2022-01-03").date(), pd.Timestamp("2024-06-28").date())
    for _, r in g.iterrows():
        end = pd.Timestamp(f"{pd.Timestamp(r.day):%Y-%m-%d} 16:00", tz="America/New_York")
        aft = b[(b.index > r.exit_at) & (b.index < end)]
        long = r.side == "long"; d = abs(r.tp1 - r.stop)          # distance from where price is (the stop)
        mirror = r.stop - d if long else r.stop + d
        up = (aft.high >= r.tp1) if long else (aft.low <= r.tp1)
        dn = (aft.low <= mirror) if long else (aft.high >= mirror)
        tu = aft.index[up.argmax()] if up.any() else None; td = aft.index[dn.argmax()] if dn.any() else None
        first = "tp1" if tu is not None and (td is None or tu < td) else ("mirror" if td is not None else "neither")
        rows.append((r.family, bool(up.any()), bool(dn.any()), first))
x = pd.DataFrame(rows, columns=["family", "tp1", "mirror", "first"])
out = x.groupby("family").agg(n=("tp1", "size"), tp1_after=("tp1", "mean"), mirror_after=("mirror", "mean"))
out = out.join(x.groupby("family")["first"].value_counts(normalize=True).unstack().add_prefix("first_"))
print(sys.argv[1]); print(out.round(3).to_string())
