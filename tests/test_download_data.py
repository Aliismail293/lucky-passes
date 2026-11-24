"""Offline test: HF hotpot_qa parquet rows convert to the original HotpotQA JSON that load_hotpotqa reads."""

import importlib.util
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from lp.datasets import load_hotpotqa

REPO_ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("download_data", REPO_ROOT / "scripts" / "download_data.py")
download_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download_data)

ROWS = [
    {
        "id": "q1",
        "question": "Which city is the capital of the country where Alpha was born?",
        "answer": "Beta City",
        "type": "bridge",
        "level": "medium",
        "supporting_facts": {"title": ["Alpha", "Gamma"], "sent_id": [0, 1]},
        "context": {
            "title": ["Alpha", "Gamma", "Delta"],
            "sentences": [
                ["Alpha was born in Gamma."],
                ["Gamma is a country.", " Its capital is Beta City."],
                ["Delta."],
            ],
        },
    },
    {
        "id": "q2",
        "question": "Are Alpha and Delta both people?",
        "answer": "no",
        "type": "comparison",
        "level": "hard",
        "supporting_facts": {"title": ["Alpha"], "sent_id": [0]},
        "context": {"title": ["Alpha", "Delta"], "sentences": [["Alpha was born in Gamma."], ["Delta."]]},
    },
]


def test_parquet_converts_to_original_hotpot_format(tmp_path):
    parquet = tmp_path / "fake.parquet"
    pq.write_table(pa.Table.from_pylist(ROWS), parquet)
    target = tmp_path / "hotpot_dev_distractor_v1.json"

    assert download_data.parquet_to_hotpot_json(parquet, target) == 2

    records = json.loads(target.read_text())
    assert records[0] == {
        "_id": "q1",
        "question": ROWS[0]["question"],
        "answer": "Beta City",
        "type": "bridge",
        "level": "medium",
        "supporting_facts": [["Alpha", 0], ["Gamma", 1]],
        "context": [
            ["Alpha", ["Alpha was born in Gamma."]],
            ["Gamma", ["Gamma is a country.", " Its capital is Beta City."]],
            ["Delta", ["Delta."]],
        ],
    }
    assert not target.with_suffix(".json.part").exists()

    dataset = load_hotpotqa(target, n=10, seed=0)
    assert dataset.info == {"available": 2, "after_yes_no_filter": 1, "sampled": 1}
    question = dataset.questions[0]
    assert question.answers == ["Beta City"]
    assert sorted(dataset.passages[p].title for p in question.gold_ids) == ["Alpha", "Gamma"]
    assert dataset.passages[question.gold_ids[1]].text == "Gamma is a country. Its capital is Beta City."
