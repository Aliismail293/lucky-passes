"""Post-hoc (not pre-registered) sensitivity check for the UTM calendar's lucky-pass rate.

The calendar repeats field values across course entries ("Mode of delivery: In Class", "Distribution
requirement: Science"). A question whose answer is one of those values can be answered from any course's entry,
so "no gold passage retrieved" doesn't mean the answer wasn't in the context. This script calls an answer
boilerplate when its normalised text occurs, as whole words, in at least THRESHOLD of the corpus chunks, and
re-summarises the UTM cells without those questions, for a sweep of thresholds (the threshold was chosen after
seeing the data, so the sweep shows the conclusion doesn't hinge on it). scripts/extra_analyses.py has a
threshold-free version: lucky passes whose retrieved passages contain the answer. The pre-registered numbers in
summary.json are unchanged.

Usage: uv run python scripts/utm_sensitivity.py results/core
"""

import json
import sys
from pathlib import Path

from lp import report
from lp.config import load_config
from lp.datasets import chunk_corpus
from lp.judge import normalize
from lp.runner import corpus_folder

THRESHOLDS = (2, 3, 5, 10, 15, 20)


def chunk_texts(config_path: Path) -> dict[str, str]:
    chunks = chunk_corpus(corpus_folder(load_config(config_path), "utm"))
    return {f"utm:{c.chunk_id[:16]}": f" {normalize(c.text)} " for c in chunks}


def answer_frequency(answers: list[str], texts: dict[str, str]) -> int:
    """In how many chunks the most widespread gold answer occurs, as whole words after normalising."""
    return max(sum(f" {normalize(a)} " in t for t in texts.values()) for a in answers if normalize(a))


def main(argv: list[str]) -> int:
    run_dir = Path(argv[0]) if argv else Path("results/core")
    summary = json.loads((run_dir / "summary.json").read_text())
    meta = summary["meta"]
    texts = chunk_texts(Path(meta["config"]))
    records = [json.loads(line) for line in (run_dir / "records.jsonl").open()]
    utm = [r for r in records if r["dataset"] == "utm"]
    freq = {r["qid"]: answer_frequency(r["answers"], texts) for r in utm}
    lucky = [r for r in utm if r["outcome"] == "lucky_pass"]
    out = {
        "note": "post-hoc sensitivity analysis, not pre-registered; see the docstring of scripts/utm_sensitivity.py",
        "chunks": len(texts),
        "questions": len(freq),
        "thresholds": {},
    }
    for threshold in THRESHOLDS:
        boiler = {q for q, f in freq.items() if f >= threshold}
        kept = [r for r in utm if r["qid"] not in boiler]
        out["thresholds"][str(threshold)] = {
            "boilerplate_questions": len(boiler),
            "lucky_records": len(lucky),
            "lucky_records_boilerplate": sum(r["qid"] in boiler for r in lucky),
            "cells_without_boilerplate": report.summarize(kept, meta["bootstrap_resamples"], meta["seed"])["cells"],
        }
    path = run_dir / "utm_sensitivity.json"
    path.write_text(json.dumps(out, indent=1))
    for threshold, block in out["thresholds"].items():
        print(
            f"threshold {threshold}: {block['boilerplate_questions']}/{out['questions']} boilerplate questions, "
            f"{block['lucky_records_boilerplate']}/{block['lucky_records']} UTM lucky-pass records"
        )
        for cell in block["cells_without_boilerplate"]:
            rate = report.pct(cell["rates"]["lucky_pass"])
            print(f"  {cell['model']:12} {cell['retriever']:7} n = {cell['n']:3}  {rate}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
