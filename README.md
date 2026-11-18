# ICT reading, v2

Sharif is teaching Claude to read the market his way. This repository holds what has been taught and confirmed, one
concept at a time, each with its lesson (his words), its tools and its tests.

- Start with `CLAUDE.md` (how the work is done) and `v2/README.md` (the rules of what may enter).
- Progress: `v2/MIGRATION.md`.
- Tests: `uv sync`, then `uv run pytest -q v2`.
- The chart: `uv run python v2/chart/server.py`, then http://127.0.0.1:8776/

The old version is sealed off in `v1/`. Nothing here depends on it.
