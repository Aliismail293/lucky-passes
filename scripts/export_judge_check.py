"""Export every answer the LLM judge called correct although contains-match said no, for a human to label.

Why: in the pilot, all disagreements between the two judges went one way (LLM says correct, contains says
wrong). If many of those are wrong, the LLM judge inflates accuracy and closed-book accuracy. Ali's labels in
the `human_correct` column (1 / 0) measure that, and give a fixed judge prompt something to be tested against.

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
