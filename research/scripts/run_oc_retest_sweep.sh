#!/usr/bin/env bash
# research/preregistered-oc-retest-2026-11-15.md: MMxM, futures, runner R.
cd "$(dirname "$0")/../.."
A="US100 US500 US30 XAUUSD XAGUSD"
echo "=== OC RETEST mmxm futures (runner R)"; uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model mmxm --only "entry: retest of the broken OC" --metric runner_r --assets $A --cost futures --workers 10 2>&1 | grep -E "^\||Error"
sensors 2>/dev/null | grep Tctl
echo "=== DONE"
