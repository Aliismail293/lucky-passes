from lp import classify


def test_four_outcome_classes():
    assert classify.outcome(gold_retrieved=True, correct=True) == "true_pass"
    assert classify.outcome(gold_retrieved=True, correct=False) == "grounding_failure"
    assert classify.outcome(gold_retrieved=False, correct=True) == "lucky_pass"
    assert classify.outcome(gold_retrieved=False, correct=False) == "miss"


def test_lucky_kind_only_for_lucky_passes():
    assert classify.lucky_kind("lucky_pass", correct_closed=True) == "memory_lucky"
    assert classify.lucky_kind("lucky_pass", correct_closed=False) == "guess_lucky"
    assert classify.lucky_kind("true_pass", correct_closed=True) is None


def test_hits_any_vs_all_for_multi_hop():
    retrieved = ["a", "b", "c", "d", "e", "f"]
    assert classify.hits(retrieved, ["b", "f"], k=5) == (True, False)
    assert classify.hits(retrieved, ["b", "f"], k=6) == (True, True)
    assert classify.hits(retrieved, ["z"], k=5) == (False, False)
    assert classify.hits(retrieved, ["a"], k=1) == (True, True)


def test_hits_with_no_gold_is_never_all():
    assert classify.hits(["a"], [], k=1) == (False, False)
