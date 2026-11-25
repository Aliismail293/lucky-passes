"""Download HotpotQA, BEIR nq and NQ-open into data/raw/. Skips files that are already there.

Run on your Mac: `uv run python scripts/download_data.py` (about 0.5 GB, mostly the BEIR nq zip).
Add `--only hotpotqa` to fetch just what the pilot needs.
"""

import argparse
import json
import sys
import zipfile
from collections.abc import Iterable
from pathlib import Path

import httpx

from lp.config import Paths

SOURCES = {
    "hotpotqa": [
        ("hotpot_dev_distractor_v1.json", "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json")
    ],
    "nq": [
        ("nq.zip", "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nq.zip"),
        (
            "NQ-open.dev.jsonl",
            "https://raw.githubusercontent.com/google-research-datasets/natural-questions/master/nq_open/NQ-open.dev.jsonl",
        ),
    ],
}

# The CMU host stopped resolving (Nov 2026). Fallback: the same distractor dev split on Hugging Face, as parquet,
# pinned to a revision so the bytes can't change under us. URL taken from the dataset's file listing.
HF_REVISION = "1908d6afbbead072334abe2965f91bd2709910ab"
HOTPOT_PARQUET_URL = (
    f"https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/{HF_REVISION}/distractor/validation-00000-of-00001.parquet"
)
FALLBACKS = {"hotpot_dev_distractor_v1.json": HOTPOT_PARQUET_URL}

# The BEIR host (public.ukp.informatik.tu-darmstadt.de) timed out (Nov 2026). Fallback: the same BEIR nq files on
# Hugging Face (BeIR/nq and BeIR/nq-qrels), pinned to revisions, written out in the layout of the BEIR zip.
BEIR_NQ_REVISION = "b7253e6c379163d024ddb1d6948152a91a2e3b46"
BEIR_NQ_QRELS_REVISION = "519acd4e48bb3e5da22b2b888ce36c614f4f2bc9"
BEIR_NQ_HF = {
    "corpus": f"https://huggingface.co/datasets/BeIR/nq/resolve/{BEIR_NQ_REVISION}/corpus/corpus-00000-of-00001.parquet",
    "queries": f"https://huggingface.co/datasets/BeIR/nq/resolve/{BEIR_NQ_REVISION}/queries/queries-00000-of-00001.parquet",
    "qrels": f"https://huggingface.co/datasets/BeIR/nq-qrels/resolve/{BEIR_NQ_QRELS_REVISION}/test.tsv",
}


def hf_rows_to_hotpot(rows: Iterable[dict]) -> list[dict]:
    """Turn Hugging Face hotpot_qa rows back into the original HotpotQA JSON records.

    HF stores supporting_facts as {title: [...], sent_id: [...]} and context as {title: [...], sentences: [...]};
    the original file (and lp.datasets.load_hotpotqa) uses [[title, sent_id], ...] and [[title, [sentences]], ...].
    """
    records = []
    for row in rows:
        facts, context = row["supporting_facts"], row["context"]
        records.append(
            {
                "_id": row["id"],
                "question": row["question"],
                "answer": row["answer"],
                "type": row["type"],
                "level": row["level"],
                "supporting_facts": [[t, int(i)] for t, i in zip(facts["title"], facts["sent_id"], strict=True)],
                "context": [[t, list(s)] for t, s in zip(context["title"], context["sentences"], strict=True)],
            }
        )
    return records


def parquet_to_hotpot_json(parquet_path: Path, target: Path) -> int:
    import pyarrow.parquet as pq

    records = hf_rows_to_hotpot(pq.read_table(parquet_path).to_pylist())
    partial = target.with_suffix(target.suffix + ".part")
    partial.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    partial.rename(target)
    return len(records)


def download_hotpot_from_hf(target: Path) -> None:
    parquet = target.with_name("hotpot_dev_distractor_hf.parquet")
    download(HOTPOT_PARQUET_URL, parquet)
    n = parquet_to_hotpot_json(parquet, target)
    parquet.unlink()
    print(f"wrote {n} records to {target.name}")


def parquet_to_jsonl(parquet_path: Path, target: Path, fields: tuple[str, ...]) -> int:
    """Write one JSON object per row with just `fields`, in batches so the 0.8 GB corpus never sits in memory."""
    import pyarrow.parquet as pq

    partial = target.with_suffix(target.suffix + ".part")
    n = 0
    with partial.open("w", encoding="utf-8") as handle:
        for batch in pq.ParquetFile(parquet_path).iter_batches(columns=list(fields)):
            for row in batch.to_pylist():
                handle.write(json.dumps({f: row[f] for f in fields}, ensure_ascii=False) + "\n")
                n += 1
    partial.rename(target)
    return n


def download_beir_nq_from_hf(raw: Path) -> None:
    """Rebuild raw/nq/{corpus.jsonl, queries.jsonl, qrels/test.tsv}, the files load_nq reads from the BEIR zip."""
    nq = raw / "nq"
    (nq / "qrels").mkdir(parents=True, exist_ok=True)
    for name, out, fields in (
        ("queries", nq / "queries.jsonl", ("_id", "text")),
        ("corpus", nq / "corpus.jsonl", ("_id", "title", "text")),
    ):
        if out.exists():
            continue
        parquet = raw / f"beir_nq_{name}.parquet"
        if not parquet.exists():
            download(BEIR_NQ_HF[name], parquet)
        print(f"wrote {parquet_to_jsonl(parquet, out, fields)} rows to nq/{out.name}")
        parquet.unlink()
    if not (nq / "qrels" / "test.tsv").exists():
        download(BEIR_NQ_HF["qrels"], nq / "qrels" / "test.tsv")


def download(url: str, target: Path) -> None:
    partial = target.with_suffix(target.suffix + ".part")
    print(f"downloading {url}")
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        done = 0
        with partial.open("wb") as handle:
            for block in response.iter_bytes(1 << 20):
                handle.write(block)
                done += len(block)
                if total:
                    print(f"\r  {done / 1e6:.0f} / {total / 1e6:.0f} MB", end="", flush=True)
    print()
    partial.rename(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(SOURCES), default=None)
    args = parser.parse_args()
    raw = Paths().raw_data
    raw.mkdir(parents=True, exist_ok=True)
    for name, files in SOURCES.items():
        if args.only and name != args.only:
            continue
        for filename, url in files:
            target = raw / filename
            if target.exists() or (filename == "nq.zip" and (raw / "nq" / "corpus.jsonl").exists()):
                print(f"have {target.name}")
                continue
            try:
                download(url, target)
            except httpx.HTTPError as exc:
                if filename == "nq.zip":
                    print(f"FAILED {url}: {exc}\ntrying Hugging Face fallback (BeIR/nq)")
                    try:
                        download_beir_nq_from_hf(raw)
                    except httpx.HTTPError as exc2:
                        print(f"FAILED Hugging Face BeIR/nq: {exc2}\nPut nq.zip at {target} by hand", file=sys.stderr)
                        return 1
                    continue
                if filename not in FALLBACKS:
                    print(f"FAILED {url}: {exc}\nDownload it in a browser and put it at {target}", file=sys.stderr)
                    return 1
                print(f"FAILED {url}: {exc}\ntrying Hugging Face fallback")
                try:
                    download_hotpot_from_hf(target)
                except httpx.HTTPError as exc2:
                    print(f"FAILED {FALLBACKS[filename]}: {exc2}\nPut the file at {target} by hand", file=sys.stderr)
                    return 1
    zipped = raw / "nq.zip"
    if zipped.exists() and not (raw / "nq" / "corpus.jsonl").exists():
        print("unzipping nq.zip")
        with zipfile.ZipFile(zipped) as archive:
            archive.extractall(raw)
    print("data ready in", raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
