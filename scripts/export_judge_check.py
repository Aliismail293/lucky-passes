"""Export every answer the LLM judge called correct although contains-match said no, for a human to label.

Why: in the pilot, all disagreements between the two judges went one way (LLM says correct, contains says
wrong). If many of those are wrong, the LLM judge inflates accuracy and closed-book accuracy. The filled-in sheet
(audit/pilot_judge_check.csv) has reference labels from a stronger model in `claude_label`, spot-checked by Ali,
whose edits go in `human_correct`; scripts/eval_judges.py uses it to choose the judge. They are not human labels.
This script refuses to overwrite an existing sheet, so the labels can't be wiped by re-running it.

Usage: uv run python scripts/export_judge_check.py results/pilot audit/pilot_judge_check.csv
"""

import csv
import json
import sys
from pathlib import Path

CONDITIONS = ("rag", "closed", "oracle")
COLUMNS = ["dataset", "qid", "condition", "question", "gold_answers", "prediction", "llm_judge", "human_correct"]


def disagreements(records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        for condition in CONDITIONS:
            verdict = record[f"judge_{condition}"]
            if verdict["contains"] is False and verdict["llm"] is True:
                rows.append(
                    {
                        "dataset": record["dataset"],
                        "qid": record["qid"],
                        "condition": condition,
                        "question": record["question"],
                        "gold_answers": " | ".join(record["answers"]),
                        "prediction": record[f"pred_{condition}"],
                        "llm_judge": "correct",
                        "human_correct": "",
                    }
                )
    return rows


def main() -> int:
    run_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    records = [json.loads(line) for line in (run_dir / "records.jsonl").read_text().splitlines() if line.strip()]
    if out.exists():
        # The check sheet holds labels once filled in; regenerating it would wipe them.
        print(f"{out} already exists (it may hold labels); not overwriting. Pick another path.", file=sys.stderr)
        return 1
    rows = disagreements(records)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
