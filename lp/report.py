"""Turn per-question records into summary.json, tables (CSV + LaTeX), figures (PNG + PDF) and a pilot report.

Every number in the tables, figures and report is computed here from records.jsonl, never typed by hand.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from lp import classify, judge, stats

RATE_KEYS = (
    "accuracy",
    "true_pass",
    "lucky_pass",
    "memory_lucky",
    "guess_lucky",
    "grounding_failure",
    "miss",
    "hit_any",
    "hit_all",
    "lucky_pass_all",
    "closed_accuracy",
    "oracle_accuracy",
)
LABELS = {
    "accuracy": "Answer accuracy",
    "true_pass": "True pass",
    "lucky_pass": "Lucky pass",
    "memory_lucky": "Memory lucky",
    "guess_lucky": "Guess lucky",
    "grounding_failure": "Grounding failure",
    "miss": "Miss",
    "hit_any": "Hit@k (any gold)",
    "hit_all": "Hit@k (all gold)",
    "lucky_pass_all": "Lucky pass (all-gold rule)",
    "closed_accuracy": "Closed-book accuracy",
    "oracle_accuracy": "Oracle accuracy",
}
DATASET_ORDER = ["hotpotqa", "nq", "utm", "invented"]
# Categorical slots 1-4 of the reference palette, light mode, in fixed order.
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK_SECONDARY, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def indicators(record: dict) -> dict[str, float]:
    out = {
        "accuracy": float(record["correct_rag"]),
        "hit_any": float(record["hit_any"]),
        "hit_all": float(record["hit_all"]),
        "closed_accuracy": float(record["correct_closed"]),
        "oracle_accuracy": float(record["correct_oracle"]),
        "lucky_pass_all": float(record["outcome_all"] == classify.LUCKY_PASS),
        "memory_lucky": float(record["lucky_kind"] == classify.MEMORY_LUCKY),
        "guess_lucky": float(record["lucky_kind"] == classify.GUESS_LUCKY),
    }
    for name in classify.OUTCOMES:
        out[name] = float(record["outcome"] == name)
    return out


def _rates(group: list[dict], resamples: int, seed: int) -> dict:
    values = defaultdict(list)
    for record in group:
        for key, value in indicators(record).items():
            values[key].append(value)
    rates = {key: stats.bootstrap_ci(values[key], resamples, seed) for key in RATE_KEYS}
    rates["overstatement"] = rates["lucky_pass"]
    rates["lucky_share_of_correct"] = stats.bootstrap_ratio_ci(
        values["lucky_pass"], values["accuracy"], resamples, seed
    )
    return rates


def summarize(records: list[dict], resamples: int = 1000, seed: int = 0) -> dict:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for record in records:
        groups[(record["dataset"], record["model"], record["retriever"], record["k"])].append(record)
    cells = []
    for (dataset, model, retriever, k), group in sorted(groups.items(), key=lambda kv: _cell_sort(kv[0])):
        oracle_ok = [r for r in group if r["correct_oracle"]]
        counts = {name: sum(1 for r in group if r["outcome"] == name) for name in classify.OUTCOMES}
        cells.append(
            {
                "dataset": dataset,
                "model": model,
                "judge": group[0]["judge_model"],
                "retriever": retriever,
                "k": k,
                "n": len(group),
                "counts": counts,
                "rates": _rates(group, resamples, seed),
                "n_oracle_ok": len(oracle_ok),
                "rates_oracle_ok": _rates(oracle_ok, resamples, seed) if oracle_ok else None,
            }
        )
    verdicts = [r[f"judge_{mode}"] for r in records for mode in ("rag", "closed", "oracle")]
    return {"cells": cells, "judge_agreement": judge.agreement(verdicts)}


def _cell_sort(key: tuple) -> tuple:
    dataset, model, retriever, k = key
    order = DATASET_ORDER.index(dataset) if dataset in DATASET_ORDER else 99
    return (order, dataset, model, retriever, k)


def pct(ci: dict | None) -> str:
    if not ci or ci.get("value") is None:
        return "n/a"
    return f"{100 * ci['value']:.1f} [{100 * ci['lo']:.1f}, {100 * ci['hi']:.1f}]"


# --- tables ----------------------------------------------------------------

TABLE_COLUMNS = ("accuracy", "true_pass", "lucky_pass", "memory_lucky", "guess_lucky", "grounding_failure", "miss")


def write_tables(summary: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for cell in summary["cells"]:
        row = {"dataset": cell["dataset"], "model": cell["model"], "retriever": cell["retriever"], "k": cell["k"]}
        row["n"] = cell["n"]
        for key in TABLE_COLUMNS:
            row[key] = pct(cell["rates"][key])
        rows.append(row)
    with (out_dir / "main_table.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["dataset"])
        writer.writeheader()
        writer.writerows(rows)

    header = " & ".join(["Dataset", "Model", "Retr.", "$k$", "$n$"] + [LABELS[c] for c in TABLE_COLUMNS])
    lines = [
        "% Generated by lp/report.py from summary.json. Do not edit by hand.",
        "\\begin{tabular}{llllr" + "l" * len(TABLE_COLUMNS) + "}",
        "\\toprule",
        header + " \\\\",
        "\\midrule",
    ]
    for row in rows:
        values = [row["dataset"], row["model"], row["retriever"], str(row["k"]), str(row["n"])]
        values += [row[c].replace("[", "{\\scriptsize[").replace("]", "]}") for c in TABLE_COLUMNS]
        lines.append(" & ".join(v.replace("_", "\\_") for v in values) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (out_dir / "main_table.tex").write_text("\n".join(lines) + "\n")


# --- figures ---------------------------------------------------------------


def _plt():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.edgecolor": INK_SECONDARY,
            "axes.labelcolor": INK,
            "xtick.color": INK_SECONDARY,
            "ytick.color": INK_SECONDARY,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
        }
    )
    return plt


def _save(fig, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # No creation date in the PDFs, so rebuilding unchanged results gives byte-identical files.
    fig.savefig(out_dir / f"{name}.png", dpi=200, bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.pdf", dpi=200, bbox_inches="tight", metadata={"CreationDate": None})


def _grouped_bars(plt, groups: list[str], series: dict[str, list[dict | None]], ylabel: str, title: str):
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    width = 0.8 / max(len(series), 1)
    for s, (name, cis) in enumerate(series.items()):
        xs, ys, lo, hi = [], [], [], []
        for g, ci in enumerate(cis):
            if ci and ci.get("value") is not None:
                xs.append(g - 0.4 + width * (s + 0.5))
                ys.append(100 * ci["value"])
                lo.append(100 * (ci["value"] - ci["lo"]))
                hi.append(100 * (ci["hi"] - ci["value"]))
        ax.bar(xs, ys, width * 0.92, color=SERIES_COLORS[s % len(SERIES_COLORS)], label=name, edgecolor="white")
        ax.errorbar(xs, ys, yerr=[lo, hi], fmt="none", ecolor=INK_SECONDARY, elinewidth=0.8, capsize=2)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", color=INK, fontsize=10)
    ax.set_ylim(bottom=0)
    if len(series) > 1:
        ax.legend(frameon=False, fontsize=8)
    return fig


def _cell(summary: dict, **match) -> dict | None:
    for cell in summary["cells"]:
        if all(cell[k] == v for k, v in match.items()):
            return cell
    return None


def write_figures(summary: dict, out_dir: Path) -> list[str]:
    """Writes whichever figures this run's grid supports. Returns their names."""
    plt = _plt()
    cells = summary["cells"]
    if not cells:
        return []
    datasets = [d for d in DATASET_ORDER if any(c["dataset"] == d for c in cells)]
    models = sorted({c["model"] for c in cells})
    retrievers = sorted({c["retriever"] for c in cells})
    ks = sorted({c["k"] for c in cells})
    main_model = models[0]
    main_retriever = "hybrid" if "hybrid" in retrievers else retrievers[0]
    main_k = 5 if 5 in ks else ks[-1]
    made = []

    def lucky(**m):
        cell = _cell(summary, **m)
        return cell["rates"]["lucky_pass"] if cell else None

    # H1 and H3: lucky-pass rate by dataset, one bar per model.
    series = {m: [lucky(dataset=d, model=m, retriever=main_retriever, k=main_k) for d in datasets] for m in models}
    fig = _grouped_bars(
        plt, datasets, series, "Lucky-pass rate (%)", f"Lucky passes by dataset ({main_retriever}, k={main_k})"
    )
    _save(fig, out_dir, "lucky_by_dataset")
    plt.close(fig)
    made.append("lucky_by_dataset")

    if len(retrievers) > 1:  # H2: by retriever
        series = {r: [lucky(dataset=d, model=main_model, retriever=r, k=main_k) for d in datasets] for r in retrievers}
        fig = _grouped_bars(
            plt, datasets, series, "Lucky-pass rate (%)", f"Lucky passes by retriever ({main_model}, k={main_k})"
        )
        _save(fig, out_dir, "lucky_by_retriever")
        plt.close(fig)
        made.append("lucky_by_retriever")

    if len(ks) > 1:  # H2: by k
        fig, ax = plt.subplots(figsize=(4.2, 2.8))
        for i, d in enumerate(datasets):
            cis = [lucky(dataset=d, model=main_model, retriever=main_retriever, k=k) for k in ks]
            pts = [(k, ci) for k, ci in zip(ks, cis, strict=True) if ci and ci["value"] is not None]
            if not pts:
                continue
            color = SERIES_COLORS[i % len(SERIES_COLORS)]
            xs = [k for k, _ in pts]
            ax.plot(
                xs, [100 * ci["value"] for _, ci in pts], color=color, linewidth=2, marker="o", markersize=5, label=d
            )
            ax.fill_between(
                xs, [100 * ci["lo"] for _, ci in pts], [100 * ci["hi"] for _, ci in pts], color=color, alpha=0.12
            )
        ax.set_xticks(ks)
        ax.set_xlabel("k (passages retrieved)")
        ax.set_ylabel("Lucky-pass rate (%)")
        ax.set_title(f"Lucky passes vs k ({main_model}, {main_retriever})", loc="left", color=INK, fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        _save(fig, out_dir, "lucky_vs_k")
        plt.close(fig)
        made.append("lucky_vs_k")

    # H4: closed-book accuracy vs lucky-pass rate. Colour = dataset, marker shape = model.
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    markers = ["o", "s", "^", "D"]
    for i, d in enumerate(datasets):
        for j, m in enumerate(models):
            cell = _cell(summary, dataset=d, model=m, retriever=main_retriever, k=main_k)
            if not cell:
                continue
            x, y = cell["rates"]["closed_accuracy"]["value"], cell["rates"]["lucky_pass"]["value"]
            color = SERIES_COLORS[i % len(SERIES_COLORS)]
            ax.scatter(
                [100 * x],
                [100 * y],
                s=40,
                marker=markers[j % len(markers)],
                color=color,
                edgecolor="white",
                linewidth=1.5,
                zorder=3,
            )
    handles = [
        plt.Line2D([], [], linestyle="", marker="o", color=SERIES_COLORS[i % len(SERIES_COLORS)], label=d)
        for i, d in enumerate(datasets)
    ]
    if len(models) > 1:
        handles += [
            plt.Line2D([], [], linestyle="", marker=markers[j % len(markers)], color=INK_SECONDARY, label=m)
            for j, m in enumerate(models)
        ]
    ax.legend(handles=handles, frameon=False, fontsize=7, loc="center left", bbox_to_anchor=(1.0, 0.5))
    ax.set_xlabel("Closed-book accuracy (%)")
    ax.set_ylabel("Lucky-pass rate (%)")
    ax.set_title("Memory predicts lucky passes?", loc="left", color=INK, fontsize=10)
    ax.grid(True, axis="both")
    _save(fig, out_dir, "closed_vs_lucky")
    plt.close(fig)
    made.append("closed_vs_lucky")
    return made


# --- pilot / run report -------------------------------------------------------


def two_by_two(cell: dict) -> list[str]:
    r, c, n = cell["rates"], cell["counts"], cell["n"]
    return [
        "| | Answer correct | Answer wrong |",
        "|---|---|---|",
        f"| **Gold retrieved** | True pass: {c['true_pass']}/{n} = {pct(r['true_pass'])} | "
        f"Grounding failure: {c['grounding_failure']}/{n} = {pct(r['grounding_failure'])} |",
        f"| **Gold not retrieved** | Lucky pass: {c['lucky_pass']}/{n} = {pct(r['lucky_pass'])} | "
        f"Miss: {c['miss']}/{n} = {pct(r['miss'])} |",
    ]


def write_run_report(summary: dict, records: list[dict], run_dir: Path, title: str) -> Path:
    meta = summary["meta"]
    lines = [
        f"# {title}",
        "",
        "Generated by `lp/report.py` from `records.jsonl`. Rates are % with 95% bootstrap CIs "
        f"({meta['bootstrap_resamples']} resamples).",
        "",
    ]
    if meta.get("mock"):
        lines += [
            "> **MOCK RUN.** Toy data and a fake model. These numbers mean nothing; they only show the pipeline works.",
            "",
        ]
    lines += ["## Setup", ""]
    for key in ("config", "seed", "models", "retrievers", "ks", "embed_model", "started", "finished"):
        lines.append(f"- {key}: `{meta.get(key)}`")
    lines += ["", "## Datasets", ""]
    for name, info in meta["datasets"].items():
        lines.append(f"- **{name}**: " + ", ".join(f"{k} = {v}" for k, v in info.items()))
    for cell in summary["cells"]:
        r = cell["rates"]
        lines += [
            "",
            f"## {cell['dataset']} · {cell['model']} · {cell['retriever']} k={cell['k']} "
            f"(n = {cell['n']}, judge {cell['judge']})",
            "",
            *two_by_two(cell),
            "",
            f"- Answer accuracy (what an answer-only eval reports): {pct(r['accuracy'])}",
            f"- True-pass rate: {pct(r['true_pass'])}",
            f"- **Overstatement = accuracy − true pass = lucky-pass rate: {pct(r['overstatement'])}**",
            f"- Lucky passes as a share of correct answers: {pct(r['lucky_share_of_correct'])} "
            f"(n correct = {r['lucky_share_of_correct']['n']})",
            f"- Memory lucky: {pct(r['memory_lucky'])} · guess lucky: {pct(r['guess_lucky'])}",
            f"- Closed-book accuracy: {pct(r['closed_accuracy'])} · oracle accuracy: {pct(r['oracle_accuracy'])}",
            f"- Hit@{cell['k']} any gold: {pct(r['hit_any'])} · all gold: {pct(r['hit_all'])} · "
            f"lucky pass under the all-gold rule: {pct(r['lucky_pass_all'])}",
            f"- Oracle-correct subset (n = {cell['n_oracle_ok']}): lucky-pass rate "
            f"{pct((cell['rates_oracle_ok'] or {}).get('lucky_pass'))}",
        ]
    agreement = summary["judge_agreement"]
    rate = f"{100 * agreement['rate']:.1f}%" if agreement["rate"] is not None else "n/a"
    lines += [
        "",
        "## Judge agreement (contains-match vs LLM judge)",
        "",
        f"- Items where both ran: {agreement['n']}; agreement {agreement['agree']}/{agreement['n']} = {rate}",
        f"- Table: `{json.dumps(agreement['table'])}`",
    ]

    lucky = [r for r in records if r["outcome"] == classify.LUCKY_PASS]
    lines += ["", "## Example lucky passes (up to 10)", ""]
    by_dataset = defaultdict(list)
    for record in lucky:
        by_dataset[record["dataset"]].append(record)
    examples: list[dict] = []
    while len(examples) < 10 and any(by_dataset.values()):
        for name in list(by_dataset):
            if by_dataset[name] and len(examples) < 10:
                examples.append(by_dataset[name].pop(0))
    if not examples:
        lines.append("None in this run.")
    for record in examples:
        lines += [
            f"- **{record['dataset']}** `{record['qid']}` "
            f"({record['lucky_kind']}, judged by {record['judge_rag']['method']})",
            f"  - Q: {record['question']}",
            f"  - Gold: {' | '.join(record['answers'])} · RAG answer: {record['pred_rag']} "
            f"· closed-book: {record['pred_closed']}",
        ]

    timing = meta["timing"]
    lines += [
        "",
        "## Runtime",
        "",
        f"- Wall time: {timing['wall_seconds'] / 60:.1f} min · uncached model calls: {timing['uncached_calls']} · "
        f"cache hits: {timing['cache_hits']} · failures: {timing['failures']}",
    ]
    if timing.get("seconds_per_100_questions") is not None:
        lines.append(
            "- Answering + judging time per 100 questions per model: "
            f"{timing['seconds_per_100_questions'] / 60:.1f} min"
        )
    for name, hours in (timing.get("projections_hours") or {}).items():
        lines.append(f"- Projected time for `{name}` (uncached, at this speed): {hours:.1f} h")
    path = run_dir / ("PILOT_REPORT.md" if meta["config_name"] == "pilot" else "RUN_REPORT.md")
    path.write_text("\n".join(lines) + "\n")
    return path
