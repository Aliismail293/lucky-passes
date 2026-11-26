import importlib.util

from lp.config import REPO_ROOT

spec = importlib.util.spec_from_file_location("export_error_sample", REPO_ROOT / "scripts" / "export_error_sample.py")
export_error_sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_error_sample)


def record(qid, model, outcome="lucky_pass", retriever="bm25"):
    return {"qid": qid, "model": model, "outcome": outcome, "retriever": retriever}


def test_sample_takes_lucky_passes_once_per_question_and_model_and_is_seeded():
    records = [record("q1", "m"), record("q1", "m", retriever="dense"), record("q2", "m"), record("q3", "m", "miss")]
    rows = export_error_sample.sample(records, size=5)
    assert sorted((r["qid"], r["retriever"]) for r in rows) == [("q1", "bm25"), ("q2", "bm25")]
    assert export_error_sample.sample(records, size=1) == export_error_sample.sample(records, size=1)
