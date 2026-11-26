"""Paired comparisons for H2-H4, on the same questions: a paired bootstrap of the difference plus exact McNemar.

- H2 (k): k-sweep, k = 1 vs k = 5 (qwen2.5:7b, hybrid), per dataset.
- H2 (retriever): core, BM25 vs hybrid at k = 5, per dataset and model.
- H3 (model size): core, llama3.1:8b vs llama3.2:3b (same family) at hybrid k = 5, per dataset.
- H4: across the core cells at hybrid k = 5 (dataset x model), Spearman correlation of closed-book accuracy with
  the lucky-pass rate.

Measures: lucky_pass (main rule), lucky_pass_all (secondary rule) and memory_lucky. Questions missing from one
side (a call that failed) are dropped from that comparison, so n is the paired count.
Writes results/comparisons.json.

Usage: uv run python scripts/compare_conditions.py
"""

import json
import sys
from collections import defaultdict

import numpy as np

from lp import stats
from lp.config import REPO_ROOT

RESULTS = REPO_ROOT / "results"
MEASURES = {
    "lucky_pass": lambda r: r["outcome"] == "lucky_pass",
    "lucky_pass_all": lambda r: r["outcome_all"] == "lucky_pass",
    "memory_lucky": lambda r: r["lucky_kind"] == "memory_lucky",
}
DATASETS = ["hotpotqa", "nq", "utm", "invented"]


def ranks(values: list[float]) -> np.ndarray:
    """Ranks 1..n, with tied values given the average of their ranks."""
    data = np.asarray(values, dtype=float)
    out = np.empty(len(data))
    for value in np.unique(data):
        where = np.flatnonzero(data == value)
        out[where] = np.argsort(np.argsort(data, kind="stable"), kind="stable")[where].mean() + 1
    return out


def spearman(x: list[float], y: list[float], permutations: int = 10000, seed: int = 0) -> dict:
    """Spearman's rho, with a two-sided permutation p-value (shuffle y, count |rho| at least as large)."""
    rx, ry = ranks(x), ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return {"rho": None, "p": None}
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rng = np.random.default_rng(seed)
    hits = sum(abs(np.corrcoef(rx, rng.permutation(ry))[0, 1]) >= abs(rho) - 1e-12 for _ in range(permutations))
    return {"rho": rho, "p": float((hits + 1) / (permutations + 1))}


def load(run: str) -> tuple[list[dict], dict]:
    records = [json.loads(line) for line in (RESULTS / run / "records.jsonl").open()]
    return records, json.loads((RESULTS / run / "summary.json").read_text())["meta"]


def by_cell(records: list[dict]) -> dict[tuple, dict[str, dict]]:
    cells: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in records:
        cells[(r["dataset"], r["model"], r["retriever"], r["k"])][r["qid"]] = r
    return cells


def compare(a: dict[str, dict], b: dict[str, dict], meta: dict) -> dict:
    """Rates under a minus rates under b, on the questions both have."""
    qids = sorted(a.keys() & b.keys())
    out = {"n": len(qids)}
    for rule, measure in MEASURES.items():
        xa = [measure(a[q]) for q in qids]
        xb = [measure(b[q]) for q in qids]
        out[rule] = {
            "a": stats.bootstrap_ci([float(x) for x in xa], meta["bootstrap_resamples"], meta["seed"]),
            "b": stats.bootstrap_ci([float(x) for x in xb], meta["bootstrap_resamples"], meta["seed"]),
            "diff": stats.paired_bootstrap_diff(
                [float(x) for x in xa], [float(x) for x in xb], meta["bootstrap_resamples"], meta["seed"]
            ),
            "mcnemar": stats.mcnemar(xa, xb),
        }
    return out


def main() -> int:
    core, core_meta = load("core")
    ksweep, ksweep_meta = load("ksweep")
    core_cells, k_cells = by_cell(core), by_cell(ksweep)
    out = {"note": "a minus b on the same questions; see the docstring of scripts/compare_conditions.py"}

    out["h2_k"] = [
        {"dataset": d, "a": "k=1", "b": "k=5"}
        | compare(k_cells[(d, "qwen2.5:7b", "hybrid", 1)], k_cells[(d, "qwen2.5:7b", "hybrid", 5)], ksweep_meta)
        for d in DATASETS
    ]
    out["h2_retriever"] = [
        {"dataset": d, "model": m, "a": "bm25", "b": "hybrid"}
        | compare(core_cells[(d, m, "bm25", 5)], core_cells[(d, m, "hybrid", 5)], core_meta)
        for d in DATASETS
        for m in core_meta["models"]
    ]
    out["h3_size"] = [
        {"dataset": d, "a": "llama3.1:8b", "b": "llama3.2:3b"}
        | compare(core_cells[(d, "llama3.1:8b", "hybrid", 5)], core_cells[(d, "llama3.2:3b", "hybrid", 5)], core_meta)
        for d in DATASETS
    ]

    summary = json.loads((RESULTS / "core" / "summary.json").read_text())
    points = [c for c in summary["cells"] if c["retriever"] == "hybrid" and c["k"] == 5]
    h4 = {}
    for label, cells in (("all", points), ("without_utm", [c for c in points if c["dataset"] != "utm"])):
        closed = [c["rates"]["closed_accuracy"]["value"] for c in cells]
        lucky = [c["rates"]["lucky_pass"]["value"] for c in cells]
        h4[label] = {"cells": len(cells)} | spearman(closed, lucky, seed=core_meta["seed"])
    out["h4_closed_vs_lucky"] = h4

    path = RESULTS / "comparisons.json"
    path.write_text(json.dumps(out, indent=1))
    for key in ("h2_k", "h2_retriever", "h3_size"):
        print(key)
        for row in out[key]:
            main_rule = row["lucky_pass"]
            label = " ".join(str(row[f]) for f in ("dataset", "model") if f in row)
            print(
                f"  {label:24} n = {row['n']:3}  diff {main_rule['diff']['value'] * 100:+.1f} "
                f"[{main_rule['diff']['lo'] * 100:.1f}, {main_rule['diff']['hi'] * 100:.1f}]  "
                f"McNemar p = {main_rule['mcnemar']['p']:.3g}"
            )
    print("h4", h4)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
