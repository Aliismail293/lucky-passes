"""Check everything a real run needs before leaving it overnight: Ollama up, models pulled, data and corpora present.

Exit code 0 = ready. Anything missing is printed with the command that fixes it.
"""

import sys

import httpx

from lp.config import REPO_ROOT, judge_models, load_config
from lp.runner import corpus_folder


def main(config_name: str) -> int:
    config = load_config(REPO_ROOT / "configs" / f"{config_name}.yaml")
    problems = []
    try:
        tags = httpx.get(f"{config.ollama_url}/api/tags", timeout=5).json()
        have = {m["name"] for m in tags.get("models", [])}
        have |= {name.removesuffix(":latest") for name in have}
    except httpx.HTTPError:
        have = set()
        problems.append("Ollama is not running. Open the Ollama app (or run: ollama serve) and try again.")
    needed = set(config.models) | {j for m in config.models for j in judge_models(config, m)} | {config.embed_model}
    if any(s.name in ("invented", "utm") for s in config.datasets):
        needed |= {config.question_generator, config.question_verifier}
    if have:
        for model in sorted(needed - have):
            problems.append(f"Model missing: ollama pull {model}")
    raw = config.paths.raw_data
    names = {s.name for s in config.datasets}
    if "hotpotqa" in names and not (raw / "hotpot_dev_distractor_v1.json").exists():
        problems.append("HotpotQA missing: uv run python scripts/download_data.py --only hotpotqa")
    if "nq" in names and not ((raw / "nq" / "corpus.jsonl").exists() and (raw / "NQ-open.dev.jsonl").exists()):
        problems.append("NQ missing: uv run python scripts/download_data.py --only nq")
    for name in names & {"invented", "utm"}:
        try:
            print(f"{name} corpus: {corpus_folder(config, name)}")
        except FileNotFoundError as exc:
            problems.append(f"{exc}. Set LP_INVENTED_DOCS or LP_UTM_CORPUS to the right folder.")
    for line in problems:
        print("NOT READY:", line)
    if not problems:
        print(f"Ready to run {config_name}.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "pilot"))
