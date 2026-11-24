"""The invented and UTM questions must come from ragaudit's verified pipeline, not a copy of it."""

import json
from pathlib import Path

from ragaudit.llm.mock import MockLLM

from lp.datasets import chunk_corpus, generate_questions_for_chunks, load_generated

FIXTURE = Path(__file__).parent / "fixtures" / "tiny_corpus"


class Counting:
    def __init__(self, inner):
        self.inner = inner
        self.model = inner.model
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return self.inner.complete(system, user)


def test_generation_uses_ragaudit_pipeline_with_separate_verifier(tmp_path):
    chunks = chunk_corpus(FIXTURE)
    assert len(chunks) == 2
    generator, verifier = Counting(MockLLM(model="mock-gen")), Counting(MockLLM(model="mock-ver"))
    out = tmp_path / "gen.jsonl"
    generate_questions_for_chunks(chunks, generator, verifier, out)

    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert {r["chunk_id"] for r in rows} == {c.chunk_id for c in chunks}
    questions = [q for r in rows for q in r["questions"]]
    assert questions, "ragaudit's mock should produce at least one question"
    assert all(q["generator_model"] == "mock-gen" and q["verifier_model"] == "mock-ver" for q in questions)
    assert verifier.calls > 0

    dataset = load_generated("invented", chunks, out, n=100, seed=1)
    active = [q for q in questions if q["status"] == "active"]
    assert len(dataset.questions) == len(active)
    for q in dataset.questions:
        assert q.gold_ids[0] in dataset.passages


def test_generation_resumes_without_repeating_chunks(tmp_path):
    chunks = chunk_corpus(FIXTURE)
    out = tmp_path / "gen.jsonl"
    generate_questions_for_chunks(chunks[:1], MockLLM(model="g"), MockLLM(model="v"), out)
    generator = Counting(MockLLM(model="g"))
    generate_questions_for_chunks(chunks, generator, MockLLM(model="v"), out)
    assert len(out.read_text().splitlines()) == 2
    assert generator.calls > 0
    again = Counting(MockLLM(model="g"))
    generate_questions_for_chunks(chunks, again, MockLLM(model="v"), out)
    assert again.calls == 0
