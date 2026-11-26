# Fact sheet: Reproducibility

These are notes for Ali, who writes every sentence; this file is not paper text.

## What is released
- **Code, configs, per-question records (`results/*/records.jsonl`) and summaries (`results/*/summary.json`):** in the
  repository.
  - In the CODEX paper, the link is `\repolink`, an anonymised copy for double-blind review. See NEEDS_ALI.
- **Every table and figure** is generated from the summaries by `scripts/make_paper_assets.py`; none is edited by hand.
- **Number checks:**
  - `scripts/check_numbers.py` fails if the paper states a number that no results file holds.
  - `scripts/check_factsheets.py` does the same for these fact sheets.

## Determinism
- **Local models:** every model runs in Ollama with temperature 0 and seed 13 `[src: configs/core.yaml#seed]`.
- **Fixed sampling:** question samples use that same fixed seed.
- **Disk cache:** every model call is cached, keyed by a hash of the model, prompt and decoding parameters. A stopped
  run resumes where it stopped; a rerun with nothing changed makes no model calls.
- **Pinned data:** the data download uses pinned revisions (`scripts/download_data.py`).

## Evidence that it reproduces
- **Fresh-clone rerun of the pilot**, on 2026-11-25 (`paper/REPRODUCTION.md`):
  - Clean clone, empty cache, fresh data download, then the README's 3 commands.
  - The rerun's 444 records matched the committed `results/pilot/records.jsonl` field by field.
  - It also regenerated the same 48 invented questions `[src: results/pilot/summary.json#meta/datasets/invented/verified_questions]`.
- **Caveats:**
  - Same machine, same Ollama install. Outputs can differ across Ollama versions and hardware; say so.
  - That rerun used the pilot configuration from before fix attempt 2. Attempt 2 didn't change the pilot, because
    the qwen generators kept prompt v2.

## Commands
- **Set up:** `uv sync`, then `uv run python scripts/download_data.py`.
- **Pilot:** `bash scripts/overnight.sh pilot`.
- **Full run:** `bash scripts/overnight.sh full --approve-hours N` runs the core grid, then the k-sweep, then the
  paper assets.
  - Core produced 4479 records, and the k-sweep 1494, on one Mac with local Ollama (logs: research-progress.md,
    2026-11-25 19:45 to 2026-11-26 07:15).
- **Analysis**, all from the committed records with no model calls:
  - `uv run python scripts/compare_conditions.py`: paired tests → `results/comparisons.json`;
  - `uv run python scripts/utm_sensitivity.py results/core`: the post-hoc UTM check;
  - `uv run python scripts/make_paper_assets.py`: tables and figures. The PDFs carry no creation date, so a rebuild is
    byte-identical.

## Guiding questions for writing this section
- What would a stranger need, beyond the 3 commands, to get your exact numbers?
- Which parts aren't deterministic (Ollama version, hardware), and how big a difference would you expect?
