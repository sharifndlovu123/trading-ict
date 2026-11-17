#!/usr/bin/env bash
# research/preregistered-htf-stop-2026-11-15.md: 2022 model + MMxM, futures, runner R.
cd "$(dirname "$0")/../.."
A="US100 US500 US30 XAUUSD XAGUSD"
for m in 2022_model mmxm; do echo "=== HTF STOP $m futures (runner R)"; uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model $m --only "stop:" --metric runner_r --assets $A --cost futures --workers 10 2>&1 | grep -E "^\||Error"; done
sensors 2>/dev/null | grep Tctl
echo "=== DONE"
