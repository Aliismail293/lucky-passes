import importlib.util
import json

from lp.config import REPO_ROOT

spec = importlib.util.spec_from_file_location("check_numbers", REPO_ROOT / "scripts" / "check_numbers.py")
check_numbers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_numbers)


def test_numbers_from_results_are_allowed_with_rounding(tmp_path):
    (tmp_path / "summary.json").write_text(json.dumps({"lucky": 0.6234, "n": 300}))
    allowed = check_numbers.numbers_in_results(tmp_path)
    tex = "Lucky passes were 62.3\\% (n = 300), about 62\\%.\n"
    assert check_numbers.unverified_numbers(tex, allowed) == []


def test_invented_number_is_caught(tmp_path):
    (tmp_path / "summary.json").write_text(json.dumps({"lucky": 0.62}))
    allowed = check_numbers.numbers_in_results(tmp_path)
    assert check_numbers.unverified_numbers("We saw 71.5\\% lucky passes.", allowed) == [(1, "71.5")]


def test_small_ints_years_citations_and_comments_are_skipped(tmp_path):
    allowed = check_numbers.numbers_in_results(tmp_path)
    tex = "We use 3 retrievers at k = 5 in 2026 \\cite{lewis2020}. % 99.9 in a comment\nSee Table~\\ref{tab:1}."
    assert check_numbers.unverified_numbers(tex, allowed) == []
