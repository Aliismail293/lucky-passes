"""Phase 4 k-sweep (hybrid, qwen2.5:7b, k = 1, 3, 5). Real runs need LP_REAL=1."""

import sys

from lp.cli import main

if __name__ == "__main__":
    sys.exit(main("ksweep"))
