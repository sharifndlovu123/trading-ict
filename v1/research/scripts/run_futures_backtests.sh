#!/usr/bin/env bash
# Futures-basis backtests of all five models, 2022-01-03 → 2024-06-28 (selection period), 8 at a time.
cd "$(dirname "$0")/../.."
for m in 2022_model mmxm silver_bullet cameron pd_return; do for a in US100 US500 US30 XAUUSD XAGUSD; do echo "$m $a"; done; done |
  xargs -P 8 -L 1 sh -c 'nice -n 10 uv run python -m ict_engine.eval.backtest "$1" 2022-01-03 2024-06-28 --model "$0" --cost futures 2>&1 | tail -2'
sensors 2>/dev/null | grep Tctl
echo "=== DONE"
