#!/usr/bin/env bash
# research/preregistered-nested-fvg-2026-11-14.md: 2022 model + MMxM, futures, runner R.
cd "$(dirname "$0")/../.."
A="US100 US500 US30 XAUUSD XAGUSD"
for m in 2022_model mmxm; do echo "=== NESTED $m futures (runner R)"; uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model $m --only "loc:" "targets: 50%" --metric runner_r --assets $A --cost futures --workers 8 2>&1 | grep -E "^\||Error"; done
sensors 2>/dev/null | grep Tctl
echo "=== DONE"
