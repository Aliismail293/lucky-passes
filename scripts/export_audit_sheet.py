"""Export the Phase 5 human audit sheet: 50 fresh, random, judged RAG answers, half of them lucky passes.

"Fresh" means no question that appears in the pilot judge-check sheet (audit/pilot_judge_check.csv): the judge
was chosen on those items, so its accuracy there is optimistic. Ali labels `human_correct` (1 or 0); Claude
doesn't. `llm_judge` is the verdict the pipeline used (from contains-match or the LLM judge, see `judge_method`).
Seeded, so the same results give the same sheet. Refuses to overwrite an existing sheet, so labels can't be wiped.

Usage: uv run python scripts/export_audit_sheet.py results/core audit/audit_sheet.csv
"""

import csv
import json
import random
import sys
from pathlib import Path

from lp.config import REPO_ROOT

SIZE = 50
SEED = 2026
PILOT_CHECK = REPO_ROOT / "audit" / "pilot_judge_check.csv"
COLUMNS = [
    "audit_id", "dataset", "model", "retriever", "k", "qid", "question", "gold_answers", "prediction",
    "gold_retrieved", "judge_method", "llm_judge", "human_correct", "notes",
]


def excluded_qids(path: Path = PILOT_CHECK) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="") as handle:
        return {row["qid"] for row in csv.DictReader(handle)}


def pick(records: list[dict], excluded: set[str], size: int = SIZE, seed: int = SEED) -> list[dict]:
    """Half lucky passes (all of them if there are fewer), the rest from every other RAG answer."""
    pool = [r for r in records if r["qid"] not in excluded]
    lucky = sorted((r for r in pool if r["outcome"] == "lucky_pass"), key=_key)
    other = sorted((r for r in pool if r["outcome"] != "lucky_pass"), key=_key)
    rng = random.Random(seed)
    chosen_lucky = rng.sample(lucky, min(size // 2, len(lucky)))
    chosen_other = rng.sample(other, min(size - len(chosen_lucky), len(other)))
    chosen = chosen_lucky + chosen_other
    rng.shuffle(chosen)
    return chosen


def _key(record: dict) -> tuple:
    return (record["dataset"], record["model"], record["retriever"], record["k"], record["qid"])


def row(i: int, record: dict) -> dict:
    return {
        "audit_id": f"a{i:02d}",
        "dataset": record["dataset"],
        "model": record["model"],
        "retriever": record["retriever"],
        "k": record["k"],
        "qid": record["qid"],
        "question": record["question"],
        "gold_answers": " | ".join(record["answers"]),
        "prediction": record["pred_rag"],
        "gold_retrieved": int(record["hit_any"]),
        "judge_method": record["judge_rag"]["method"],
        "llm_judge": "correct" if record["correct_rag"] else "incorrect",
        "human_correct": "",
        "notes": "",
    }


def main() -> int:
    run_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    if out.exists():
        print(f"{out} already exists (it may hold labels); not overwriting. Pick another path.", file=sys.stderr)
        return 1
    records = [json.loads(line) for line in (run_dir / "records.jsonl").read_text().splitlines() if line.strip()]
    chosen = pick(records, excluded_qids(PILOT_CHECK))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(row(i, r) for i, r in enumerate(chosen, start=1))
    lucky = sum(r["outcome"] == "lucky_pass" for r in chosen)
    print(f"wrote {len(chosen)} rows ({lucky} lucky passes) to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
