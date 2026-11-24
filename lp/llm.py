"""Model clients: Ollama chat and embeddings, each wrapped by the disk cache.

The chat clients have the same shape as ragaudit's `Completer` (a `.model` attribute and
`.complete(system, user)`), so ragaudit's question-generation pipeline can use them directly.
"""

import time
from dataclasses import dataclass, field

import httpx
import numpy as np

from lp.cache import Cache, make_key


class LLMCallFailed(Exception):
    """A model call failed after every retry. It is not cached, so the next run tries it again."""


class OllamaChat:
    def __init__(self, model: str, url: str, seed: int, num_ctx: int, timeout: float = 600.0, retries: int = 3) -> None:
        self.model = model
        self.url = url.rstrip("/")
        self.options = {"temperature": 0, "seed": seed, "num_ctx": num_ctx}
        self.retries = retries
        self._http = httpx.Client(timeout=timeout)

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": self.options,
        }
        last_error = ""
        for attempt in range(self.retries):
            try:
                response = self._http.post(f"{self.url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                last_error = str(exc)
                time.sleep(2**attempt)
        raise LLMCallFailed(f"{self.model}: {last_error}")


class OllamaEmbedder:
    def __init__(self, model: str, url: str, timeout: float = 600.0) -> None:
        self.model = model
        self.url = url.rstrip("/")
        self._http = httpx.Client(timeout=timeout)

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self._http.post(
            f"{self.url}/api/embed", json={"model": self.model, "input": texts, "truncate": True}
        )
        response.raise_for_status()
        return np.asarray(response.json()["embeddings"], dtype=np.float32)


@dataclass
class CallStats:
    hits: int = 0
    misses: int = 0
    failures: int = 0
    seconds_on_misses: float = 0.0
    failed_examples: list[str] = field(default_factory=list)

    @property
    def seconds_per_miss(self) -> float | None:
        return self.seconds_on_misses / self.misses if self.misses else None


class CachedChat:
    """Looks every call up in the cache first; only uncached calls reach the model."""

    def __init__(self, inner, cache: Cache, params: dict, stats: CallStats | None = None) -> None:
        self.inner = inner
        self.model = inner.model
        self.cache = cache
        self.params = params
        self.stats = stats or CallStats()

    def key(self, system: str, user: str) -> str:
        return make_key("chat", self.model, {"system": system, "user": user, "params": self.params})

    def is_cached(self, system: str, user: str) -> bool:
        return self.cache.get(self.key(system, user)) is not None

    def complete(self, system: str, user: str) -> str:
        key = self.key(system, user)
        cached = self.cache.get(key)
        if cached is not None:
            self.stats.hits += 1
            return cached
        start = time.monotonic()
        try:
            value = self.inner.complete(system, user)
        except LLMCallFailed as exc:
            self.stats.failures += 1
            self.stats.failed_examples = (self.stats.failed_examples + [str(exc)])[-5:]
            raise
        self.stats.seconds_on_misses += time.monotonic() - start
        self.stats.misses += 1
        self.cache.put(key, self.model, value)
        return value


class CachedEmbedder:
    """Caches one vector per (model, text). Embeds uncached texts in batches."""

    def __init__(self, inner, cache: Cache, batch_size: int = 64) -> None:
        self.inner = inner
        self.model = inner.model
        self.cache = cache
        self.batch_size = batch_size

    def embed(self, texts: list[str]) -> np.ndarray:
        keys = [make_key("embed", self.model, {"text": t}) for t in texts]
        vectors: list[np.ndarray | None] = []
        missing: list[int] = []
        for i, key in enumerate(keys):
            blob = self.cache.get_vector(key)
            vectors.append(np.frombuffer(blob, dtype=np.float32) if blob is not None else None)
            if blob is None:
                missing.append(i)
        for start in range(0, len(missing), self.batch_size):
            batch = missing[start : start + self.batch_size]
            new = self.inner.embed([texts[i] for i in batch])
            self.cache.put_vectors([(keys[i], new[j].astype(np.float32).tobytes()) for j, i in enumerate(batch)])
            for j, i in enumerate(batch):
                vectors[i] = new[j]
        return np.vstack([v for v in vectors if v is not None]) if vectors else np.zeros((0, 1), dtype=np.float32)
