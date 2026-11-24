"""Phase 3 pilot. `uv run python scripts/run_pilot.py --mock` works offline; real runs need LP_REAL=1."""

import sys

from lp.cli import main

if __name__ == "__main__":
    sys.exit(main("pilot"))
