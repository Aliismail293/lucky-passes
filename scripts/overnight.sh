#!/bin/bash
# Run experiments unattended on the Mac. Keeps the Mac awake for exactly as long as this script runs.
#
#   bash scripts/overnight.sh pilot                     Phase 3 pilot
#   bash scripts/overnight.sh full                      core grid, then the k-sweep
#   bash scripts/overnight.sh full --approve-hours 14   same, allowing a run estimated up to 14 h
#   bash scripts/overnight.sh judges --prompt v3 --out results/judge_selection_v3
#                                                       judge comparison on the labelled pilot items
#
# Safe to stop (Ctrl+C) or crash: run the same command again and it resumes from the cache.
# Everything is logged to logs/ and to ~/Desktop/research-design/research-progress.md.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

STAGE="${1:-pilot}"
shift || true
EXTRA=("$@")

mkdir -p logs
LOG="logs/overnight-${STAGE}-$(date +%Y%m%d-%H%M).log"
export LP_REAL=1

echo "Logging to $LOG"
caffeinate -dimsu -w $$ &

run_step() {
  echo "=== $* ($(date)) ===" | tee -a "$LOG"
  uv run python "$@" 2>&1 | tee -a "$LOG"
  return "${PIPESTATUS[0]}"
}

case "$STAGE" in
  pilot)
    run_step scripts/download_data.py --only hotpotqa || exit 1
    run_step scripts/preflight.py pilot || exit 1
    run_step scripts/run_pilot.py ${EXTRA[@]+"${EXTRA[@]}"}
    ;;
  full)
    run_step scripts/download_data.py || exit 1
    run_step scripts/preflight.py core || exit 1
    run_step scripts/run_core.py ${EXTRA[@]+"${EXTRA[@]}"} || exit $?
    run_step scripts/run_ksweep.py ${EXTRA[@]+"${EXTRA[@]}"} || exit $?
    run_step scripts/make_paper_assets.py
    ;;
  judges)
    run_step scripts/eval_judges.py ${EXTRA[@]+"${EXTRA[@]}"}
    ;;
  core|ksweep)
    run_step scripts/preflight.py "$STAGE" || exit 1
    run_step "scripts/run_${STAGE}.py" ${EXTRA[@]+"${EXTRA[@]}"}
    ;;
  *)
    echo "Unknown stage: $STAGE (use pilot, full, core, ksweep or judges)"
    exit 2
    ;;
esac
STATUS=$?
echo "=== finished with status $STATUS ($(date)) ===" | tee -a "$LOG"
if [ "$STATUS" -eq 3 ]; then
  echo "Stopped before starting: over the time limit. Open ~/Desktop/research-design/NEEDS_ALI.md" | tee -a "$LOG"
fi
exit "$STATUS"
