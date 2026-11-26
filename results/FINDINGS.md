# Findings (Phase 5, revised after the Phase 7 internal review)

Plain-words results of the full run, hypothesis by hypothesis.

**Definitions:**
- **Lucky pass:** this is the **pre-registered main rule**: a correct answer with *no* gold passage in the top k.
- **Secondary rule:** a correct answer with *not all* gold passages in the top k. It only differs on multi-hop
  HotpotQA.

**Intervals:**
- n is the number of questions.
- **Pre-registered:** rates use 95% percentile bootstrap intervals (1000 resamples, seed 13), taken from
  `summary.json`.
- **Added after review:** where a rate is at or near 0, the **exact** (Clopper–Pearson) interval is given as well.
  The bootstrap collapses to [0.0, 0.0] there. An exact interval says, for example, that 0 of 150 is compatible
  with up to 2.4%.

**Sources:**

| Source | Produced by | Contents |
|---|---|---|
| `results/core/summary.json` | the core run | 3 generators x 3 retrievers at k = 5 |
| `results/ksweep/summary.json` | the k-sweep | qwen2.5:7b, hybrid, k = 1, 3, 5 |
| `results/comparisons.json` | `scripts/compare_conditions.py` | paired tests, Holm-adjusted |
| `results/extra_analyses.json` | `scripts/extra_analyses.py` | the post-review analyses |
| `results/core/utm_sensitivity.json` | `scripts/utm_sensitivity.py` | post-hoc UTM check |
| `results/core/error_sample.csv` | `scripts/export_error_sample.py` | error-analysis sample |

**Not yet checked by a human.** The judge's accuracy on fresh items depends on Ali's labels in
`audit/audit_sheet.csv` (50 items, 25 of them lucky passes, unlabelled). Until then, every rate below rests on the
LLM judges. Any finding the audit undermines will be flagged here.

## The headline

1. **On HotpotQA and NQ, answer-only evaluation barely overstates retrieval, because retrieval rarely misses.**
   - The lucky-pass rate is at most 1.3% in every one of the 18 cells: n = 150 each, exact upper bounds 2.4–4.7%.
   - At hybrid k = 5, retrieval found no gold passage for only 1 of 150 HotpotQA questions and 4 of 150 NQ
     questions. So there were few chances for a lucky pass at all.
2. **When retrieval does miss, a correct answer is not rare.**
   - Pooled over models and retrievers, a correct answer came back:
     - HotpotQA: 11.1% [3.7, 24.1] of 45 miss records;
     - NQ: 7.0% [1.9, 17.0] of 57 miss records.
   - On HotpotQA, when *one* of the two gold paragraphs is missing, the answer is still correct 17.9–44.6% of the
     time (n = 54–92 per cell).
   - That is the quantity Jonah et al. study, so this partly reproduces their result rather than contradicting it.
   - The overstatement is small because misses are rare, not because models can't answer without gold.
3. **The UTM course calendar shows 12.7–24.8% lucky passes, but mostly from incomplete gold labels.**
   - In most of them, the answer string is in a retrieved passage that just isn't the labelled one.
   - Lucky passes whose retrieved context does *not* contain the answer are 2.7–6.0% per cell.
4. **The invented-corpus control is uninformative.** At hybrid and dense, retrieval never missed gold there (0 of 48),
   so a lucky pass was impossible. "0 lucky passes" there doesn't test memory either way.

**Main table (hybrid, k = 5; lucky-pass rate, exact interval):**

| Dataset | qwen2.5:7b | llama3.1:8b | llama3.2:3b | Questions with no gold retrieved |
|---|---|---|---|---|
| HotpotQA (n = 150) | 0.0 [0.0, 2.4] | 0.0 [0.0, 2.4] | 0.0 [0.0, 2.4] | 1 |
| NQ (n = 150) | 0.0 [0.0, 2.4] | 0.0 [0.0, 2.4] | 0.0 [0.0, 2.4] | 4 |
| UTM (n = 150; llama3.1:8b n = 149) | 15.3 [10.0, 22.1] | 15.4 [10.0, 22.3] | 12.7 [7.8, 19.1] | 52–53 |
| Invented (n = 48) | 0.0 [0.0, 7.4] | 0.0 [0.0, 7.4] | 0.0 [0.0, 7.4] | 0 |

## H1: high on public data, near zero on the invented corpus. Not supported, and the control can't test it

**Public half:**
- HotpotQA and NQ lucky-pass rates are 0.0–1.3% in all 18 cells.
- The highest are 1.3% [0.2, 4.7] (n = 150):
  - HotpotQA: dense retrieval, with qwen2.5:7b and with llama3.1:8b;
  - NQ: BM25, with qwen2.5:7b.
- The pre-registration didn't fix a threshold for "high". But no reading of "high" that would make 5% low fits an
  upper bound of 4.7%.

**Invented half:**
- 0 lucky passes, but it is vacuous: with dense or hybrid retrieval there was no question without gold retrieved.
  With BM25 there was 1.

**Secondary rule:**
- HotpotQA does show a large gap: from 6.7 [2.7, 10.7] (llama3.2:3b, hybrid) to 24.7 [18.0, 31.3] (qwen2.5:7b,
  BM25). These are correct answers with one of the two needed paragraphs missing.
- That is "half the evidence", not "no evidence".

**Why the public null is partly built in:**
- The NQ pool is every gold passage plus 20000 random distractors.
- HotpotQA questions name one of their two entities.
- Both make retrieval easy. A harder pool, or a weaker retriever, would give lucky passes more chances.

## The UTM result is mostly incomplete gold labels (post-hoc, not pre-registered)

**Threshold-free check** (`extra_analyses.json`):
- A lucky pass whose retrieved passages contain the gold answer as whole words is not evidence of an answer from
  outside the context.
- Without those, the UTM rate is 2.7–6.0% per cell, e.g. qwen2.5:7b with hybrid: 5.3% [2.3, 10.2], n = 150.
- Some of what remains is judge error, so it is not all memory or guessing.

**Boilerplate answers** (`utm_sensitivity.json`, whole-word matching):
- 74 of the 150 UTM questions have an answer that appears in at least 10 of the 125 chunks ("In Class",
  "Science"). They produce 234 of the 270 UTM lucky-pass records.
- Dropping them gives 1.3–11.8% per cell (n = 75–76).
- The 10-chunk threshold was picked after seeing the data, so all thresholds from 2 to 20 were checked:

  | Threshold (chunks) | Questions dropped | Remaining range |
  |---|---|---|
  | 2 | 103 | 0.0–6.5% |
  | 10 | 74 | 1.3–11.8% |
  | 20 | 58 | 1.1–10.9% |

  The conclusion holds throughout.

**Not the judge:** counting only contains-match decisions (judge-free), the UTM lucky-pass rate is still
8.0–19.5% per cell.

**Error analysis of 30 random lucky passes** (one per question and model; 28 are UTM). These categories are Claude's
reading, not human labels, and the intervals are exact:

| Category | Count | Share |
|---|---|---|
| Bad question (names no course or program) | 11 | 36.7% [19.9, 56.1] |
| Answer in a retrieved non-gold chunk | 11 | 36.7% [19.9, 56.1] |
| Judge error (incomplete answer accepted) | 6 | 20.0% [7.7, 38.6] |
| Memory | 1 | 3.3% [0.1, 17.2] |
| Guess | 1 | 3.3% [0.1, 17.2] |

**Why UTM went wrong:**
- Its questions came from a single-chunk generator (ragaudit's pipeline), which labels exactly one chunk as gold.
- Its verifier passed questions that name no course.
- **Methods point:** a lucky-pass count is only as good as the gold labels. Mark every passage that contains the
  answer as gold, and reject questions with boilerplate answers or no named subject.

## H2: rises as retrieval weakens. Mixed, and mostly mechanical

**Paired tests** (`results/comparisons.json`; diff = weaker minus stronger; exact McNemar p, then Holm-adjusted over
all 60 tests in the file):

| Comparison | Diff | McNemar p | Holm p |
|---|---|---|---|
| UTM, k = 1 vs 5 | +12.0 [6.7, 18.0] | 0.0001 | 0.007 |
| HotpotQA, k = 1 vs 5 | +1.3 [0.0, 3.3] | 0.5 | |
| NQ, k = 1 vs 5 | +2.0 [0.0, 4.7] | 0.25 | |
| UTM, BM25 vs hybrid, llama3.2:3b | +10.7 | 0.0001 | 0.008 |
| UTM, BM25 vs hybrid, qwen2.5:7b | +9.3 | 0.0013 | 0.07 |
| UTM, BM25 vs hybrid, llama3.1:8b | +9.4 | 0.0026 | 0.13 |

- After correction, the BM25 vs hybrid effect on UTM holds only for llama3.2:3b.

**The rise is mostly more misses, not more luck per miss.** On UTM, accuracy *given that no gold was retrieved* is
flat across k:

| k | Accuracy given no gold | n |
|---|---|---|
| 1 | 46.1% | 89 |
| 3 | 49.3% | 71 |
| 5 | 43.4% | 53 |

Weaker retrieval misses more often, and about the same share of misses are answered right. That near-mechanical
consequence of the definition is what H2 measured.

**Secondary rule:** BM25 is worse than hybrid on HotpotQA. The p-values are 0.0003, 0.00004 and 0.0013; Holm-adjusted
they are 0.017, 0.002 and 0.07. On NQ the p-values are 0.016, 0.016 and 0.039, and none survives Holm. k = 1 vs 5
under this rule on HotpotQA is mechanical (one passage can't hold both gold paragraphs), so it is not evidence.

## H3: larger models have more memory-lucky passes. Not testable here

- With so few retrieval misses on the public data, there is almost nothing to compare.
- Memory-lucky passes are at most 4.0% [1.3, 7.3] (UTM, qwen2.5:7b, BM25).
- **llama3.1:8b vs llama3.2:3b** (same family, hybrid k = 5), memory-lucky difference:
  - HotpotQA and NQ: +0.0;
  - UTM: +0.7 [0.0, 2.0] (n = 149).
- **Closed-book, the 8B model does know more on NQ:** 42.7% vs 34.0%, McNemar 19 vs 6 discordant, p = 0.015. On
  HotpotQA it doesn't (23.3% vs 20.7%, p = 0.58).
- **Confound:** qwen2.5:7b wrote the UTM questions, and it scores 18.0% closed-book on them against 1.3–3.4% for
  the llama models.

## H4: a dataset's closed-book accuracy predicts its lucky-pass rate. Not testable here

- Across the 12 hybrid k = 5 cells, Spearman rho = -0.57 (permutation p = 0.06). But 9 of the 12 cells are tied at
  0, so it is really 4 datasets, and the sign comes from UTM alone.
- Without UTM, the lucky-pass rate is constant at 0 and rho is undefined.

## Judges

**Contains-match vs the LLM judges.** The two kinds of item are sampled differently:
- Every answer that contains-match rejects goes to the LLM judge. Of those, the LLM accepted 1896 of 7280 (26.0%).
- Only a 25% sample of the answers contains-match accepts goes to the LLM. Of those, the LLM rejected 45 of 1470
  (3.1%).
- The raw 77.8% overall agreement mixes the two samples, so it isn't an estimate of anything. Report these two rates
  instead.

**The judges' validation is thin where it matters:**
- The 144 selection items are HotpotQA and invented only, with no NQ or UTM.
- The chosen pair cleared the 90% bar by one item.
- The reference labels are Claude Opus's, and Ali edited none.
- The two judge set-ups have opposite error profiles: the qwen answers' pair false-accepts 16.0%, while the llama
  answers' judge (qwen2.5:7b, prompt v3) false-rejects 17.4% [10.1, 26.1] of correct answers (n = 69). So cross-family comparisons are confounded by the judge.
- Ali's audit has 29 UTM and 16 NQ items and is the real check.

## Run notes

- **Core:** 4479 records.
  - One call never completed: utm:a834714a3824cdcd:1, llama3.1:8b, a 14-course exclusion list. It timed out on
    the run and on the retry, so 3 UTM cells have n = 149.
  - Worst and best case for that cell (BM25): 24.7% [18.0, 32.4] to 25.3% [18.6, 33.1] at n = 150, so nothing
    changes.
- **k-sweep:** 1494 records, none failed. Its k = 5 cells match core's qwen2.5:7b hybrid cells exactly.
- **Analysis decisions made after seeing the results** (listed for transparency):
  - the UTM boilerplate threshold;
  - the answer-in-context rule;
  - conditioning on retrieval misses;
  - exact intervals;
  - the Holm family;
  - the error-sample categories.

  None changes the pre-registered numbers in summary.json.
