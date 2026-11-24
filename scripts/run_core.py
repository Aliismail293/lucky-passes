"""Phase 4 core grid (4 datasets x 3 models x 3 retrievers, k=5). Real runs need LP_REAL=1."""

import sys

from lp.cli import main

if __name__ == "__main__":
    sys.exit(main("core"))
