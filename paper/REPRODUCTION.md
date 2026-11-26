# Fresh-clone reproduction (Phase 7, step 1)

- **When:** 2026-11-25, 01:55–04:39 (160.3 min of model time, nothing cached).
- **What:** `git clone --branch phase-4-full-runs` (commit dabf99b) into a temp folder, then the README's 3 commands:
  `uv sync`, `uv run python scripts/download_data.py`, `bash scripts/overnight.sh pilot`. It had its own empty
  cache and its own data download (HotpotQA from Hugging Face, BEIR nq through the Hugging Face fallback).
- **Result:** all 444 records are identical to the committed `results/pilot/records.jsonl`, field by field:
  retrieved ids, all three answers, all three verdicts, outcome, outcome under the all-gold rule, and lucky kind.
  It also regenerated the same 48 invented questions, with the same rejection counts.
  - `summary.json` cells and judge agreement are identical.
  - `scripts/check_pilot_report.py` gives OK on the reproduced run.
- **Same machine, same Ollama install.** A different Mac or Ollama version may change outputs; the paper's
  Reproducibility statement says so.

## Full-run analyses from a fresh clone (2026-11-26, Phase 7)

- Fresh clone of `phase-5-analysis` from GitHub into a temporary folder, then `uv sync`.
- Ran `scripts/compare_conditions.py`, `scripts/make_paper_assets.py` and `scripts/utm_sensitivity.py results/core`.
  These use only the committed records (plus the UTM corpus folder) and make no model calls.
- `git status` afterwards was clean. `results/comparisons.json`, `results/core/utm_sensitivity.json`, and every table
  and figure (PDF and PNG) came out byte-identical to the committed files.
- `scripts/extra_analyses.py` also needs the downloaded HotpotQA and NQ files (`scripts/download_data.py`), so it
  wasn't part of this check.
- The full model run itself (about 11 h) wasn't repeated. Every call is cached, so a re-run on this machine replays
  the cache.
