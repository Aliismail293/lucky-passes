import json

from scripts import check_factsheets as cf


def write_source(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "REPO", tmp_path)
    (tmp_path / "r.json").write_text(
        json.dumps(
            {
                "meta": {"n": 66581, "share": 0.25},
                "cells": [
                    {"dataset": "a", "rate": {"value": 0.104, "lo": 0.021, "hi": 0.188, "n": 48}},
                    {"dataset": "b", "rate": {"value": 0.5, "lo": 0.4, "hi": 0.6, "n": 10}},
                ],
                "results": {"llama3.1:8b": {"x": 0.903}},
            }
        )
    )
    (tmp_path / "c.py").write_text("RRF_K = 60\nclass C:\n    depth: int = 10\n")


def test_matching_numbers_pass(tmp_path, monkeypatch):
    write_source(tmp_path, monkeypatch)
    text = (
        "pool of 66581 passages `[src: r.json#meta/n]`, 25% sampled `[src: r.json#meta/share]`,\n"
        "closed-book 10.4% [2.1, 18.8], n = 48\n`[src: r.json#cells[dataset=a]/rate]`; "
        "90.3% `[src: r.json#results/llama3.1:8b/x]`; k = 60 `[src: c.py#RRF_K]`, depth 10 `[src: c.py#depth]`"
    )
    assert cf.problems_in(text, "t.md") == []


def test_wrong_number_and_wrong_ci_fail(tmp_path, monkeypatch):
    write_source(tmp_path, monkeypatch)
    text = "66580 passages `[src: r.json#meta/n]`; 10.4% [2.1, 18.0], n = 48 `[src: r.json#cells[dataset=a]/rate]`"
    problems = cf.problems_in(text, "t.md")
    assert len(problems) == 2


def test_rate_needs_n_and_bad_key_is_reported(tmp_path, monkeypatch):
    write_source(tmp_path, monkeypatch)
    assert cf.problems_in("10.4% [2.1, 18.8] `[src: r.json#cells[dataset=a]/rate]`", "t.md")
    assert "can't resolve" in cf.problems_in("1 `[src: r.json#meta/missing]`", "t.md")[0]
