"""Three retrievers: BM25 (keywords), dense (embeddings) and hybrid (reciprocal rank fusion of the two).

Retrieval doesn't depend on the generator model, so it runs once per dataset and is saved to
data/cache/retrieval/. Each saved ranking is the top `depth` passage ids; k <= depth is sliced later.
"""

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from lp.datasets import Dataset

STOPWORDS = set(
    "a an and are as at be by for from has have he her his in is it its of on or she that the their them they "
    "this to was were what when where which who whom why will with how did does do".split()
)
TOKEN_RE = re.compile(r"[a-z0-9]+")

# nomic-embed-text expects these task prefixes on its inputs.
QUERY_PREFIX = "search_query: "
DOCUMENT_PREFIX = "search_document: "
RRF_K = 60


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


class BM25:
    """Okapi BM25 with an inverted index. k1 and b are the usual defaults."""

    def __init__(self, docs: dict[str, str], k1: float = 1.5, b: float = 0.75) -> None:
        self.ids = list(docs)
        self.k1, self.b = k1, b
        self.lengths = []
        self.postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for index, pid in enumerate(self.ids):
            counts = Counter(tokenize(docs[pid]))
            self.lengths.append(sum(counts.values()))
            for term, tf in counts.items():
                self.postings[term].append((index, tf))
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0
        n = len(self.ids)
        self.idf = {t: math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.postings.items()}

    def search(self, query: str, depth: int) -> list[str]:
        scores: dict[int, float] = defaultdict(float)
        for term in set(tokenize(query)):
            for index, tf in self.postings.get(term, []):
                norm = self.k1 * (1 - self.b + self.b * self.lengths[index] / (self.avg_len or 1))
                scores[index] += self.idf[term] * tf * (self.k1 + 1) / (tf + norm)
        best = sorted(scores, key=lambda i: (-scores[i], self.ids[i]))[:depth]
        return [self.ids[i] for i in best]


class Dense:
    def __init__(self, docs: dict[str, str], embedder) -> None:
        self.ids = list(docs)
        self.embedder = embedder
        self.matrix = _unit(embedder.embed([DOCUMENT_PREFIX + docs[p] for p in self.ids]))

    def search_many(self, queries: list[str], depth: int) -> list[list[str]]:
        q = _unit(self.embedder.embed([QUERY_PREFIX + text for text in queries]))
        scores = q @ self.matrix.T
        out = []
        for row in scores:
            order = np.lexsort((np.array(self.ids), -row))[:depth]
            out.append([self.ids[i] for i in order])
        return out


def _unit(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


def rrf(rankings: list[list[str]], depth: int, k: int = RRF_K) -> list[str]:
    """Reciprocal rank fusion: score(d) = sum over rankings of 1 / (k + rank of d), rank starting at 1."""
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, pid in enumerate(ranking, start=1):
            scores[pid] += 1 / (k + rank)
    return sorted(scores, key=lambda pid: (-scores[pid], pid))[:depth]


def retrieve_all(dataset: Dataset, retrievers: list[str], embedder, depth: int, cache_dir: Path | None) -> dict:
    """{retriever: {qid: [pid, ...]}} for every question. Uses and fills the retrieval cache."""
    docs = {pid: p.as_text() for pid, p in dataset.passages.items()}
    queries = [q.question for q in dataset.questions]
    qids = [q.qid for q in dataset.questions]
    # Hybrid fuses deeper lists than it returns, so a passage ranked 15th by one retriever can still win.
    fuse_depth = max(depth * 10, 50)
    needed = set(retrievers) | ({"bm25", "dense"} if "hybrid" in retrievers else set())

    results: dict[str, dict[str, list[str]]] = {}
    path = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = cache_dir / f"{dataset.name}_{dataset.fingerprint()}_{embedder.model}.json".replace(":", "-")
        if path.exists():
            results = json.loads(path.read_text())
    missing_q = lambda name: name not in results or any(qid not in results[name] for qid in qids)  # noqa: E731

    if "bm25" in needed and missing_q("bm25"):
        bm25 = BM25(docs)
        results["bm25"] = {
            **results.get("bm25", {}),
            **{qid: bm25.search(t, fuse_depth) for qid, t in zip(qids, queries, strict=True)},
        }
    if "dense" in needed and missing_q("dense"):
        dense = Dense(docs, embedder)
        found = dense.search_many(queries, fuse_depth)
        results["dense"] = {**results.get("dense", {}), **dict(zip(qids, found, strict=True))}
    if "hybrid" in needed and missing_q("hybrid"):
        results["hybrid"] = {
            **results.get("hybrid", {}),
            **{qid: rrf([results["bm25"][qid], results["dense"][qid]], fuse_depth) for qid in qids},
        }
    if path is not None:
        path.write_text(json.dumps(results))
    return {name: {qid: results[name][qid][:depth] for qid in qids} for name in retrievers}
