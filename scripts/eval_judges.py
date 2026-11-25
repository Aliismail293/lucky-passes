"""Compare candidate LLM judges (judge v2: non-answer rule + strict prompt) on the labelled pilot judge-check items.

The items are the 149 pilot answers where the v1 judge (llama3.1:8b) said "correct" and contains-match said no.
Reference labels: the `claude_label` column (correct / incorrect / unclear), written by Claude (Opus), a stronger
model. Where `human_correct` says "edited by Ali", Ali's label in that cell wins. These are reference labels from a
stronger model, spot-checked by the author, NOT human labels. "unclear" rows are left out of agreement and listed
as candidate bad questions.

The labels are only read, never written. Because the default judge is chosen on these items, its agreement here is
optimistic; an unbiased judge-accuracy number needs fresh items (the Phase 5 human audit).

Usage:
  LP_REAL=1 uv run python scripts/eval_judges.py [--csv audit/pilot_judge_check.csv] [--out results/judge_selection]
                                                 [--judges llama3.1:8b gemma2:9b qwen2.5:7b] [--mock]
Every judge call goes through the normal cache (data/cache/calls.sqlite) with the run's parameters, so the
re-run pilot reuses them.
"""

import argparse
import csv
import itertools
import json
import os
import sys
from collections import Counter
from pathlib import Path

from lp import judge
from lp.cache import Cache
from lp.config import REPO_ROOT, family, load_config
from lp.runner import Clients
from lp.stats import bootstrap_ci

LABELS = ("correct", "incorrect", "unclear")
DEFAULT_JUDGES = ["llama3.1:8b", "gemma2:9b", "qwen2.5:7b"]
GENERATORS = ["qwen2.5:7b", "llama3.1:8b", "llama3.2:3b"]
"""The core config's generator models; each needs a judge from another family."""
PILOT_GENERATOR = "qwen2.5:7b"
"""Every labelled answer was written by this model, so a qwen judge here is grading its own family's answers."""
MIN_AGREEMENT = 0.90


def reference_label(row: dict) -> str:
    """Ali's edit wins over Claude's label. An "edited by Ali" cell must contain exactly one of the label words."""
    edit = row.get("human_correct", "").strip().lower()
    if "edited by ali" in edit:
        words = {w.strip(" .,:;()[]\"'") for w in edit.replace("edited by ali", " ").split()}
        found = [label for label in LABELS if label in words]
        if len(found) != 1:
            raise ValueError(f"can't read Ali's label from human_correct={row['human_correct']!r} ({row['qid']})")
        return found[0]
    label = row["claude_label"].strip().lower()
    if label not in LABELS:
        raise ValueError(f"unknown claude_label {row['claude_label']!r} ({row['qid']}, {row['condition']})")
    return label


def read_items(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["reference"] = reference_label(row)
        row["reference_source"] = "ali" if "edited by ali" in row.get("human_correct", "").lower() else "claude"
    return rows


def score(items: list[dict], accepted: list[bool]) -> dict:
    """Agreement with the reference labels, false-accept rate (on items labelled incorrect) and false-reject rate
    (on items labelled correct). Unclear items are excluded."""
    pairs = [(it, ok) for it, ok in zip(items, accepted, strict=True) if it["reference"] != "unclear"]
    agree = [float((it["reference"] == "correct") == ok) for it, ok in pairs]
    wrong = [float(ok) for it, ok in pairs if it["reference"] == "incorrect"]
    right = [float(not ok) for it, ok in pairs if it["reference"] == "correct"]
    return {
        "n": len(pairs),
        "agreement": bootstrap_ci(agree, seed=13),
        "false_accept_rate": bootstrap_ci(wrong, seed=13),
        "false_reject_rate": bootstrap_ci(right, seed=13),
        "by_condition": {
            cond: sum((it["reference"] == "correct") == ok for it, ok in pairs if it["condition"] == cond)
            / max(1, sum(it["condition"] == cond for it, _ in pairs))
            for cond in sorted({it["condition"] for it, _ in pairs})
        },
    }


def choose(results: dict[str, dict]) -> dict[str, str | None]:
    """For each generator family, the candidate with the best agreement among judges of a different family
    (ties: lower false-accept rate, then fewer judges, then name). A candidate "a+b" is two judges that must both
    accept; every one of its judges must be of another family than the generator."""
    out: dict[str, str | None] = {}
    for gen_family in sorted({family(g) for g in GENERATORS}):
        eligible = [j for j in results if all(family(part) != gen_family for part in j.split("+"))]
        ranked = sorted(
            eligible,
            key=lambda j: (
                -results[j]["agreement"]["value"], results[j]["false_accept_rate"]["value"], j.count("+"), j
            ),
        )
        out[gen_family] = ranked[0] if ranked else None
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--csv", type=Path, default=REPO_ROOT / "audit" / "pilot_judge_check.csv")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "results" / "judge_selection")
    parser.add_argument("--judges", nargs="+", default=DEFAULT_JUDGES)
    parser.add_argument("--prompt", default="v2", choices=["v2", "v3"], help="judge prompt version")
    parser.add_argument("--mock", action="store_true", help="offline: the mock judge (exact match) instead of Ollama")
    args = parser.parse_args(argv)
    if not args.mock and os.environ.get("LP_REAL") != "1":
        print("Real judge calls need LP_REAL=1 (or use --mock).", file=sys.stderr)
        return 1

    config = load_config(REPO_ROOT / "configs" / "pilot.yaml")
    items = read_items(args.csv)
    cache = Cache(config.paths.cache / ("mock-calls.sqlite" if args.mock else "calls.sqlite"))
    clients = Clients(config, cache, args.mock, memory={})

    results: dict[str, dict] = {}
    per_item: list[dict] = [
        {k: it[k] for k in ("dataset", "qid", "condition", "prediction", "reference", "reference_source")}
        for it in items
    ]
    # The pilot's v1 judge accepted every one of these items (that is how they were selected).
    results["llama3.1:8b (v1 prompt, pilot)"] = score(items, [True] * len(items))
    for model in args.judges:
        chat = clients.chat(model)
        verdicts = []
        for i, it in enumerate(items):
            golds = [g.strip() for g in it["gold_answers"].split(" | ")]
            item_id = f"{it['qid']}|judge-check|{it['condition']}"
            verdicts.append(judge.judge(it["question"], golds, it["prediction"], chat, item_id, 0.0, args.prompt))
            print(f"\r{model}: {i + 1}/{len(items)}", end="", file=sys.stderr)
        print(file=sys.stderr)
        for row, v in zip(per_item, verdicts, strict=True):
            row[model] = v["correct"]
        results[model] = score(items, [v["correct"] for v in verdicts])
        results[model]["methods"] = dict(Counter(v["method"] for v in verdicts))

    # Two-judge candidates (both must accept), from the verdicts above: no extra calls. Added after pilot re-run 1
    # showed the single gemma2:9b judge still accepting wrong closed-book answers.
    pairs = ["+".join(pair) for pair in itertools.combinations(args.judges, 2)]
    for pair in pairs:
        a, b = pair.split("+")
        accepted = [row[a] and row[b] for row in per_item]
        results[pair] = score(items, accepted)
    candidates = {j: r for j, r in results.items() if j in args.judges or j in pairs}
    labels = Counter(it["reference"] for it in items)
    unclear = sorted({it["qid"] for it in items if it["reference"] == "unclear"})
    summary = {
        "items": len(items),
        "reference_labels": dict(labels),
        "reference_sources": dict(Counter(it["reference_source"] for it in items)),
        "reference_label_note": "Reference labels from a stronger model (Claude Opus), spot-checked by the author; "
        "not human labels. Ali's edits (human_correct = 'edited by Ali') override.",
        "unclear_qids": unclear,
        "judge_prompt": args.prompt,
        "pilot_generator": PILOT_GENERATOR,
        "results": results,
        "chosen": choose(candidates),
        "min_agreement": MIN_AGREEMENT,
        "meets_min_agreement": {j: r["agreement"]["value"] >= MIN_AGREEMENT for j, r in candidates.items()},
        "mock": args.mock,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    with (args.out / "items.jsonl").open("w") as handle:
        for row in per_item:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"{len(items)} items; reference labels {dict(labels)}; unclear excluded: {unclear}")
    print(f"{'judge':34} {'n':>4} {'agree':>7} {'95% CI':>15} {'false acc':>10} {'false rej':>10}")
    for name, r in results.items():
        a, fa, fr = r["agreement"], r["false_accept_rate"], r["false_reject_rate"]
        print(
            f"{name:34} {r['n']:>4} {100 * a['value']:>6.1f}% [{100 * a['lo']:5.1f}, {100 * a['hi']:5.1f}]"
            f" {100 * fa['value']:>9.1f}% {100 * fr['value']:>9.1f}%"
        )
    print(f"chosen per generator family: {summary['chosen']}")
    cache.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
