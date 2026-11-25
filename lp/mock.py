"""Offline stand-ins for Ollama, used by tests and `--mock` runs. No network, fully deterministic.

MockChat behaves like a small model with some memory:
- closed-book: answers right only for questions in its `memory` dict, otherwise says "unknown";
- with passages: reads the answer out of a passage that names the question's subject, and
  falls back to memory when no passage does (that fallback is what creates memory-lucky passes);
- as a judge: compares normalised answers.
"""

import hashlib
import re

import numpy as np

from lp import generate, judge


class MockChat:
    def __init__(self, model: str = "mock-qwen:7b", memory: dict[str, str] | None = None) -> None:
        self.model = model
        self.memory = memory or {}
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        if judge.REFERENCE_LABEL in user:
            return self._judge(user)
        question = user.rsplit(generate.QUESTION_LABEL, 1)[-1].split(generate.ANSWER_LABEL)[0].strip()
        if user.startswith(generate.PASSAGES_HEADER):
            found = self._read(question, user)
            if found:
                return found
        return self.memory.get(question, "unknown")

    @staticmethod
    def _read(question: str, user: str) -> str | None:
        subject = re.search(r"(?:of|for|started|through) ([A-Z][a-z]+ \d+)", question)
        if not subject:
            return None
        match = re.search(rf"of {re.escape(subject.group(1))} is ([A-Za-z0-9]+)", user)
        return match.group(1) if match else None

    @staticmethod
    def _judge(user: str) -> str:
        # The item being graded comes last; earlier reference/predicted lines are the prompt's worked examples.
        golds = user.rsplit(judge.REFERENCE_LABEL, 1)[1].split("\n", 1)[0].strip().split(" | ")
        predicted = user.rsplit(judge.PREDICTED_LABEL, 1)[1].split("\n", 1)[0].strip()
        correct = any(judge.normalize(g) == judge.normalize(predicted) for g in golds)
        return '{"correct": true}' if correct else '{"correct": false}'


class MockEmbedder:
    """Hashed bag-of-words vectors: texts that share words get similar vectors. Ignores nomic prefixes."""

    def __init__(self, model: str = "mock-embed", dim: int = 256) -> None:
        self.model = model
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for word in re.findall(r"[a-z0-9]+", text.lower().split(": ", 1)[-1]):
                out[i, int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dim] += 1.0
        return out
