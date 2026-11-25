"""Check a run's PILOT_REPORT.md against its summary.json, and summary.json against records.jsonl.

Phase 3 "done when": the pilot report's numbers match the results files. Two independent checks:
1. Every number in the report (decimals, percentages, integers of 11 or more) appears in summary.json.
   Only summary.json counts as evidence here; the report can't vouch for itself.
2. Every count and rate in summary.json is recomputed from the per-question records.jsonl.

Usage: uv run python scripts/check_pilot_report.py results/pilot [other.md ...]
"""

import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("check_numbers", HERE / "check_numbers.py")
assert _spec is not None and _spec.loader is not None
check_numbers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_numbers)

# Rates in summary.json, and how to recompute each one from a record (n = all records in the cell,
# except lucky_share_of_correct whose n is the correct answers).
RATE_RULES = {
    "accuracy": lambda r: r["correct_rag"],
    "true_pass": lambda r: r["outcome"] == "true_pass",
    "lucky_pass": lambda r: r["outcome"] == "lucky_pass",
    "memory_lucky": lambda r: r["lucky_kind"] == "memory",
    "guess_lucky": lambda r: r["lucky_kind"] == "guess",
    "grounding_failure": lambda r: r["outcome"] == "grounding_failure",
    "miss": lambda r: r["outcome"] == "miss",
    "hit_any": lambda r: r["hit_any"],
    "hit_all": lambda r: r["hit_all"],
    "lucky_pass_all": lambda r: r["outcome_all"] == "lucky_pass",
    "closed_accuracy": lambda r: r["correct_closed"],
    "oracle_accuracy": lambda r: r["correct_oracle"],
    "overstatement": lambda r: r["outcome"] == "lucky_pass",
}


def report_numbers_not_in_summary(report: str, summary: dict) -> list[tuple[int, str]]:
    """Numbers inside summary strings (the started/finished timestamps) count, and so does wall time in minutes."""
    allowed: set[str] = set()
    derived = [summary["meta"]["timing"]["wall_seconds"] / 60] if "timing" in summary.get("meta", {}) else []
    for value in [*_numbers(summary), *derived]:
        for v in (value, value * 100):
            allowed.update({f"{v:.0f}", f"{v:.1f}", f"{v:.2f}", f"{v:.3f}"})
        if float(value).is_integer():
            allowed.add(str(int(value)))
    return check_numbers.unverified_numbers(report, allowed)


def _numbers(obj):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield float(obj)
    elif isinstance(obj, str):
        yield from (float(m) for m in re.findall(r"\d+(?:\.\d+)?", obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _numbers(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _numbers(v)


def cell_mismatches(cell: dict, records: list[dict]) -> list[str]:
    problems = []
    name = f"{cell['dataset']}/{cell['model']}/{cell['retriever']}/k={cell['k']}"
    if len(records) != cell["n"]:
        problems.append(f"{name}: n is {cell['n']} in summary but {len(records)} records")
    counts = Counter(r["outcome"] for r in records)
    for outcome, expected in cell["counts"].items():
        if counts.get(outcome, 0) != expected:
            problems.append(f"{name}: {outcome} count {expected} in summary, {counts.get(outcome, 0)} in records")
    for subset, rates, rows in (
        ("all", cell["rates"], records),
        ("oracle_ok", cell.get("rates_oracle_ok", {}), [r for r in records if r["correct_oracle"]]),
    ):
        for rate_name, rule in RATE_RULES.items():
            if rate_name not in rates:
                continue
            got = sum(bool(rule(r)) for r in rows) / len(rows) if rows else 0.0
            if abs(got - rates[rate_name]["value"]) > 1e-9 or rates[rate_name]["n"] != len(rows):
                problems.append(f"{name} [{subset}] {rate_name}: summary {rates[rate_name]}, records {got:.4f}")
        if "lucky_share_of_correct" in rates:
            correct = [r for r in rows if r["correct_rag"]]
            got = sum(r["outcome"] == "lucky_pass" for r in correct) / len(correct) if correct else 0.0
            if abs(got - rates["lucky_share_of_correct"]["value"]) > 1e-9:
                problems.append(f"{name} [{subset}] lucky_share_of_correct: summary differs from records ({got:.4f})")
    return problems


def judge_agreement(records: list[dict]) -> dict:
    table: Counter[str] = Counter()
    for record in records:
        for condition in ("rag", "closed", "oracle"):
            judge = record[f"judge_{condition}"]
            if judge["contains"] is None or judge["llm"] is None:
                continue
            key = {(True, True): "both_correct", (False, False): "both_wrong", (True, False): "contains_only"}.get(
                (judge["contains"], judge["llm"]), "llm_only"
            )
            table[key] += 1
    n = sum(table.values())
    return {"n": n, "agree": table["both_correct"] + table["both_wrong"], "table": dict(table)}


def main() -> int:
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/pilot")
    summary = json.loads((run_dir / "summary.json").read_text())
    records = [json.loads(line) for line in (run_dir / "records.jsonl").read_text().splitlines() if line.strip()]

    problems = []
    # The report, plus any other write-up named on the command line (e.g. the 1-page summary).
    for doc in [run_dir / "PILOT_REPORT.md", *(Path(p) for p in sys.argv[2:])]:
        for ln, num in report_numbers_not_in_summary(doc.read_text(), summary):
            problems.append(f"{doc.name} line {ln}: {num} not in summary.json")
    for cell in summary["cells"]:
        rows = [
            r
            for r in records
            if (r["dataset"], r["model"], r["retriever"], r["k"])
            == (cell["dataset"], cell["model"], cell["retriever"], cell["k"])
        ]
        problems += cell_mismatches(cell, rows)
    agreement = judge_agreement(records)
    expected = summary["judge_agreement"]
    for key in ("n", "agree"):
        if agreement[key] != expected[key]:
            problems.append(f"judge_agreement {key}: summary {expected[key]}, records {agreement[key]}")
    for key, value in expected["table"].items():
        if agreement["table"].get(key, 0) != value:
            problems.append(f"judge_agreement table {key}: summary {value}, records {agreement['table'].get(key, 0)}")

    for problem in problems:
        print(problem)
    print(f"checked {len(summary['cells'])} cells, {len(records)} records:", "FAIL" if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
