"""v2 tests import only from v2 (never from v1's ict_engine or research/scripts). Each concept folder is put on the
path, so a test imports its own eyes file by name (`from bias_eyes import ...`)."""
import sys
from pathlib import Path

for d in sorted((Path(__file__).parent / "concepts").iterdir()):
    if d.is_dir():
        sys.path.insert(0, str(d))
