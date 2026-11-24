from lp.datasets import Dataset, Passage, Question
from lp.mock import MockEmbedder
from lp.retrieve import BM25, retrieve_all, rrf, tokenize

DOCS = {
    "a": "The capital of Orvane is Kelmar.",
    "b": "Tessix is known for its rivers and lakes.",
    "c": "Brundle was founded by a sailor.",
}


def test_tokenize_drops_stopwords():
    assert tokenize("What is the Capital of Orvane?") == ["capital", "orvane"]


def test_bm25_ranks_the_matching_doc_first():
    assert BM25(DOCS).search("capital of Orvane", depth=3)[0] == "a"


def test_bm25_returns_nothing_for_unknown_words():
    assert BM25(DOCS).search("zzz", depth=3) == []


def test_rrf_rewards_agreement():
    # "x" is 2nd in both lists; "y" is 1st in one and absent from the other.
    fused = rrf([["y", "x"], ["z", "x"]], depth=3)
    assert fused[0] == "x"
    assert 1 / 62 + 1 / 62 > 1 / 61


def test_retrieve_all_caches_and_slices(tmp_path):
    passages = {pid: Passage(pid=pid, title="", text=t) for pid, t in DOCS.items()}
    questions = [Question(qid="q1", question="Who founded Brundle?", answers=["a sailor"], gold_ids=["c"])]
    dataset = Dataset(name="toy", questions=questions, passages=passages)
    first = retrieve_all(dataset, ["bm25", "dense", "hybrid"], MockEmbedder(), depth=2, cache_dir=tmp_path)
    assert all(len(r["q1"]) <= 2 for r in first.values())
    assert first["hybrid"]["q1"][0] == "c"
    assert len(list(tmp_path.glob("toy_*.json"))) == 1
    second = retrieve_all(dataset, ["hybrid"], MockEmbedder(), depth=2, cache_dir=tmp_path)
    assert second["hybrid"] == first["hybrid"]
