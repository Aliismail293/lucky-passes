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
