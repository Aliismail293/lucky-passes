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

## Why NQ needs two sources
BEIR's `nq` gives the gold passages (qrels) but no answer strings. NQ-open gives answer strings for the
same Natural Questions dev questions. `lp/datasets.py` joins them on the normalised question text and keeps
only questions that match; the number kept is logged in each run's `summary.json`.
