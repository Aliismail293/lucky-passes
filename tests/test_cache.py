import pytest

from lp.cache import Cache, make_key
from lp.llm import CachedChat, LLMCallFailed


class CountingModel:
    """Fails after `fail_after` calls, like a crash or Ollama going down mid-run."""

    def __init__(self, fail_after=None):
        self.model = "counting:1b"
        self.calls = 0
        self.fail_after = fail_after

    def complete(self, system, user):
        if self.fail_after is not None and self.calls >= self.fail_after:
            raise LLMCallFailed("simulated crash")
        self.calls += 1
        return f"answer to {user}"


def test_key_changes_with_every_input():
    base = make_key("chat", "m", {"system": "s", "user": "u", "params": {"t": 0}})
    assert base == make_key("chat", "m", {"system": "s", "user": "u", "params": {"t": 0}})
    assert base != make_key("chat", "m2", {"system": "s", "user": "u", "params": {"t": 0}})
    assert base != make_key("chat", "m", {"system": "s", "user": "u2", "params": {"t": 0}})
    assert base != make_key("chat", "m", {"system": "s", "user": "u", "params": {"t": 1}})


def test_second_run_makes_no_model_calls(tmp_path):
    cache = Cache(tmp_path / "c.sqlite")
    model = CountingModel()
    chat = CachedChat(model, cache, {"temperature": 0})
    for i in range(5):
        chat.complete("sys", f"q{i}")
    again = CachedChat(CountingModel(), Cache(tmp_path / "c.sqlite"), {"temperature": 0})
    answers = [again.complete("sys", f"q{i}") for i in range(5)]
    assert again.inner.calls == 0
    assert answers[2] == "answer to q2"


def test_resume_after_crash_only_redoes_unfinished_calls(tmp_path):
    path = tmp_path / "c.sqlite"
    crashing = CachedChat(CountingModel(fail_after=3), Cache(path), {})
    with pytest.raises(LLMCallFailed):
        for i in range(10):
            crashing.complete("sys", f"q{i}")
    assert crashing.stats.failures == 1

    resumed = CachedChat(CountingModel(), Cache(path), {})
    for i in range(10):
        resumed.complete("sys", f"q{i}")
    assert resumed.inner.calls == 7
    assert resumed.stats.hits == 3


def test_failed_calls_are_not_cached(tmp_path):
    cache = Cache(tmp_path / "c.sqlite")
    chat = CachedChat(CountingModel(fail_after=0), cache, {})
    with pytest.raises(LLMCallFailed):
        chat.complete("sys", "q")
    assert cache.count() == 0
