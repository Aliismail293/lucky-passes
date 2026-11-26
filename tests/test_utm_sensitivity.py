import importlib.util

from lp.config import REPO_ROOT

spec = importlib.util.spec_from_file_location("utm_sensitivity", REPO_ROOT / "scripts" / "utm_sensitivity.py")
utm_sensitivity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utm_sensitivity)


def test_answer_frequency_counts_chunks_and_takes_the_most_common_answer():
    texts = {"a": "mode of delivery in class", "b": "mode of delivery in class", "c": "prerequisite mat240h5"}
    assert utm_sensitivity.answer_frequency(["In Class"], texts) == 2
    assert utm_sensitivity.answer_frequency(["MAT240H5", "in class"], texts) == 2
    assert utm_sensitivity.answer_frequency(["MAT999H5"], texts) == 0
