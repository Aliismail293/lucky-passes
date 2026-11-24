"""Run one config end to end: load data -> estimate + time gate -> generate questions -> retrieve -> answer + judge
-> classify -> summary, tables, figures, report.

Safe to stop at any point. Every model call is cached, so running the same command again skips finished work.
Real model calls only happen when LP_REAL=1 is set (ground rule B2.5); otherwise use --mock.
"""

import json
import os
import subprocess
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from lp import classify, generate, judge, report
from lp.cache import Cache
from lp.config import REPO_ROOT, RunConfig, judge_for
from lp.datasets import (
    Dataset,
    chunk_corpus,
    generate_questions_for_chunks,
    load_generated,
    load_hotpotqa,
    load_nq,
    toy_dataset,
)
from lp.llm import CachedChat, CachedEmbedder, CallStats, LLMCallFailed, OllamaChat, OllamaEmbedder
from lp.retrieve import retrieve_all

QGEN_CALLS_PER_CHUNK = 11
"""Rough: 1 fact extraction + 3 facts x (write + 1-2 rewrites + verify)."""
JUDGE_CALLS_PER_ANSWER = 0.6
"""Rough: answers that contains-match can't decide, plus the agreement sample."""
PROGRESS_EVERY_SECONDS = 15 * 60
MOCK_MEMORY = {"hotpotqa": 0.6, "nq": 0.5, "utm": 0.15, "invented": 0.0}
MOCK_OFFSET = {"hotpotqa": 0, "nq": 1000, "utm": 2000, "invented": 3000}
EXIT_NEEDS_APPROVAL = 3


class NeedsApproval(Exception):
    """The time estimate is over the limit. Details have been written to NEEDS_ALI.md."""


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# --- progress + NEEDS_ALI -------------------------------------------------------


class Progress:
    """Prints progress and appends it to research-progress.md, at most every 15 minutes (plus milestones)."""

    def __init__(self, config: RunConfig, mock: bool, echo=print) -> None:
        self.path = config.paths.progress_file
        self.label = config.run_name + (" (mock)" if mock else "")
        self.echo = echo
        self.last = 0.0
        self.started = time.time()

    def note(self, message: str, force: bool = True) -> None:
        line = f"- {now()} | {self.label} | {message}"
        if not force and time.time() - self.last < PROGRESS_EVERY_SECONDS:
            return
        self.echo(line)
        self.last = time.time()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("# research-progress\n\n## Summary\n\n(Updated by Claude Code.)\n\n## Run log\n\n")
        with self.path.open("a") as handle:
            handle.write(line + "\n")

    def tick(self, done: int, total: int) -> None:
        elapsed = time.time() - self.started
        eta = (elapsed / done) * (total - done) / 60 if done else float("nan")
        self.note(
            f"answering: {done}/{total} question-model pairs done, {total - done} left, ETA {eta:.0f} min", force=False
        )


NEEDS_ALI_HEADER = "# NEEDS_ALI\n\nNewest first. Tick an item when it's done.\n"


def add_to_needs_ali(config: RunConfig, title: str, body: str) -> None:
    """Puts a new item at the TOP of NEEDS_ALI.md, right under the header."""
    path = config.paths.needs_ali_file
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text() if path.exists() else NEEDS_ALI_HEADER
    rest = existing[len(NEEDS_ALI_HEADER) :] if existing.startswith(NEEDS_ALI_HEADER) else "\n" + existing
    item = f"\n## [ ] {title} ({now()})\n\n{body.strip()}\n"
    path.write_text(NEEDS_ALI_HEADER + item + rest)


# --- clients ---------------------------------------------------------------------


class Clients:
    def __init__(self, config: RunConfig, cache: Cache, mock: bool, memory: dict[str, str]) -> None:
        self.config, self.cache, self.mock = config, cache, mock
        self.stats = CallStats()
        self.memory = memory
        self._chats: dict[str, CachedChat] = {}
        if mock:
            from lp.mock import MockEmbedder

            self.embedder = CachedEmbedder(MockEmbedder(model="mock-" + config.embed_model), cache)
        else:
            self.embedder = CachedEmbedder(OllamaEmbedder(config.embed_model, config.ollama_url), cache)

    def chat(self, model: str) -> CachedChat:
        if model not in self._chats:
            inner: Any
            if self.mock:
                from lp.mock import MockChat

                inner = MockChat(model=model, memory=self.memory)
            else:
                inner = OllamaChat(model, self.config.ollama_url, self.config.seed, self.config.num_ctx)
            params = {"temperature": 0, "seed": self.config.seed, "num_ctx": self.config.num_ctx}
            self._chats[model] = CachedChat(inner, self.cache, params, self.stats)
        return self._chats[model]


# --- datasets --------------------------------------------------------------------


def corpus_folder(config: RunConfig, name: str) -> Path:
    if name == "utm":
        folders = [config.paths.utm_corpus]
    else:
        folders = config.paths.invented_docs
    for folder in folders:
        if folder.exists():
            return folder
    raise FileNotFoundError(f"no corpus folder for {name}: looked in {', '.join(str(f) for f in folders)}")


RAW_FILES = {
    "hotpotqa": ["hotpot_dev_distractor_v1.json"],
    "nq": ["nq/corpus.jsonl", "nq/queries.jsonl", "NQ-open.dev.jsonl"],
}


def load_static_datasets(
    config: RunConfig, mock: bool, allow_missing: bool = False
) -> tuple[dict[str, Dataset], dict[str, str], dict]:
    """Datasets that need no model calls to build. Also returns chunk lists for the generated ones.

    allow_missing (used by --estimate-only) skips datasets whose files aren't downloaded yet.
    """
    raw = config.paths.raw_data
    loaded: dict[str, Dataset] = {}
    memory: dict[str, str] = {}
    chunks: dict = {}
    for spec in config.datasets:
        if mock:
            offset = MOCK_OFFSET[spec.name]
            dataset, mem = toy_dataset(spec.name, spec.n, config.seed, MOCK_MEMORY[spec.name], offset=offset)
            loaded[spec.name] = dataset
            memory.update(mem)
            continue
        missing = [f for f in RAW_FILES.get(spec.name, []) if not (raw / f).exists()]
        if missing:
            if allow_missing:
                continue
            raise FileNotFoundError(
                f"{spec.name} data missing ({', '.join(missing)} in {raw}). Run: uv run python scripts/download_data.py"
            )
        if spec.name == "hotpotqa":
            loaded[spec.name] = load_hotpotqa(
                raw / "hotpot_dev_distractor_v1.json", spec.n, config.seed, config.exclude_yes_no
            )
        elif spec.name == "nq":
            loaded[spec.name] = load_nq(
                raw / "nq", raw / "NQ-open.dev.jsonl", spec.n, config.seed, config.nq_distractors
            )
        else:
            try:
                chunks[spec.name] = chunk_corpus(corpus_folder(config, spec.name))
            except FileNotFoundError:
                if not allow_missing:
                    raise
    return loaded, memory, chunks


def generated_path(config: RunConfig, name: str) -> Path:
    tag = f"{config.question_generator}_{config.question_verifier}".replace(":", "-")
    return config.paths.cache / "generated" / f"{name}_{tag}.jsonl"


def pending_chunks(config: RunConfig, name: str, chunk_list) -> int:
    path = generated_path(config, name)
    if not path.exists():
        return len(chunk_list)
    done = {json.loads(line)["chunk_id"] for line in path.read_text().splitlines() if line.strip()}
    return sum(1 for c in chunk_list if c.chunk_id not in done)


# --- estimate + gate ---------------------------------------------------------------


def speed_file(config: RunConfig) -> Path:
    return config.paths.cache / "speed.json"


def seconds_per_call(config: RunConfig, mock: bool) -> float:
    if mock:
        return 0.0
    path = speed_file(config)
    if path.exists():
        return float(json.loads(path.read_text()).get("seconds_per_call", config.default_seconds_per_call))
    return config.default_seconds_per_call


def record_speed(config: RunConfig, stats: CallStats) -> None:
    if stats.seconds_per_miss is None or stats.misses < 20:
        return
    path = speed_file(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"seconds_per_call": round(stats.seconds_per_miss, 3), "measured_on_calls": stats.misses, "updated": now()}
        )
    )


def planned_answer_calls(config: RunConfig, n_questions: dict[str, int]) -> int:
    per_question_model = 2 + len(config.retrievers) * len(config.ks)
    return sum(n_questions.values()) * len(config.models) * per_question_model


def estimate(config: RunConfig, cache: Cache, n_questions: dict[str, int], qgen_chunks: int, mock: bool) -> dict:
    """Upper-bound-ish estimate of uncached model calls and hours.

    Answer calls already in the cache (from an earlier run with the same models) are subtracted,
    which is approximate because the cache is shared between configs.
    """
    answers = planned_answer_calls(config, n_questions)
    judges = int(answers * JUDGE_CALLS_PER_ANSWER)
    qgen = qgen_chunks * QGEN_CALLS_PER_CHUNK
    models = set(config.models) | {judge_for(config, m) for m in config.models}
    cached = sum(cache.count(m) for m in models)
    uncached = max(0, answers + judges - cached) + qgen
    spc = seconds_per_call(config, mock)
    return {
        "answer_calls": answers,
        "judge_calls_est": judges,
        "question_generation_calls_est": qgen,
        "already_cached": cached,
        "uncached_calls_est": uncached,
        "seconds_per_call": spc,
        "hours_est": uncached * spc / 3600,
    }


def gate(config: RunConfig, est: dict, approve_hours: float | None, progress: Progress) -> None:
    limit = approve_hours if approve_hours is not None else config.max_hours
    progress.note(
        f"estimate: ~{est['uncached_calls_est']} uncached calls x {est['seconds_per_call']:.1f}s = "
        f"{est['hours_est']:.1f} h (limit {limit:.0f} h)"
    )
    if est["hours_est"] <= limit:
        return
    body = (
        f"`{config.run_name}` is estimated at **{est['hours_est']:.1f} hours**, over the {limit:.0f} h limit.\n\n"
        f"Estimate: `{json.dumps(est)}`\n\n"
        "Options (pick one and tell Claude Code, or run it yourself):\n"
        f"- Approve as is: `bash scripts/overnight.sh {config.run_name} --approve-hours {int(est['hours_est']) + 2}`\n"
        "- Cut questions: lower `n` in the config (e.g. 300 -> 200 cuts answer time by a third)\n"
        "- Cut models: drop `llama3.2:3b` or `llama3.1:8b` from `models` (H3 then rests on fewer sizes)\n"
        "- Split it across two nights: the cache keeps everything, so a stopped run resumes"
    )
    add_to_needs_ali(config, f"Approve long run: {config.run_name}", body)
    raise NeedsApproval(body)


# --- answering -----------------------------------------------------------------------


def judged(clients: Clients, config: RunConfig, model: str, q, prediction: str, mode: str) -> dict:
    judge_client = clients.chat(judge_for(config, model))
    item_id = f"{q.qid}|{model}|{mode}"
    return judge.judge(q.question, q.answers, prediction, judge_client, item_id, config.judge_agreement_sample)


def answer_dataset(
    clients: Clients, config: RunConfig, dataset: Dataset, rankings: dict, progress: Progress, counter: dict
) -> tuple[list[dict], int]:
    records, failures = [], 0
    for model in config.models:
        chat = clients.chat(model)
        for q in dataset.questions:
            try:
                pred_closed = generate.answer(chat, q.question, None)
                gold_passages = [dataset.passages[p] for p in q.gold_ids if p in dataset.passages]
                pred_oracle = generate.answer(chat, q.question, gold_passages)
                v_closed = judged(clients, config, model, q, pred_closed, "closed")
                v_oracle = judged(clients, config, model, q, pred_oracle, "oracle")
                for retriever in config.retrievers:
                    for k in config.ks:
                        retrieved = rankings[retriever][q.qid][:k]
                        pred_rag = generate.answer(chat, q.question, [dataset.passages[p] for p in retrieved])
                        v_rag = judged(clients, config, model, q, pred_rag, f"rag-{retriever}-{k}")
                        hit_any, hit_all = classify.hits(retrieved, q.gold_ids, k)
                        outcome = classify.outcome(hit_any, v_rag["correct"])
                        records.append(
                            {
                                "dataset": dataset.name,
                                "model": model,
                                "judge_model": judge_for(config, model),
                                "retriever": retriever,
                                "k": k,
                                "qid": q.qid,
                                "question": q.question,
                                "answers": q.answers,
                                "gold_ids": q.gold_ids,
                                "retrieved_ids": retrieved,
                                "multi_hop": q.multi_hop,
                                "hit_any": hit_any,
                                "hit_all": hit_all,
                                "pred_rag": pred_rag,
                                "correct_rag": v_rag["correct"],
                                "judge_rag": v_rag,
                                "pred_closed": pred_closed,
                                "correct_closed": v_closed["correct"],
                                "judge_closed": v_closed,
                                "pred_oracle": pred_oracle,
                                "correct_oracle": v_oracle["correct"],
                                "judge_oracle": v_oracle,
                                "outcome": outcome,
                                "outcome_all": classify.outcome(hit_all, v_rag["correct"]),
                                "lucky_kind": classify.lucky_kind(outcome, v_closed["correct"]),
                            }
                        )
            except LLMCallFailed as exc:
                failures += 1
                progress.note(f"call failed for {q.qid} ({model}): {exc}; it will be retried on the next run")
            counter["done"] += 1
            progress.tick(counter["done"], counter["total"])
    return records, failures


# --- main ----------------------------------------------------------------------------


def git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True)
        return out.stdout.strip() or None
    except OSError:
        return None


def run(
    config: RunConfig,
    config_path: Path,
    mock: bool = False,
    approve_hours: float | None = None,
    estimate_only: bool = False,
    echo=print,
) -> Path:
    if not mock and os.environ.get("LP_REAL") != "1":
        raise RuntimeError("Real model runs need LP_REAL=1 (or use --mock). scripts/overnight.sh sets it for you.")
    started_at, t0 = now(), time.time()
    paths = config.paths
    run_dir = paths.results / (config.run_name + ("-mock" if mock else ""))
    run_dir.mkdir(parents=True, exist_ok=True)
    cache = Cache(paths.cache / ("mock-calls.sqlite" if mock else "calls.sqlite"))
    progress = Progress(config, mock, echo)
    progress.note(
        f"start: config {config_path.name}, models {config.models}, retrievers {config.retrievers}, k {config.ks}"
    )

    datasets, memory, chunks = load_static_datasets(config, mock, allow_missing=estimate_only)
    clients = Clients(config, cache, mock, memory)

    n_questions = {
        spec.name: (len(datasets[spec.name].questions) if spec.name in datasets else spec.n) for spec in config.datasets
    }
    qgen_chunks = sum(pending_chunks(config, name, c) for name, c in chunks.items())
    est = estimate(config, cache, n_questions, qgen_chunks, mock)
    (run_dir / "estimate.json").write_text(json.dumps(est, indent=2))
    gate(config, est, approve_hours, progress)
    if estimate_only:
        return run_dir

    for name, chunk_list in chunks.items():
        progress.note(
            f"question generation for {name}: {len(chunk_list)} chunks "
            f"({pending_chunks(config, name, chunk_list)} not done yet)"
        )
        generate_questions_for_chunks(
            chunk_list,
            clients.chat(config.question_generator),
            clients.chat(config.question_verifier),
            generated_path(config, name),
            on_chunk=lambda i, total, name=name: progress.note(
                f"{name} question generation: {i}/{total} chunks", force=False
            ),
        )
        n = next(s.n for s in config.datasets if s.name == name)
        datasets[name] = load_generated(name, chunk_list, generated_path(config, name), n, config.seed)
        progress.note(f"{name}: {datasets[name].info}")

    counter = {"done": 0, "total": sum(len(d.questions) for d in datasets.values()) * len(config.models)}
    records, failures = [], 0
    for spec in config.datasets:
        dataset = datasets[spec.name]
        progress.note(
            f"retrieval for {dataset.name}: {len(dataset.questions)} questions, {len(dataset.passages)} passages"
        )
        rankings = retrieve_all(
            dataset,
            config.retrievers,
            clients.embedder,
            config.retrieval_depth,
            paths.cache / ("retrieval-mock" if mock else "retrieval"),
        )
        got, failed = answer_dataset(clients, config, dataset, rankings, progress, counter)
        records += got
        failures += failed
        (run_dir / "questions").mkdir(exist_ok=True)
        (run_dir / "questions" / f"{dataset.name}.json").write_text(
            json.dumps({"info": dataset.info, "questions": [asdict(q) for q in dataset.questions]}, indent=1)
        )

    if not mock:
        record_speed(config, clients.stats)
    with (run_dir / "records.jsonl").open("w") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = report.summarize(records, config.bootstrap_resamples, config.seed)
    wall = time.time() - t0
    stats = clients.stats
    total_q_models = counter["total"] or 1
    spc = stats.seconds_per_miss or seconds_per_call(config, mock)
    per_q = (planned_answer_calls(config, {"x": 1}) / len(config.models)) * (1 + JUDGE_CALLS_PER_ANSWER)
    summary["meta"] = {
        "config": str(config_path.relative_to(REPO_ROOT))
        if config_path.is_relative_to(REPO_ROOT)
        else str(config_path),
        "config_name": config.run_name,
        "mock": mock,
        "seed": config.seed,
        "models": config.models,
        "judges": {m: judge_for(config, m) for m in config.models},
        "retrievers": config.retrievers,
        "ks": config.ks,
        "embed_model": config.embed_model,
        "question_generator": config.question_generator,
        "question_verifier": config.question_verifier,
        "bootstrap_resamples": config.bootstrap_resamples,
        "git_commit": git_commit(),
        "started": started_at,
        "finished": now(),
        "datasets": {name: d.info for name, d in datasets.items()},
        "estimate": est,
        "failures": failures,
        "timing": {
            "wall_seconds": round(wall, 1),
            "uncached_calls": stats.misses,
            "cache_hits": stats.hits,
            "failures": stats.failures,
            "seconds_per_uncached_call": round(spc, 3) if spc else None,
            "seconds_per_100_questions": round(100 * per_q * spc, 1) if spc else None,
            "projections_hours": projections(config, spc) if spc else {},
            "question_model_pairs": total_q_models,
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    report.write_tables(summary, run_dir / "tables")
    report.write_figures(summary, run_dir / "figures")
    title = "Pilot report" if config.run_name == "pilot" else f"Run report: {config.run_name}"
    report_path = report.write_run_report(summary, records, run_dir, title + (" (MOCK)" if mock else ""))
    status = "complete" if failures == 0 else f"{failures} failures, re-run the same command to retry them"
    progress.note(f"done in {wall / 60:.1f} min: {len(records)} records, {status}. Report: {report_path}")
    cache.close()
    return run_dir


def projections(config: RunConfig, spc: float) -> dict[str, float]:
    """Hours for the other configs if nothing were cached, at the measured speed."""
    from lp.config import load_config

    out = {}
    for name in ("core", "ksweep"):
        path = REPO_ROOT / "configs" / f"{name}.yaml"
        if path.exists():
            other = load_config(path)
            calls = planned_answer_calls(other, {s.name: s.n for s in other.datasets}) * (1 + JUDGE_CALLS_PER_ANSWER)
            out[name] = round(calls * spc / 3600, 1)
    return out
