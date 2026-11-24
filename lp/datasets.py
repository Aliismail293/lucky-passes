"""Load the four datasets into one shape: questions, a passage corpus, and gold passage ids per question.

- hotpotqa: HotpotQA distractor dev. Each question's 10 paragraphs are pooled into one shared corpus.
- nq: BEIR nq (gold passages via qrels) joined with NQ-open dev (answer strings) on the question text,
  plus a fixed-seed sample of distractor passages from the BEIR corpus.
- invented / utm: questions generated and verified by ragaudit's pipeline (generator != verifier).

Sampling always uses random.Random(seed) on a sorted list, so the same seed gives the same questions.
"""

import hashlib
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from lp.judge import normalize


@dataclass
class Passage:
    pid: str
    title: str
    text: str

    def as_text(self) -> str:
        return f"{self.title}\n{self.text}" if self.title else self.text


@dataclass
class Question:
    qid: str
    question: str
    answers: list[str]
    gold_ids: list[str]
    multi_hop: bool = False
    meta: dict = field(default_factory=dict)


@dataclass
class Dataset:
    name: str
    questions: list[Question]
    passages: dict[str, Passage]
    info: dict = field(default_factory=dict)
    """Counts and choices worth reporting (questions available, dropped, why)."""

    def fingerprint(self) -> str:
        """Changes whenever the corpus changes, so cached retrieval is never reused for a different corpus."""
        h = hashlib.sha256()
        for pid in sorted(self.passages):
            h.update(pid.encode())
            h.update(self.passages[pid].text.encode())
        return h.hexdigest()[:16]


def _short_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def sample(items: list, n: int, seed: int, key) -> list:
    ordered = sorted(items, key=key)
    if n >= len(ordered):
        return ordered
    return sorted(random.Random(seed).sample(ordered, n), key=key)


# --- HotpotQA ----------------------------------------------------------------


def load_hotpotqa(path: Path, n: int, seed: int, exclude_yes_no: bool = True) -> Dataset:
    records = json.loads(path.read_text())
    available = len(records)
    if exclude_yes_no:
        records = [r for r in records if normalize(r["answer"]) not in ("yes", "no")]
    chosen = sample(records, n, seed, key=lambda r: r["_id"])

    passages: dict[str, Passage] = {}
    questions = []
    for record in chosen:
        title_to_pid = {}
        for title, sentences in record["context"]:
            pid = "hp:" + _short_hash(title)
            title_to_pid[title] = pid
            passages.setdefault(pid, Passage(pid=pid, title=title, text="".join(sentences).strip()))
        gold_titles = sorted({title for title, _ in record["supporting_facts"]})
        questions.append(
            Question(
                qid="hp:" + record["_id"],
                question=record["question"],
                answers=[record["answer"]],
                gold_ids=[title_to_pid[t] for t in gold_titles if t in title_to_pid],
                multi_hop=True,
                meta={"type": record.get("type"), "level": record.get("level")},
            )
        )
    info = {"available": available, "after_yes_no_filter": len(records), "sampled": len(questions)}
    return Dataset(name="hotpotqa", questions=questions, passages=passages, info=info)


# --- Natural Questions (BEIR + NQ-open) --------------------------------------


def _read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def load_nq(beir_dir: Path, nq_open_path: Path, n: int, seed: int, n_distractors: int) -> Dataset:
    answers_by_question = {normalize(r["question"]): r["answer"] for r in _read_jsonl(nq_open_path)}
    queries = {r["_id"]: r["text"] for r in _read_jsonl(beir_dir / "queries.jsonl")}

    gold: dict[str, list[str]] = {}
    with (beir_dir / "qrels" / "test.tsv").open() as handle:
        next(handle)
        for line in handle:
            qid, pid, score = line.rstrip("\n").split("\t")
            if int(score) > 0:
                gold.setdefault(qid, []).append(pid)

    matched = [
        (qid, text, answers_by_question[normalize(text)])
        for qid, text in queries.items()
        if qid in gold and normalize(text) in answers_by_question
    ]
    chosen = sample(matched, n, seed, key=lambda item: item[0])
    gold_needed = {pid for qid, _, _ in chosen for pid in gold[qid]}

    # One pass over the corpus: keep every gold passage, and reservoir-sample the distractors.
    rng = random.Random(seed)
    passages: dict[str, Passage] = {}
    reservoir: list[Passage] = []
    seen = 0
    for record in _read_jsonl(beir_dir / "corpus.jsonl"):
        passage = Passage(pid="nq:" + record["_id"], title=record.get("title", ""), text=record["text"])
        if record["_id"] in gold_needed:
            passages[passage.pid] = passage
            continue
        seen += 1
        if len(reservoir) < n_distractors:
            reservoir.append(passage)
        else:
            slot = rng.randrange(seen)
            if slot < n_distractors:
                reservoir[slot] = passage
    for passage in reservoir:
        passages[passage.pid] = passage

    questions = [
        Question(qid="nq:" + qid, question=text, answers=list(answers), gold_ids=["nq:" + p for p in gold[qid]])
        for qid, text, answers in chosen
    ]
    info = {
        "beir_queries": len(queries),
        "matched_to_nq_open": len(matched),
        "sampled": len(questions),
        "distractors": len(reservoir),
    }
    return Dataset(name="nq", questions=questions, passages=passages, info=info)


# --- ragaudit-generated corpora (invented docs, UTM calendar) ---------------


def load_documents_any(folder: Path):
    """ragaudit's loader for .md/.txt, plus .json/.jsonl records that have a 'text' or 'content' field."""
    from ragaudit.ingest.loader import load_documents
    from ragaudit.models.document import Document

    documents = list(load_documents(folder))
    for path in sorted(folder.rglob("*")):
        if path.suffix not in (".json", ".jsonl"):
            continue
        rows = list(_read_jsonl(path)) if path.suffix == ".jsonl" else json.loads(path.read_text())
        rows = rows if isinstance(rows, list) else [rows]
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            text = row.get("text") or row.get("content")
            if not isinstance(text, str) or not text.strip():
                continue
            title = row.get("title") or row.get("url") or ""
            content = f"# {title}\n\n{text}" if title else text
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            documents.append(
                Document(
                    doc_id=hashlib.sha256(f"{path}#{i}:{content_hash}".encode()).hexdigest(),
                    source_path=f"{path}#{i}",
                    content=content,
                    content_hash=content_hash,
                )
            )
    return documents


def chunk_corpus(folder: Path):
    from ragaudit.ingest.chunker import chunk_document

    chunks = []
    for document in load_documents_any(folder):
        chunks.extend(chunk_document(document))
    return chunks


def generate_questions_for_chunks(
    chunks, generator, verifier, out_path: Path, max_facts: int = 3, on_chunk=None
) -> None:
    """Run ragaudit's v2 pipeline (facts -> question -> de-wording -> checks -> independent verification).

    Results are appended to out_path one chunk per line, so a restart skips chunks already done.
    """
    from ragaudit.generate.pipeline import (
        DEFAULT_LEXICAL_THRESHOLD,
        build_checked_question,
        extract_facts,
        write_question,
    )

    done = {row["chunk_id"] for row in _read_jsonl(out_path)} if out_path.exists() else set()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pending = [c for c in chunks if c.chunk_id not in done]
    for i, chunk in enumerate(pending, start=1):
        facts = extract_facts(generator, chunk, max_facts) or []
        built = []
        for item in facts:
            draft = write_question(generator, item["fact"], item["answer"], [chunk])
            if draft is None:
                continue
            question, _ = build_checked_question(
                generator, verifier, [chunk], item["fact"], item["answer"], draft, DEFAULT_LEXICAL_THRESHOLD
            )
            built.append(
                {
                    "question": question.question,
                    "gold_answer": question.gold_answer,
                    "fact": question.fact,
                    "status": str(question.status),
                    "reject_reason": question.reject_reason,
                    "generator_model": question.generator_model,
                    "verifier_model": question.verifier_model,
                    "lexical_overlap": question.lexical_overlap,
                }
            )
        with out_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"chunk_id": chunk.chunk_id, "questions": built}) + "\n")
        if on_chunk:
            on_chunk(i, len(pending))


def load_generated(name: str, chunks, generated_path: Path, n: int, seed: int) -> Dataset:
    passages = {
        f"{name}:{c.chunk_id[:16]}": Passage(pid=f"{name}:{c.chunk_id[:16]}", title="", text=c.text) for c in chunks
    }
    by_chunk = {row["chunk_id"]: row["questions"] for row in _read_jsonl(generated_path)}
    active: list[Question] = []
    rejected: dict[str, int] = {}
    for chunk in chunks:
        for j, q in enumerate(by_chunk.get(chunk.chunk_id, [])):
            if q["status"] == "active":
                active.append(
                    Question(
                        qid=f"{name}:{chunk.chunk_id[:16]}:{j}",
                        question=q["question"],
                        answers=[q["gold_answer"]],
                        gold_ids=[f"{name}:{chunk.chunk_id[:16]}"],
                        meta={"generator": q["generator_model"], "verifier": q["verifier_model"]},
                    )
                )
            else:
                reason = q.get("reject_reason") or "unknown"
                rejected[reason] = rejected.get(reason, 0) + 1
    chosen = sample(active, n, seed, key=lambda q: q.qid)
    info = {
        "chunks": len(chunks),
        "chunks_generated": sum(1 for c in chunks if c.chunk_id in by_chunk),
        "verified_questions": len(active),
        "rejected": rejected,
        "sampled": len(chosen),
    }
    return Dataset(name=name, questions=chosen, passages=passages, info=info)


# --- Toy datasets for --mock runs and tests -----------------------------------

TOY_WORDS = ["Orvane", "Kelmar", "Tessix", "Brundle", "Vaskor", "Quillon", "Marrow", "Zephan", "Lorrin", "Ostrava"]
TOY_RELATIONS = [
    ("capital", "What is the capital of {e}?", "Which city is the seat of government of the region coded {c}?"),
    ("founder", "Who is the founder of {e}?", "Which person started the group coded {c}?"),
    ("river", "What is the main river of {e}?", "Which waterway flows through the area coded {c}?"),
]


def toy_dataset(
    name: str,
    n: int,
    seed: int,
    memory_rate: float,
    alias_rate: float = 0.3,
    awkward_rate: float = 0.1,
    offset: int = 0,
):
    """A made-up corpus with known answers, plus the 'memory' a mock model should have.

    memory_rate: share of questions the mock model knows closed-book (0 for the invented control).
    alias_rate: share of questions that name the subject by a code the passage never uses, so retrieval misses.
    awkward_rate: share of passages worded so the mock model can't read the answer (grounding failures).
    offset keeps entity names unique across toy datasets.
    Returns (dataset, memory) where memory maps question text -> answer.
    """
    rng = random.Random(seed)
    passages: dict[str, Passage] = {}
    questions: list[Question] = []
    memory: dict[str, str] = {}
    for i in range(n):
        entity = f"{rng.choice(TOY_WORDS)} {offset + i}"
        relation, plain, aliased = TOY_RELATIONS[i % len(TOY_RELATIONS)]
        answer = f"{rng.choice(TOY_WORDS)}{rng.randint(10, 99)}"
        pid = f"{name}:p{i}"
        wording = (
            "The {r} of {e}, by most accounts, is {a}." if rng.random() < awkward_rate else "The {r} of {e} is {a}."
        )
        passages[pid] = Passage(pid=pid, title=entity, text=wording.format(r=relation, e=entity, a=answer))
        if rng.random() < alias_rate:
            text = aliased.format(c=f"ZX{offset + i}")
        else:
            text = plain.format(e=entity)
        questions.append(Question(qid=f"{name}:q{i}", question=text, answers=[answer], gold_ids=[pid]))
        if rng.random() < memory_rate:
            memory[text] = answer
    for j in range(n * 3):
        entity = f"{rng.choice(TOY_WORDS)} {offset + n + j}"
        relation = TOY_RELATIONS[j % len(TOY_RELATIONS)][0]
        pid = f"{name}:d{j}"
        passages[pid] = Passage(pid=pid, title=entity, text=f"The {relation} of {entity} is {rng.choice(TOY_WORDS)}.")
    info = {"toy": True, "memory_rate": memory_rate, "sampled": n}
    return Dataset(name=name, questions=questions, passages=passages, info=info), memory


def dataset_to_json(dataset: Dataset) -> dict:
    return {"name": dataset.name, "info": dataset.info, "questions": [asdict(q) for q in dataset.questions]}
