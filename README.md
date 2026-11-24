# lucky-passes

**How often do answer-only scores overstate retrieval-augmented generation (RAG)?**

A *lucky pass* is a RAG answer that is judged correct even though no gold passage was retrieved.
The model got it right from memory (or by guessing), and an answer-only score gives the retriever the credit.
On a company's private documents the model has no memory to fall back on, so the score drops.

This repo measures lucky passes per question across datasets, retrievers, k and model sizes, using small
local models (Ollama). It reuses [ragaudit](https://github.com/Aliismail293/rag-tester) to generate and verify
questions for corpora that have none.

| | Answer correct | Answer wrong |
|---|---|---|
| **Gold retrieved** | True pass | Grounding failure |
| **Gold not retrieved** | **Lucky pass** | Miss |

**Overstatement = answer accuracy − true-pass rate = lucky-pass rate.**

## Reproduce in 3 commands

You need [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com) with the models in `configs/`.

```
uv sync
uv run python scripts/download_data.py
bash scripts/overnight.sh pilot
```

`bash scripts/overnight.sh full` runs the core grid and the k-sweep. Any run can be stopped and restarted:
every model call is cached in `data/cache/calls.sqlite`.

No Ollama? `uv run python scripts/run_pilot.py --mock` runs the whole pipeline on toy data with a fake model.

## Results

No real results yet. They will be in `results/<run>/` (`summary.json`, `records.jsonl`, report, tables, figures).

## Layout

| Path | What it does |
|---|---|
| `lp/datasets.py` | Loads HotpotQA, NQ (BEIR + NQ-open), and ragaudit-generated questions for the invented and UTM corpora |
| `lp/retrieve.py` | BM25, dense (nomic-embed-text), hybrid (reciprocal rank fusion) |
| `lp/generate.py` | Closed-book, RAG and oracle prompts |
| `lp/judge.py` | Contains-match plus a cross-family LLM judge, and their agreement |
| `lp/classify.py` | True pass / lucky pass / grounding failure / miss; memory vs guess lucky |
| `lp/cache.py` | Hash-keyed SQLite cache of every model call |
| `lp/stats.py` | Bootstrap CIs, paired bootstrap, exact McNemar |
| `lp/report.py` | summary.json, tables (CSV + LaTeX), figures (PNG + PDF), run report |
| `lp/runner.py` | Runs a config end to end, with the time estimate and the 10-hour gate |
| `scripts/` | download, preflight, run_pilot / run_core / run_ksweep, overnight.sh, make_paper_assets, check_numbers |

## Data licences

See `data/LICENSES.md`.
