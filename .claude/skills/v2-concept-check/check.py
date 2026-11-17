"""Mechanical half of the v2 concept check. Run from the repo root:

    uv run python .claude/skills/v2-concept-check/check.py            # every concept
    uv run python .claude/skills/v2-concept-check/check.py 02_liquidity

It cannot judge whether the logic matches what Sharif meant; it finds the things that usually give a copy away
(values lifted from an example, tests that lean on a real day, rules with no words of his behind them) and lists
what a reader must still judge. Exit code 1 if anything FAILS.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "v2"
PLAIN = {0, 1, 2, 3, -1}                                   # counting numbers a three-candle rule needs
V1 = ("ict_engine", "research", "hunt_scan", "hunt_watch", "live_recipe", "live_snapshot", "read_build")
REAL = ("today.json", "out/live", "dukascopy", ".parquet", "reports/", "data/bars", "overlay.json")
TF = re.compile(r"""["'](1m|5m|15m|30m|1h|4h|1D|1W|1M|daily|weekly|monthly)["']""")
ASSET = re.compile(r"\b(US100|US500|US30|NQ|ES|YM|XAUUSD|XAGUSD|DXY|EURUSD|UK100|DE40|US2000|FTSE|DAX|gold|silver)\b")
DATE = re.compile(r"\b20[12]\d-\d\d-\d\d\b")


def numbers(text: str) -> set[str]:
    """Prices and other long numbers written in a lesson (example values): 10,991 / 26076 / 103.33."""
    out = set()
    for m in re.finditer(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])\d{4,}(?:\.\d+)?|(?<![\w.,])\d{2,3}\.\d{2,}", text):
        n = m.group().replace(",", "")
        if not re.fullmatch(r"20[12]\d", n):                # a year is not a price
            out.add(n.rstrip("0").rstrip(".") if "." in n else n)
    return out


def literals(path: Path) -> list[tuple[int, object]]:
    out = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool) and node.value not in PLAIN:
            out.append((node.lineno, node.value))
    return sorted(out)


def check(folder: Path) -> tuple[list[str], list[str], list[str]]:
    fail, judge, ok = [], [], []
    lessons = sorted(folder.glob("*.md"))
    tools = sorted(p for p in folder.glob("*.py") if not p.name.startswith("test_"))
    tests = sorted(folder.glob("test_*.py"))
    text = "\n".join(p.read_text() for p in lessons)

    # 1. the lesson is his words
    if not (folder / "lesson.md").exists():
        fail.append("no lesson.md")
    else:
        quotes = len(re.findall(r'"[^"\n]{12,}"', text))
        (ok if quotes >= 3 else fail).append(f"lesson quotes him {quotes} time(s)" + ("" if quotes >= 3 else ": a lesson must carry his own words"))
        (ok if re.search(r"\b(1[0-9]|2[0-9]|[1-9]) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* 20\d\d", text) else fail).append("lesson says when it was taught / confirmed")
        (ok if re.search(r"(?i)\b(mine|my choice|my reading|not his|not yet confirmed|unconfirmed)\b", text) else judge).append(
            "lesson separates what is mine from what is his" if re.search(r"(?i)\b(mine|not his)\b", text) else "lesson names nothing as mine: is every rule really his words?")

    # 2. tools: no v1, no example values, every number accounted for
    lesson_numbers = numbers(text)
    for t in tools:
        src = t.read_text()
        hit = [v for v in V1 if re.search(rf"^\s*(from|import)\s+{v}\b", src, re.M)]
        (fail if hit else ok).append(f"{t.name}: imports v1 ({', '.join(hit)})" if hit else f"{t.name}: reads nothing from v1")
        code = "\n".join(line.split("#")[0] for line in re.sub(r'"""(?:.|\n)*?"""', "", src).splitlines())    # code only, no docstrings or comments
        for rx, what in ((TF, "a named timeframe"), (ASSET, "an instrument's name"), (DATE, "a calendar date")):
            m = rx.search(code)
            if m:
                fail.append(f"{t.name}: {what} in the code ({m.group()}): a tool reads any chart the same way")
        lifted = sorted(n for n in lesson_numbers if re.search(rf"(?<![\d.]){re.escape(n)}(?![\d.])", code))
        if lifted:
            fail.append(f"{t.name}: value(s) from the lesson's examples appear in the code: {', '.join(lifted)}")
        nums = literals(t)
        if nums:
            judge.append(f"{t.name}: numbers to tie to his words or to 'mine': " + ", ".join(f"{v} (line {ln})" for ln, v in nums))
        if not re.search(r"(?i)mine|my choice", src) and nums:
            judge.append(f"{t.name}: has numbers but names no choice as mine")
        if not (folder / f"test_{t.stem}.py").exists():
            fail.append(f"{t.name}: no test_{t.stem}.py")

    # 3. tests: hand-built, more than one scale and timeframe, no look-ahead, no real day
    for t in tests:
        src = t.read_text()
        real = [r for r in REAL if r in src]
        (fail if real else ok).append(f"{t.name}: leans on real data ({', '.join(real)})" if real else f"{t.name}: hand-built candles only")
        lifted = sorted(n for n in lesson_numbers if re.search(rf"(?<![\d.]){re.escape(n)}(?![\d.])", src))
        if lifted:
            fail.append(f"{t.name}: value(s) from the lesson's examples appear in the tests: {', '.join(lifted)}")
        (ok if re.search(r"parametrize\([\"']k[\"']", src) and re.search(r"parametrize\([\"']step[\"']", src) else fail).append(f"{t.name}: same shape at several price scales and timeframes")
        (ok if re.search(r"def test_\w*(before_it_happened|look_?ahead|not_known)", src) else fail).append(f"{t.name}: a no-look-ahead test")
        n = len(re.findall(r"^def test_", src, re.M))
        (ok if n >= 5 else judge).append(f"{t.name}: {n} tests" + ("" if n >= 5 else " (few: does each sentence of the lesson have one?)"))
    if tools and not tests:
        fail.append("tools without tests")

    # 4. the checklist knows about it
    num = folder.name.split("_")[0]
    mig = (V2 / "MIGRATION.md").read_text()
    (ok if re.search(rf"^\| {num} \|", mig, re.M) else fail).append(f"MIGRATION.md has a row for {num}")
    return fail, judge, ok


def main() -> int:
    want = sys.argv[1:]
    folders = [f for f in sorted((V2 / "concepts").iterdir()) if f.is_dir() and (not want or f.name in want or f.name.split("_", 1)[-1] in want)]
    bad = 0
    for f in folders:
        fail, judge, ok = check(f)
        bad += len(fail)
        print(f"\n== {f.name}: {'FAIL' if fail else 'passes the mechanical check'}")
        for x in fail:
            print(f"  FAIL   {x}")
        for x in judge:
            print(f"  JUDGE  {x}")
        for x in ok:
            print(f"  ok     {x}")
    r = subprocess.run(["uv", "run", "pytest", "-q", "v2"], cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or ["no output"])[-1]
    print(f"\n== tests: {tail}")
    bad += r.returncode != 0
    print("\nRESULT:", "FAIL" if bad else "mechanical check passed; now do the reading in SKILL.md (the JUDGE lines and the lesson-against-code table)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
