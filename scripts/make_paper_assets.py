"""Rebuild every paper table and figure from results/*/summary.json. The only way assets get into paper/."""

import json
import sys

from lp import report
from lp.config import REPO_ROOT

RUNS = ("core", "ksweep", "pilot")


def main() -> int:
    tables, figures = REPO_ROOT / "paper" / "tables", REPO_ROOT / "paper" / "figures"
    built = 0
    for run in RUNS:
        summary_path = REPO_ROOT / "results" / run / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text())
        report.write_tables(summary, tables / run)
        report.write_figures(summary, figures / run)
        built += 1
        print(f"built assets for {run}")
    if not built:
        print("no real results yet (results/<run>/summary.json); nothing to build", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
