"""v2 tests import only from v2 (never from v1's ict_engine or research/scripts)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
