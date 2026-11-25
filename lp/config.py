"""Run configuration: a YAML file in configs/ plus the defaults below.

Every setting that changes a result lives here or in the YAML, so a run can be repeated exactly.
Paths can be overridden with environment variables (useful for tests and for a different Mac layout).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()

DATASET_NAMES = ("hotpotqa", "nq", "invented", "utm")
RETRIEVER_NAMES = ("bm25", "dense", "hybrid")


def _path(env_name: str, default: Path) -> Path:
    value = os.environ.get(env_name)
    return Path(value).expanduser() if value else default


@dataclass
class Paths:
    raw_data: Path = field(default_factory=lambda: _path("LP_DATA_DIR", REPO_ROOT / "data" / "raw"))
    cache: Path = field(default_factory=lambda: _path("LP_CACHE_DIR", REPO_ROOT / "data" / "cache"))
    results: Path = field(default_factory=lambda: _path("LP_RESULTS_DIR", REPO_ROOT / "results"))
    research_dir: Path = field(default_factory=lambda: _path("LP_RESEARCH_DIR", HOME / "Desktop" / "research-design"))
    invented_docs: list[Path] = field(
        default_factory=lambda: [
            _path("LP_INVENTED_DOCS", HOME / "Desktop" / "Rag-Tester" / "demo" / "v3" / "docs"),
            HOME / "Desktop" / "Rag-Tester" / "demo" / "sample_corpus",
        ]
    )
    """First folder that exists wins.

    The spec names demo/v3/docs (38 files); sample_corpus (18 files) is the fallback.
    """
    utm_corpus: Path = field(
        default_factory=lambda: _path("LP_UTM_CORPUS", HOME / "Desktop" / "waypoint" / "data" / "corpus")
    )

    @property
    def progress_file(self) -> Path:
        return self.research_dir / "research-progress.md"

    @property
    def needs_ali_file(self) -> Path:
        return self.research_dir / "NEEDS_ALI.md"


@dataclass
class DatasetSpec:
    name: str
    n: int


@dataclass
class RunConfig:
    run_name: str
    seed: int
    datasets: list[DatasetSpec]
    models: list[str]
    retrievers: list[str]
    ks: list[int]
    # Judge for each generator family: always a different family (B3, "Judge"). Chosen by scripts/eval_judges.py
    # (results/judge_selection/summary.json): the best agreement with the reference labels among other-family
    # judges. The first pilot used llama3.1:8b for qwen with the v1 prompt.
    judges: dict[str, str] = field(default_factory=lambda: {"qwen": "gemma2:9b", "llama": "qwen2.5:7b"})
    # Question generation for invented + UTM corpora reuses ragaudit; generator and verifier differ.
    question_generator: str = "qwen2.5:7b"
    question_verifier: str = "llama3.1:8b"
    embed_model: str = "nomic-embed-text"
    ollama_url: str = field(default_factory=lambda: os.environ.get("LP_OLLAMA_URL", "http://localhost:11434"))
    num_ctx: int = 4096
    retrieval_depth: int = 10
    nq_distractors: int = 20000
    judge_prompt: str = "v2"
    """v2: non-answers wrong by rule + stricter prompt with examples. v1 reproduces the first pilot."""
    hotpotqa_corpus: str = "full"
    """full: the passage pool is every dev question's paragraphs (deduplicated by title); only the sampled
    questions are asked. sampled: only the sampled questions' own paragraphs (the first pilot; too easy)."""
    exclude_yes_no: bool = True
    """HotpotQA yes/no questions can be guessed half the time, which would inflate guess-lucky passes."""
    judge_agreement_sample: float = 0.25
    """Share of exact-match-correct answers that are also sent to the LLM judge, to measure agreement."""
    bootstrap_resamples: int = 1000
    max_hours: float = 10.0
    default_seconds_per_call: float = 3.0
    default_seconds_per_embedding: float = 0.05
    """Only used until a run (or scripts/measure_embed_speed.py) has measured the real speed into speed.json."""
    paths: Paths = field(default_factory=Paths)


def load_config(path: str | Path) -> RunConfig:
    raw = yaml.safe_load(Path(path).read_text())
    raw["datasets"] = [DatasetSpec(**d) for d in raw["datasets"]]
    config = RunConfig(**raw)
    validate(config)
    return config


def validate(config: RunConfig) -> None:
    for spec in config.datasets:
        if spec.name not in DATASET_NAMES:
            raise ValueError(f"unknown dataset {spec.name!r}; expected one of {DATASET_NAMES}")
    for name in config.retrievers:
        if name not in RETRIEVER_NAMES:
            raise ValueError(f"unknown retriever {name!r}; expected one of {RETRIEVER_NAMES}")
    if config.judge_prompt not in ("v1", "v2"):
        raise ValueError(f"judge_prompt must be v1 or v2, not {config.judge_prompt!r}")
    if config.hotpotqa_corpus not in ("full", "sampled"):
        raise ValueError(f"hotpotqa_corpus must be full or sampled, not {config.hotpotqa_corpus!r}")
    for model in config.models:
        judge = judge_for(config, model)
        if family(judge) == family(model):
            raise ValueError(f"judge {judge} is the same family as generator {model}")
    if family(config.question_generator) == family(config.question_verifier):
        raise ValueError("question generator and verifier must be different model families")


def family(model: str) -> str:
    """'qwen2.5:7b' -> 'qwen', 'llama3.1:8b' -> 'llama'. Letters before the first digit or colon."""
    name = model.split(":")[0].lower()
    letters = ""
    for char in name:
        if not char.isalpha():
            break
        letters += char
    return letters or name


def judge_for(config: RunConfig, model: str) -> str:
    fam = family(model)
    if fam not in config.judges:
        raise ValueError(f"no judge configured for model family {fam!r} (model {model})")
    return config.judges[fam]
