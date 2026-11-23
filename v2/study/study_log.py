"""The study log: what Sharif drew on each instrument, day by day, and how it changed.

His (23 Nov 2026): "keep a log of a list of assets; we will do this 1-4 study for concepts and how they work together
for the week. We will draw bias, liq etc for all, so start clean chart. I will draw them every day, or make updates to
them daily as days move, so you must keep track of these changes through a log… you can separate by asset."

History too (his, 23 Nov 2026): "we can do history instead, which allows replay… I can move a day ahead to see if I
change or remain". A save made in replay carries the moment the chart was showing (``chart_time``), so the log is
headed by that day and Claude can load the same candles, with nothing after that moment, and see what he saw.

It only READS what he saves from the chart (``v2/chart/saves.jsonl``, ``v2/chart/notes.jsonl``: his files, never
edited) and writes one log per instrument into ``v2/study/logs/``, plus an index. The logs are rebuilt from his
files each time, so they can never drift from what he saved. Nothing here judges a mark, counts anything or reads a
chart: it records. How a change is told (added, removed, changed, by a mark's id) is mine.

    uv run python v2/study/study_log.py            # rebuild every log
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
CHART = HERE.parent / "chart"
SAVES, NOTES, OUT, STUDY = CHART / "saves.jsonl", CHART / "notes.jsonl", HERE / "logs", HERE / "study.json"
NY = ZoneInfo("America/New_York")
WHERE = ("price", "top", "bottom", "p0", "p1", "t0", "t1")          # what places a mark; a change in any of these is a move
WHAT = ("kind", "tf", "shape", "side")


def rows(path: Path) -> list[dict]:
    """The lines of one of his files, oldest first. A missing file is no lines."""
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def name(m: dict) -> str:
    """A mark the way it is spoken of: ``[kind timeframe]``."""
    return f"[{m.get('kind') or m.get('shape', 'mark')} {m.get('tf', '')}]".replace(" ]", "]")


def chart_time(t) -> str:
    """A time on the chart (candle times are New York clock times kept as plain seconds)."""
    return "" if t is None else datetime.fromtimestamp(t, UTC).strftime("%d %b %Y %H:%M")


def where(m: dict) -> str:
    """Where a mark sits, in words: its price or prices, and the candle time it starts (and ends) at."""
    shape = m.get("shape")
    num = lambda v: f"{v:,.5f}".rstrip("0").rstrip(".") if isinstance(v, (int, float)) else "?"       # noqa: E731
    at = "level at " + num(m.get("price")) if shape == "level" else f"zone {num(m.get('bottom'))} to {num(m.get('top'))}" if shape == "zone" \
        else f"line {num(m.get('p0'))} to {num(m.get('p1'))}" if shape == "line" else "vertical line" if shape == "vline" else str(shape)
    span = f"from {chart_time(m.get('t0'))}" + (f" to {chart_time(m['t1'])}" if m.get("t1") is not None else "")
    return f"{at}, {span}" if m.get("t0") is not None else at


def changes(before: list[dict], now: list[dict]) -> dict:
    """What differs between two saves of one instrument: ``{"added", "removed", "changed"}``. Marks are matched by
    their id (``uid``); a mark without one is matched by everything about it. ``changed`` holds ``(before, now)``."""
    key = lambda m: m.get("uid") or json.dumps({k: m.get(k) for k in WHAT + WHERE}, sort_keys=True)   # noqa: E731
    old, new = {key(m): m for m in before}, {key(m): m for m in now}
    same = lambda a, b: all(a.get(k) == b.get(k) for k in WHAT + WHERE)                               # noqa: E731
    return {"added": [m for k, m in new.items() if k not in old], "removed": [m for k, m in old.items() if k not in new],
            "changed": [(old[k], m) for k, m in new.items() if k in old and not same(old[k], m)]}


def entries(saves: list[dict], notes: list[dict], since: float = 0) -> dict:
    """Per instrument, in order: every save since ``since`` with what changed against the save before it, and every
    note he wrote. ``{asset: [{"at", "tf", "chart_time", "kind": "save" | "note", …}]}``. The save before ``since``,
    if any, is only what the first one is compared with."""
    out: dict = {}
    last: dict = {}
    for s in sorted(saves, key=lambda s: s["saved"]):
        mine = [m for m in s.get("marks", []) if m.get("by", "S") == "S"]
        if s["saved"] >= since:
            out.setdefault(s["asset"], []).append({"at": s["saved"], "kind": "save", "tf": s.get("tf", ""), "chart_time": s.get("chart_time"),
                                                   "marks": mine, "note": s.get("note", ""), **changes(last.get(s["asset"], []) if s["asset"] in last else [], mine)})
        last[s["asset"]] = mine
    for n in notes:
        if n.get("saved", 0) >= since and n.get("asset") and not n.get("removed"):
            out.setdefault(n["asset"], []).append({"at": n["saved"], "kind": "note", "tf": n.get("tf", ""), "chart_time": n.get("chart_time"),
                                                   "text": n.get("text", ""), "mode": n.get("kind", "")})
    return {a: sorted(v, key=lambda e: e["at"]) for a, v in out.items()}


def page(asset: str, items: list[dict]) -> str:
    """One instrument's log as text: a heading per day (New York), an entry per save or note, newest day last."""
    lines, day = [f"# {asset}: study log", "", "What Sharif drew and wrote, in order. Rebuilt from his saves; not edited by hand.", ""], None
    for e in items:
        when = datetime.fromtimestamp(e["at"], NY)
        # in replay the day that matters is the one the chart was showing, not the day he sat down to draw it
        shown = datetime.fromtimestamp(e["chart_time"], UTC) if e.get("chart_time") else None
        head = f"Chart taken back to {shown.strftime('%A %d %b %Y')} (replay)" if shown else when.strftime("%A %d %b %Y")
        if head != day:
            day = head
            lines += [f"## {head}", ""]
        on = f"on the {e['tf']} chart" + (f", in replay at {chart_time(e['chart_time'])}" if e.get("chart_time") else "")
        if e["kind"] == "note":
            lines += [f"**{when.strftime('%H:%M')} New York, note {on}:** {e['text']}", ""]
            continue
        lines.append(f"**{when.strftime('%H:%M')} New York, saved {on}** ({len(e['marks'])} marks on the chart)")
        lines += [f"- added {name(m)}: {where(m)}" for m in e["added"]]
        lines += [f"- changed {name(b)}: {where(a)}  →  {name(b)}: {where(b)}" for a, b in e["changed"]]
        lines += [f"- removed {name(m)}: {where(m)}" for m in e["removed"]]
        if not (e["added"] or e["changed"] or e["removed"]):
            lines.append("- nothing changed since the save before")
        if e.get("note"):
            lines.append(f"- he wrote: {e['note']}")
        lines.append("")
    return "\n".join(lines)


def build(saves: Path = SAVES, notes: Path = NOTES, out: Path = OUT, since: float = 0) -> dict:
    """Rebuild every instrument's log and the index. Returns ``{asset: number of entries}``."""
    got = entries(rows(saves), rows(notes), since)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.md"):
        old.unlink()
    for asset, items in got.items():
        (out / f"{asset}.md").write_text(page(asset, items))
    index = ["# Study log: the instruments", "", "| Instrument | Entries | Last save or note (New York) | Marks on the chart now |", "|---|---|---|---|"]
    for asset, items in sorted(got.items()):
        marks = next((len(e["marks"]) for e in reversed(items) if e["kind"] == "save"), 0)
        index.append(f"| [{asset}]({asset}.md) | {len(items)} | {datetime.fromtimestamp(items[-1]['at'], NY).strftime('%a %d %b %H:%M')} | {marks} |")
    (out / "README.md").write_text("\n".join(index) + "\n")
    return {a: len(v) for a, v in got.items()}


if __name__ == "__main__":
    start = json.loads(STUDY.read_text())["started"] if STUDY.exists() else 0
    print(build(since=start))
