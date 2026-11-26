# Data licences

Raw data is not committed. `scripts/download_data.py` fetches it into `data/raw/`.
Each licence below was checked against its source page on 2026-11-24 (Phase 1, ground rule B2.7). The exact
wording found is quoted under the table.

| Dataset | Source | Licence | Research use |
|---|---|---|---|
| HotpotQA distractor dev (`hotpot_dev_distractor_v1.json`) | https://hotpotqa.github.io/ | CC BY-SA 4.0 (verified 2026-11-24) | yes |
| BEIR `nq` (queries, qrels, corpus) | https://github.com/beir-cellar/beir | Natural Questions: CC BY-SA 3.0 (verified 2026-11-24; BEIR only redistributes, the original licence applies) | yes |
| NQ-open dev answers (`NQ-open.dev.jsonl`) | https://github.com/google-research-datasets/natural-questions/tree/master/nq_open | CC BY-SA 3.0 (verified 2026-11-24) | yes |
| ragaudit invented demo corpus | https://github.com/Aliismail293/rag-tester | MIT (Ali's own work; GitHub reports MIT, verified 2026-11-24) | yes |
| UTM academic calendar text | Waypoint's stored copy (`data/corpus/`), public pages; not re-crawled | public web pages, quoted for research (**open:** can't be checked automatically because the site returns 403 to bots; Ali to confirm the wording with a supervisor, see NEEDS_ALI.md) | yes |

### What each source page says (fetched 2026-11-24)
- HotpotQA (hotpotqa.github.io): "HotpotQA is distributed under a CC BY-SA 4.0 License." The Hugging Face
  `hotpotqa/hotpot_qa` card we fall back to also lists `cc-by-sa-4.0`.
- NQ-open (`nq_open/README.md` in google-research-datasets/natural-questions): "All of the Natural Questions data is
  released under the [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) license." The repo's
  `LICENSE` file is Apache 2.0, which covers the code, not the data.
- BEIR (README): "We only distribute these datasets in a specific format, but we do not vouch for their quality or
  fairness, or claim that you have license to use the dataset. It remains the user's responsibility to determine
  whether you as a user have permission to use the dataset under the dataset's license". So BEIR `nq` falls
  under the Natural Questions licence above (CC BY-SA 3.0).
- CC BY-SA allows research use with attribution. Share-alike applies if we redistribute the data or derived
  data, which matters for the `results/` files that quote passages. Cite both datasets, and keep this licence
  in the repo README.

## HotpotQA download source (changed 2026-11-24)
The original host `curtis.ml.cmu.edu` no longer resolves (DNS failure), so `scripts/download_data.py` still tries
it first and then falls back to the same distractor dev split on Hugging Face (`hotpotqa/hotpot_qa`, config
`distractor`, split `validation`, file `distractor/validation-00000-of-00001.parquet`, pinned to revision
`1908d6afbbead072334abe2965f91bd2709910ab`; the dataset card lists CC BY-SA 4.0). The parquet is converted back to
the original JSON layout (`supporting_facts` as `[[title, sent_id], ...]`, `context` as `[[title, [sentences]], ...]`)
and written as `hotpot_dev_distractor_v1.json`: 7405 records, the same count as the original dev distractor file.

## Why NQ needs two sources
BEIR's `nq` gives the gold passages (qrels) but no answer strings. NQ-open gives answer strings for the
same Natural Questions dev questions. `lp/datasets.py` joins them on the normalised question text and keeps
only questions that match; the number kept is logged in each run's `summary.json`.
