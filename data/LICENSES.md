# Data licences

Raw data is not committed. `scripts/download_data.py` fetches it into `data/raw/`.
Licence lines marked **re-check** have to be confirmed against the source page in Phase 1 (ground rule B2.7)
before the paper cites them.

| Dataset | Source | Licence | Research use |
|---|---|---|---|
| HotpotQA distractor dev (`hotpot_dev_distractor_v1.json`) | https://hotpotqa.github.io/ | CC BY-SA 4.0 (**re-check**) | yes |
| BEIR `nq` (queries, qrels, corpus) | https://github.com/beir-cellar/beir | Natural Questions: CC BY-SA 3.0 (**re-check**) | yes |
| NQ-open dev answers (`NQ-open.dev.jsonl`) | https://github.com/google-research-datasets/natural-questions/tree/master/nq_open | CC BY-SA 3.0 (**re-check**) | yes |
| ragaudit invented demo corpus | https://github.com/Aliismail293/rag-tester | MIT (Ali's own work) | yes |
| UTM academic calendar text | Waypoint's stored copy (`data/corpus/`), public pages; not re-crawled | public web pages, quoted for research (**re-check** wording with supervisor) | yes |

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
