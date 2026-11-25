"""Offline tests for scripts/export_audit_sheet.py on toy records."""

import csv
import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("export_audit_sheet", REPO_ROOT / "scripts" / "export_audit_sheet.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def record(qid: str, outcome: str, dataset: str = "hotpotqa") -> dict:
    correct = outcome in ("true_pass", "lucky_pass")
    return {
        "dataset": dataset, "model": "qwen2.5:7b", "retriever": "hybrid", "k": 5, "qid": qid,
        "question": f"q {qid}?", "answers": ["a"], "pred_rag": "a" if correct else "b",
        "correct_rag": correct, "judge_rag": {"method": "contains" if correct else "llm"},
        "hit_any": outcome in ("true_pass", "grounding_failure"), "outcome": outcome,
    }


def toy(n_lucky: int, n_other: int) -> list[dict]:
    lucky = [record(f"L{i}", "lucky_pass") for i in range(n_lucky)]
    other = [record(f"O{i}", ("true_pass", "miss", "grounding_failure")[i % 3]) for i in range(n_other)]
    return lucky + other


def test_half_lucky_and_size():
    chosen = audit.pick(toy(40, 100), excluded=set())
    assert len(chosen) == 50
    assert sum(r["outcome"] == "lucky_pass" for r in chosen) == 25


def test_excludes_pilot_check_questions():
    excluded = {f"L{i}" for i in range(30)} | {f"O{i}" for i in range(50)}
    chosen = audit.pick(toy(40, 100), excluded=excluded)
    assert not {r["qid"] for r in chosen} & excluded
    assert sum(r["outcome"] == "lucky_pass" for r in chosen) == 10


def test_fewer_lucky_passes_fills_with_others():
    chosen = audit.pick(toy(5, 100), excluded=set())
    assert len(chosen) == 50
    assert sum(r["outcome"] == "lucky_pass" for r in chosen) == 5


def test_seeded():
    records = toy(40, 100)
    assert audit.pick(records, set()) == audit.pick(records, set())


def test_excluded_qids_reads_sheet(tmp_path):
    sheet = tmp_path / "check.csv"
    sheet.write_text("dataset,qid,condition\nhotpotqa,hp:1,rag\nhotpotqa,hp:2,closed\n")
    assert audit.excluded_qids(sheet) == {"hp:1", "hp:2"}


def test_main_writes_sheet_and_refuses_overwrite(tmp_path, monkeypatch):
    run_dir = tmp_path / "core"
    run_dir.mkdir()
    (run_dir / "records.jsonl").write_text("\n".join(json.dumps(r) for r in toy(30, 60)))
    monkeypatch.setattr(audit, "PILOT_CHECK", tmp_path / "missing.csv")
    out = tmp_path / "audit_sheet.csv"
    monkeypatch.setattr("sys.argv", ["x", str(run_dir), str(out)])
    assert audit.main() == 0
    with out.open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 50
    assert {r["human_correct"] for r in rows} == {""}
    assert {r["llm_judge"] for r in rows} <= {"correct", "incorrect"}
    assert audit.main() == 1
