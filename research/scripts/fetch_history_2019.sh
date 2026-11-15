#!/usr/bin/env bash
# Older history for the weekly-structure warm-up (intermediate-term swings need ~1–2 years): Oct 2019 → Sep 2021,
# US100 US500 US30, bid + ask. Data stays in data/bars/ (git-ignored).
cd "$(dirname "$0")/../.."
for a in US100 US500 US30; do
  for p in bid ask; do
    echo "=== $a $p"; uv run python -m ict_engine.data.dukascopy fetch $a 2019-10-01 2021-09-30 --price $p 2>&1 | tail -n 2
  done
done
echo "=== FETCH DONE"
