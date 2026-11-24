import pytest

from lp import judge
from lp.config import RunConfig, family, validate


class FixedJudge:
    model = "judge:1b"

    def __init__(self, reply):
        self.reply = reply
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return self.reply


def test_normalize_drops_case_punctuation_and_articles():
    assert judge.normalize("The  Eiffel Tower!") == "eiffel tower"


def test_contains_match_needs_whole_words():
    assert judge.contains_match("It was Paris, France", ["Paris"])
    assert not judge.contains_match("Parisian", ["Paris"])
    assert judge.exact_match("the Beatles", ["Beatles"])


def test_contains_match_decides_without_llm_outside_sample():
    llm = FixedJudge('{"correct": false}')
    verdict = judge.judge("q", ["Paris"], "Paris", llm, "item", sample_rate=0.0)
    assert verdict["correct"] and verdict["method"] == "contains" and llm.calls == 0


def test_llm_decides_when_contains_cannot():
    llm = FixedJudge('{"correct": true}')
    verdict = judge.judge("Who?", ["John F. Kennedy"], "JFK", llm, "item", sample_rate=0.0)
    assert verdict == {"correct": True, "method": "llm", "contains": False, "llm": True}


def test_empty_answer_is_wrong_without_llm():
    llm = FixedJudge('{"correct": true}')
    assert judge.judge("q", ["x"], "  ", llm, "item", 1.0)["correct"] is False
    assert llm.calls == 0


def test_unparseable_judge_reply_counts_as_wrong_and_is_flagged():
    verdict = judge.judge("q", ["x"], "y", FixedJudge("hmm, maybe"), "item", 0.0)
    assert verdict["correct"] is False and verdict["method"] == "llm_unparseable"


@pytest.mark.parametrize(
    "raw, expected",
    [('{"correct": true}', True), ('Sure: {"correct": false}', False), ("TRUE", True), ("no idea", None)],
)
def test_parse_judge(raw, expected):
    assert judge.parse_judge(raw) is expected


def test_agreement_table():
    verdicts = [
        {"contains": True, "llm": True},
        {"contains": False, "llm": False},
        {"contains": False, "llm": True},
        {"contains": True, "llm": None},
    ]
    result = judge.agreement(verdicts)
    assert result["n"] == 3 and result["agree"] == 2
    assert result["table"]["llm_only"] == 1


def test_agreement_sample_is_deterministic():
    assert judge.in_agreement_sample("abc", 0.5) == judge.in_agreement_sample("abc", 0.5)
    assert not judge.in_agreement_sample("abc", 0.0)
    assert judge.in_agreement_sample("abc", 1.0)


def test_model_family_and_cross_family_rule():
    assert family("qwen2.5:7b") == "qwen"
    assert family("llama3.1:8b") == "llama"
    bad = RunConfig(
        run_name="x",
        seed=1,
        datasets=[],
        models=["qwen2.5:7b"],
        retrievers=["bm25"],
        ks=[5],
        judges={"qwen": "qwen2.5:14b"},
    )
    with pytest.raises(ValueError, match="same family"):
        validate(bad)
