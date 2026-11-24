"""Shared command line for scripts/run_pilot.py, run_core.py and run_ksweep.py."""

import argparse
import sys

from lp.config import REPO_ROOT, load_config
from lp.runner import EXIT_NEEDS_APPROVAL, NeedsApproval, run


def main(config_name: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Run configs/{config_name}.yaml")
    parser.add_argument("--mock", action="store_true", help="toy data and a fake model, no Ollama needed")
    parser.add_argument("--approve-hours", type=float, default=None, help="allow a run estimated up to this many hours")
    parser.add_argument("--estimate-only", action="store_true", help="print the time estimate and stop")
    args = parser.parse_args(argv)
    path = REPO_ROOT / "configs" / f"{config_name}.yaml"
    try:
        run_dir = run(
            load_config(path), path, mock=args.mock, approve_hours=args.approve_hours, estimate_only=args.estimate_only
        )
    except NeedsApproval:
        print("Stopped: the estimate is over the time limit. See NEEDS_ALI.md for options.", file=sys.stderr)
        return EXIT_NEEDS_APPROVAL
    print(f"Results in {run_dir}")
    return 0
