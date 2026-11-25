"""Offline tests for scripts/check_pilot_report.py and scripts/export_judge_check.py on toy records."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load("check_pilot_report")
export = load("export_judge_check")


def verdict(contains, llm):
    return {"correct": bool(contains or llm), "contains": contains, "llm": llm}


def record(outcome, correct_rag, hit_any, closed=False, llm_closed=None):
    return {
        "dataset": "toy", "model": "m", "retriever": "hybrid", "k": 5, "qid": f"q{outcome}{correct_rag}",
        "question": "Q?", "answers": ["A"], "outcome": outcome, "outcome_all": outcome, "correct_rag": correct_rag,
        "hit_any": hit_any, "hit_all": hit_any, "correct_closed": closed, "correct_oracle": True,
        "lucky_kind": ("memory_lucky" if closed else "guess_lucky") if outcome == "lucky_pass" else None,
        "pred_rag": "A", "pred_closed": "B", "pred_oracle": "A",
        "judge_rag": verdict(correct_rag, None), "judge_closed": verdict(False, llm_closed),
        "judge_oracle": verdict(True, True),
    }  # fmt: skip


RECORDS = [record("true_pass", True, True), record("lucky_pass", True, False, closed=True, llm_closed=True)]


def cell(lucky_value):
    rate = lambda v: {"value": v, "lo": v, "hi": v, "n": 2}  # noqa: E731
    return {
        "dataset": "toy", "model": "m", "retriever": "hybrid", "k": 5, "n": 2,
        "counts": {"true_pass": 1, "lucky_pass": 1, "grounding_failure": 0, "miss": 0},
        "rates": {"accuracy": rate(1.0), "lucky_pass": rate(lucky_value), "closed_accuracy": rate(0.5)},
    }  # fmt: skip


def test_cell_matches_records():
    assert check.cell_mismatches(cell(0.5), RECORDS) == []


def test_cell_mismatch_is_reported():
    problems = check.cell_mismatches(cell(0.4), RECORDS)
    assert len(problems) == 1 and "lucky_pass" in problems[0]


def test_report_number_must_be_in_summary():
    summary = {"cells": [cell(0.5)], "meta": {"started": "2026-11-24 17:00"}}
    assert check.report_numbers_not_in_summary("lucky 50.0% on 2026-11-24 17:00", summary) == []
    assert check.report_numbers_not_in_summary("lucky 62.5%", summary) == [(1, "62.5")]


def test_judge_agreement_counts_only_items_where_both_judges_ran():
    table = check.judge_agreement(RECORDS)
    assert table == {"n": 3, "agree": 2, "table": {"both_correct": 2, "llm_only": 1}}


def test_export_lists_only_llm_overrules():
    rows = export.disagreements(RECORDS)
    assert [(r["qid"], r["condition"]) for r in rows] == [("qlucky_passTrue", "closed")]
