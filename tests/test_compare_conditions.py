import importlib.util

from lp.config import REPO_ROOT

spec = importlib.util.spec_from_file_location("compare_conditions", REPO_ROOT / "scripts" / "compare_conditions.py")
compare_conditions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare_conditions)


def test_ranks_average_ties():
    assert list(compare_conditions.ranks([10, 0, 0, 5])) == [4.0, 1.5, 1.5, 3.0]


def test_spearman_perfect_and_constant():
    up = compare_conditions.spearman([1, 2, 3, 4, 5, 6], [2, 4, 6, 8, 10, 12], permutations=200)
    assert up["rho"] == 1.0 and up["p"] < 0.05
    assert compare_conditions.spearman([1, 2, 3], [0, 0, 0])["rho"] is None


def test_compare_pairs_on_shared_questions():
    lucky = {"outcome": "lucky_pass", "outcome_all": "lucky_pass", "lucky_kind": "guess_lucky"}
    other = {"outcome": "true_pass", "outcome_all": "true_pass", "lucky_kind": None}
    a = {"q1": lucky, "q2": lucky, "q3": other}
    b = {"q1": other, "q2": lucky}
    out = compare_conditions.compare(a, b, {"bootstrap_resamples": 100, "seed": 13})
    assert out["n"] == 2
    assert out["lucky_pass"]["diff"]["value"] == 0.5
    assert out["lucky_pass"]["mcnemar"] == {"b01": 0, "b10": 1, "p": 1.0}
    assert out["memory_lucky"]["diff"]["value"] == 0.0
