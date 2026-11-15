#!/usr/bin/env bash
# research/preregistered-reentry-v2-2026-11-16.md: 2022 model + MMxM, futures, runner R, US100 US500 US30 only.
cd "$(dirname "$0")/../.."
A="US100 US500 US30"
touch reports/.reentry2-start
for m in ${MODELS:-2022_model mmxm}; do
  echo "=== RE-ENTRY v2 / SMALL GRAB $m futures (runner R)"
  uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model $m --only "re-entry" "small grab:" --metric runner_r --assets $A --cost futures --workers 10 2>&1 | grep -E "^\||Error"
  f=reports/variants$([ $m = 2022_model ] || echo -$m)-2022-01-03-2024-06-28-futures-only-runner.parquet
  [ "$f" -nt reports/.reentry2-start ] && cp "$f" reports/reentry2-$m.parquet || echo "no fresh output for $m"
done
sensors 2>/dev/null | grep Tctl
echo "=== DONE"
