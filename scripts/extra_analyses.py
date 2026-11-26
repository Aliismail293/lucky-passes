"""Analyses added after the internal review (Phase 7). All are computed from the committed records; no model calls.

Per cell (dataset x model x retriever x k) of the core run and the k-sweep:
- exact (Clopper-Pearson) intervals for the lucky-pass and memory-lucky rates, which don't collapse to [0, 0];
- accuracy *given that no gold passage was retrieved*, with its n: the chance that an answer-only score counts a
  miss as a success. The lucky-pass rate is this times the miss rate, so it can be small just because misses are;
- on HotpotQA, accuracy given that *not all* gold passages were retrieved (the measure in Jonah et al.);
- an answer-in-context rule: a lucky pass whose retrieved passages contain a gold answer string (whole words,
  normalised) isn't evidence of an answer from outside the context. No threshold to choose;
- a judge-free lucky-pass rate (contains-match only), which bounds what the LLM judge contributes.

Also: worst/best-case bounds for the one missing call, exact intervals for the error-sample categories, and paired
McNemar tests of closed-book accuracy for llama3.1:8b vs llama3.2:3b. Writes results/extra_analyses.json.

Usage: uv run python scripts/extra_analyses.py
"""

import csv
import json
import sys
from collections import Counter, defaultdict

from lp import stats
from lp.config import REPO_ROOT, load_config
from lp.datasets import chunk_corpus
from lp.judge import normalize
from lp.runner import corpus_folder, load_static_datasets

RESULTS = REPO_ROOT / "results"


def passage_texts() -> dict[str, str]:
    """Normalised text (title and body) of every passage in every corpus, keyed by passage id."""
    config = load_config(REPO_ROOT / "configs" / "core.yaml")
    loaded, _, _ = load_static_datasets(config, mock=False)
    texts = {}
    for dataset in loaded.values():
        for pid, p in dataset.passages.items():
            texts[pid] = f" {normalize(p.title + ' ' + p.text)} "
    for name in ("utm", "invented"):
        for c in chunk_corpus(corpus_folder(config, name)):
            texts[f"{name}:{c.chunk_id[:16]}"] = f" {normalize(c.text)} "
    return texts


def answer_in_context(record: dict, texts: dict[str, str]) -> bool:
    golds = [f" {normalize(a)} " for a in record["answers"] if normalize(a)]
    return any(g in texts[pid] for pid in record["retrieved_ids"] for g in golds)


def cell_analysis(group: list[dict], texts: dict[str, str]) -> dict:
    n = len(group)
    lucky = [r for r in group if r["outcome"] == "lucky_pass"]
    no_gold = [r for r in group if not r["hit_any"]]
    not_all = [r for r in group if not r["hit_all"]]
    lucky_outside = [r for r in lucky if not answer_in_context(r, texts)]
    out = {
        "n": n,
        "lucky_pass_exact": stats.clopper_pearson(len(lucky), n),
        "memory_lucky_exact": stats.clopper_pearson(sum(r["lucky_kind"] == "memory_lucky" for r in group), n),
        "no_gold_retrieved": len(no_gold),
        "accuracy_given_no_gold": stats.clopper_pearson(sum(r["correct_rag"] for r in no_gold), len(no_gold)),
        "lucky_answer_in_context": len(lucky) - len(lucky_outside),
        "lucky_answer_not_in_context_exact": stats.clopper_pearson(len(lucky_outside), n),
        "lucky_contains_only_exact": stats.clopper_pearson(
            sum(r["judge_rag"]["method"] == "contains" for r in lucky), n
        ),
    }
    if group[0]["multi_hop"] or any(r["multi_hop"] for r in group):
        out["not_all_gold_retrieved"] = len(not_all)
        out["accuracy_given_not_all_gold"] = stats.clopper_pearson(sum(r["correct_rag"] for r in not_all), len(not_all))
    return out


def by_cell(records: list[dict]) -> dict[tuple, list[dict]]:
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        cells[(r["dataset"], r["model"], r["retriever"], r["k"])].append(r)
    return cells


def pooled_no_gold(records: list[dict]) -> dict:
    """Accuracy given no gold retrieved, pooled over models and retrievers per dataset (records, not questions)."""
    out = {}
    for name in sorted({r["dataset"] for r in records}):
        misses = [r for r in records if r["dataset"] == name and not r["hit_any"]]
        out[name] = stats.clopper_pearson(sum(r["correct_rag"] for r in misses), len(misses))
        out[name]["distinct_questions"] = len({r["qid"] for r in misses})
    return out


def missing_call_bounds(records: list[dict]) -> list[dict]:
    """The core run lacks one llama3.1:8b UTM answer; count it as lucky (worst case) or not (best case)."""
    rows = []
    for (dataset, model, retriever, _k), group in sorted(by_cell(records).items()):
        if dataset == "utm" and model == "llama3.1:8b":
            lucky = sum(r["outcome"] == "lucky_pass" for r in group)
            rows.append(
                {
                    "retriever": retriever,
                    "observed": stats.clopper_pearson(lucky, len(group)),
                    "if_not_lucky": stats.clopper_pearson(lucky, len(group) + 1),
                    "if_lucky": stats.clopper_pearson(lucky + 1, len(group) + 1),
                }
            )
    return rows


def closed_book_size(records: list[dict]) -> dict:
    """Paired McNemar, closed-book accuracy, llama3.1:8b vs llama3.2:3b (closed-book doesn't depend on retrieval)."""
    out = {}
    for name in sorted({r["dataset"] for r in records}):
        big = {r["qid"]: r["correct_closed"] for r in records if r["dataset"] == name and r["model"] == "llama3.1:8b"}
        small = {r["qid"]: r["correct_closed"] for r in records if r["dataset"] == name and r["model"] == "llama3.2:3b"}
        qids = sorted(big.keys() & small.keys())
        out[name] = {"n": len(qids)} | stats.mcnemar([big[q] for q in qids], [small[q] for q in qids])
    return out


def error_sample_intervals() -> dict:
    with (RESULTS / "core" / "error_sample.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    counts = Counter(r["category_claude"] for r in rows)
    return {category: stats.clopper_pearson(k, len(rows)) for category, k in sorted(counts.items())}


def main() -> int:
    texts = passage_texts()
    out = {"note": "post-review analyses; see the docstring of scripts/extra_analyses.py"}
    for run in ("core", "ksweep"):
        records = [json.loads(line) for line in (RESULTS / run / "records.jsonl").open()]
        out[run] = {
            "cells": [
                {"dataset": d, "model": m, "retriever": r, "k": k} | cell_analysis(group, texts)
                for (d, m, r, k), group in sorted(by_cell(records).items())
            ],
            "accuracy_given_no_gold_pooled": pooled_no_gold(records),
        }
        if run == "core":
            out[run]["missing_call_bounds"] = missing_call_bounds(records)
            out[run]["closed_book_llama_8b_vs_3b"] = closed_book_size(records)
    out["error_sample"] = error_sample_intervals()

    path = RESULTS / "extra_analyses.json"
    path.write_text(json.dumps(out, indent=1))
    for cell in out["core"]["cells"]:
        if cell["retriever"] == "hybrid":
            acc = cell["accuracy_given_no_gold"]
            given = f"{acc['value'] * 100:.0f}% of {acc['n']}" if acc["n"] else "no misses"
            print(
                f"{cell['dataset']:8} {cell['model']:11} lucky {stats_pct(cell['lucky_pass_exact'])} "
                f"| correct when no gold: {given} | lucky with answer not in context "
                f"{stats_pct(cell['lucky_answer_not_in_context_exact'])}"
            )
    print(
        "pooled accuracy given no gold (core):",
        {d: stats_pct(v) for d, v in out["core"]["accuracy_given_no_gold_pooled"].items()},
    )
    print(f"wrote {path}")
    return 0


def stats_pct(ci: dict) -> str:
    if ci["value"] is None:
        return "n = 0"
    return f"{ci['value'] * 100:.1f} [{ci['lo'] * 100:.1f}, {ci['hi'] * 100:.1f}] (n = {ci['n']})"


if __name__ == "__main__":
    sys.exit(main())
