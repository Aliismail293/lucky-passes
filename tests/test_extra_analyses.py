import importlib.util

from lp.config import REPO_ROOT

spec = importlib.util.spec_from_file_location("extra_analyses", REPO_ROOT / "scripts" / "extra_analyses.py")
extra_analyses = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extra_analyses)


def record(outcome, hit_any, correct, retrieved, method="contains"):
    return {
        "outcome": outcome,
        "hit_any": hit_any,
        "hit_all": hit_any,
        "multi_hop": False,
        "correct_rag": correct,
        "answers": ["In Class"],
        "retrieved_ids": retrieved,
        "lucky_kind": "guess_lucky" if outcome == "lucky_pass" else None,
        "judge_rag": {"method": method},
    }


def test_answer_in_context_needs_whole_words():
    texts = {"p1": " mode of delivery in class ", "p2": " in classroom "}
    assert extra_analyses.answer_in_context(record("lucky_pass", False, True, ["p1"]), texts)
    assert not extra_analyses.answer_in_context(record("lucky_pass", False, True, ["p2"]), texts)


def test_cell_analysis_splits_lucky_passes_and_conditions_on_misses():
    texts = {"p1": " in class ", "p2": " other "}
    group = [
        record("lucky_pass", False, True, ["p1"]),
        record("lucky_pass", False, True, ["p2"], method="llm"),
        record("miss", False, False, ["p2"]),
        record("true_pass", True, True, ["p1"]),
    ]
    out = extra_analyses.cell_analysis(group, texts)
    assert out["no_gold_retrieved"] == 3
    assert abs(out["accuracy_given_no_gold"]["value"] - 2 / 3) < 1e-9
    assert out["lucky_answer_in_context"] == 1
    assert out["lucky_answer_not_in_context_exact"]["value"] == 0.25
    assert out["lucky_contains_only_exact"]["value"] == 0.25
