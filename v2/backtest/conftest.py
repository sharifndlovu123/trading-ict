"""Lets the backtest import the concept tools by name, the same way the concepts' own tests do."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in sorted((HERE.parent / "concepts").glob("[0-9]*_*")) + [HERE, HERE.parent / "chart"]:
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
