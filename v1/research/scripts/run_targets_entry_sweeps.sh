#!/usr/bin/env bash
# Pre-registered runs: liquidity targets + hold (runner R) and entry-quality gates, both cost bases.
cd "$(dirname "$0")/../.."
A="US100 US500 US30 XAUUSD XAGUSD"
for c in cfd futures; do
  for m in 2022_model pd_return; do echo "=== TARGETS $m $c (runner R)"; uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model $m --only "targets:" "hold:" --metric runner_r --assets $A --cost $c --workers 8 2>&1 | grep -E "^\|"; done
  for m in 2022_model mmxm silver_bullet cameron pd_return; do echo "=== ENTRY $m $c"; uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model $m --only "entry:" --assets $A --cost $c --workers 8 2>&1 | grep -E "^\|"; done
done
sensors 2>/dev/null | grep Tctl
echo "=== DONE"
