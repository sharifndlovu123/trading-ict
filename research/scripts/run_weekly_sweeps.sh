#!/usr/bin/env bash
# research/preregistered-weekly-structure-2026-11-16.md (+ amendments 1–2): 2022 model + MMxM, futures, runner R, indices.
cd "$(dirname "$0")/../.."
A="US100 US500 US30"
touch reports/.weekly-start
for m in ${MODELS:-2022_model mmxm}; do
  echo "=== SMALL GRAB vs WEEKLY STRUCTURE $m futures (runner R)"
  uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model $m --only "small grab: against the weekly structure" --metric runner_r --assets $A --cost futures --workers 10 2>&1 | grep -E "^\||Error"
  f=reports/variants$([ $m = 2022_model ] || echo -$m)-2022-01-03-2024-06-28-futures-only-runner.parquet
  [ "$f" -nt reports/.weekly-start ] && cp "$f" reports/weekly-$m.parquet || echo "no fresh output for $m"
done
sensors 2>/dev/null | grep Tctl
echo "=== DONE"
