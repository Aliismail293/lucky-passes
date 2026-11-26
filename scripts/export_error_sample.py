"""Draw the Phase 5 error-analysis sample: 30 random lucky passes from a run (main rule), one per question and model.

Writes a CSV with the record fields plus empty `category_claude` and `note_claude` columns. Claude fills these
(memory / guess / judge error / bad question / answer in a non-gold retrieved chunk); they are a model's reading,
not human labels, and Ali's audit (audit/audit_sheet.csv) is the human check. Seeded, so the same results give the
same sample. Refuses to overwrite an existing file, so the categories can't be wiped.

Usage: uv run python scripts/export_error_sample.py results/core results/core/error_sample.csv
"""

import csv
import json
import random
import sys
from pathlib import Path

SIZE = 30
SEED = 13
COLUMNS = [
    "row",
    "dataset",
    "model",
    "retriever",
    "qid",
    "question",
    "gold_answers",
    "rag_answer",
    "closed_book_answer",
    "lucky_kind",
    "judge_method",
    "category_claude",
    "note_claude",
]


def sample(records: list[dict], size: int = SIZE, seed: int = SEED) -> list[dict]:
    first: dict[tuple, dict] = {}
    for r in records:
        if r["outcome"] == "lucky_pass":
            first.setdefault((r["qid"], r["model"]), r)
    pool = sorted(first.values(), key=lambda r: (r["qid"], r["model"]))
    random.seed(seed)
    return random.sample(pool, min(size, len(pool)))


def main(argv: list[str]) -> int:
    run_dir, out = Path(argv[0]), Path(argv[1])
    if out.exists():
        print(f"{out} exists; not overwriting", file=sys.stderr)
        return 1
    records = [json.loads(line) for line in (run_dir / "records.jsonl").open()]
    rows = sample(records)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for i, r in enumerate(rows):
            writer.writerow(
                {
                    "row": i,
                    "dataset": r["dataset"],
                    "model": r["model"],
                    "retriever": r["retriever"],
                    "qid": r["qid"],
                    "question": r["question"],
                    "gold_answers": " | ".join(r["answers"]),
                    "rag_answer": r["pred_rag"],
                    "closed_book_answer": r["pred_closed"],
                    "lucky_kind": r["lucky_kind"],
                    "judge_method": r["judge_rag"]["method"],
                    "category_claude": "",
                    "note_claude": "",
                }
            )
    print(f"wrote {len(rows)} lucky passes to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
