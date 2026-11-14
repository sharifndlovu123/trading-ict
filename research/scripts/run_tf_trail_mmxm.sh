#!/usr/bin/env bash
# Rerun of the MMxM half of research/preregistered-timeframes-trail-2026-11-14.md after the _tf_minutes fix.
cd "$(dirname "$0")/../.."
echo "=== TF/TRAIL mmxm futures (runner R)"
uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model mmxm --only "tf:" "runner:" --metric runner_r --assets US100 US500 US30 XAUUSD XAGUSD --cost futures --workers 8 2>&1 | grep -E "^\||Error"
echo "=== DONE"
