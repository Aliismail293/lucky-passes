from lp import report


def cell(retriever, k):
    rate = {"value": 0.5, "lo": 0.4, "hi": 0.6, "n": 10}
    return {
        "dataset": "nq",
        "model": "m_1",
        "retriever": retriever,
        "k": k,
        "n": 10,
        "rates": dict.fromkeys(report.LABELS, rate),
    }


def test_headline_table_keeps_only_hybrid_k5(tmp_path):
    report.write_headline_table({"cells": [cell("hybrid", 5), cell("bm25", 5), cell("hybrid", 1)]}, tmp_path)
    rows = [line for line in (tmp_path / "headline_hybrid_k5.tex").read_text().splitlines() if line.startswith("NQ")]
    assert rows == ["NQ & m\\_1 & 10 & " + " & ".join(["50.0 {\\scriptsize[40.0, 60.0]}"] * 5) + " \\\\"]


def test_headline_table_skipped_without_hybrid_k5(tmp_path):
    report.write_headline_table({"cells": [cell("bm25", 5)]}, tmp_path)
    assert not (tmp_path / "headline_hybrid_k5.tex").exists()
