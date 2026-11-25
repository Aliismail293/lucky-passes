"""Measure nomic-embed-text speed on real passages and save it to data/cache/speed.json for the time estimate.

Embeds the first N not-yet-cached passages of the full HotpotQA corpus through the normal cache, so the
vectors are reused by the next run (nothing is wasted). Needs LP_REAL=1 and Ollama running.

Usage: LP_REAL=1 uv run python scripts/measure_embed_speed.py [N, default 512]
"""

import os
import sys

from lp.cache import Cache
from lp.config import REPO_ROOT, load_config
from lp.datasets import load_hotpotqa
from lp.llm import CachedEmbedder, CallStats, OllamaEmbedder
from lp.retrieve import document_texts
from lp.runner import record_speed


def main() -> int:
    if os.environ.get("LP_REAL") != "1":
        print("Needs LP_REAL=1 (this calls the embedding model).", file=sys.stderr)
        return 1
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 512
    config = load_config(REPO_ROOT / "configs" / "pilot.yaml")
    raw = config.paths.raw_data / "hotpot_dev_distractor_v1.json"
    dataset = load_hotpotqa(raw, 100, config.seed, config.exclude_yes_no, "full")
    cache = Cache(config.paths.cache / "calls.sqlite")
    embedder = CachedEmbedder(OllamaEmbedder(config.embed_model, config.ollama_url), cache)
    texts = document_texts(dataset)
    todo = [t for t in texts if embedder.uncached_count([t])][:n]
    embedder.embed(todo)
    record_speed(config, CallStats(), embedder)
    rate = embedder.seconds_on_misses / embedder.misses if embedder.misses else float("nan")
    print(f"embedded {embedder.misses} passages in {embedder.seconds_on_misses:.1f} s = {rate:.4f} s each")
    print(f"corpus: {len(texts)} passages, {embedder.uncached_count(texts)} still uncached")
    cache.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
