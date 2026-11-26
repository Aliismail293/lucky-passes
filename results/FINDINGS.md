# Findings (Phase 5)

Plain-words results of the full run, hypothesis by hypothesis. Rates are % with 95% bootstrap intervals (1000
resamples, seed 13) and n = questions. "Lucky pass" uses the **pre-registered main rule** (correct answer, *no*
gold passage in the top k) unless it says "secondary rule" (correct answer, *not all* gold passages in the top k;
this only differs on multi-hop HotpotQA).

Sources: `results/core/summary.json` (3 generators x 3 retrievers at k = 5), `results/ksweep/summary.json`
(qwen2.5:7b, hybrid, k = 1, 3, 5), `results/comparisons.json` (paired tests, `scripts/compare_conditions.py`),
`results/core/utm_sensitivity.json` (`scripts/utm_sensitivity.py`) and `results/core/error_sample.csv`
(`scripts/export_error_sample.py`).

**Not yet checked by a human.** The judge's accuracy on fresh items depends on Ali's labels in
`audit/audit_sheet.csv` (50 items, 25 of them lucky passes, unlabelled). Until then every rate below rests on the
LLM judges. Any finding the audit undermines will be flagged here.

## The headline

**On the two public benchmarks, answer-only evaluation barely overstates retrieval: lucky passes are at most 1.3%
under the main rule.** On the invented corpus they are 0 everywhere. The one dataset with many lucky passes, the UTM
course calendar (12.7–24.8%), gets most of them from the way its questions and gold labels were built, not from
memory.

| Hybrid, k = 5 | qwen2.5:7b | llama3.1:8b | llama3.2:3b |
|---|---|---|---|
| HotpotQA (n = 150) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| NQ (n = 150) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| UTM (n = 150; llama3.1:8b n = 149) | 15.3 [10.0, 21.3] | 15.4 [10.1, 21.5] | 12.7 [8.0, 18.0] |
| Invented (n = 48) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |

The largest public-benchmark rates are under BM25 or dense retrieval: HotpotQA 1.3 [0.0, 3.3] (dense, qwen2.5:7b and
llama3.1:8b) and NQ 1.3 [0.0, 3.3] (BM25, qwen2.5:7b).

## H1 — high on public data, near zero on the invented corpus: **not supported** (main rule)

- The invented-corpus half holds: 0.0 [0.0, 0.0] in all 9 cells (n = 48).
- The public-data half doesn't: HotpotQA and NQ are 0.0–1.3% in all 18 cells (n = 150 each).
- Retrieval rarely misses every gold passage on these benchmarks. Any-gold hit@5 is 90.7–99.3%, so there are few
  chances for a lucky pass.
- **Under the secondary rule, HotpotQA does show a large gap**, from 6.7 [2.7, 10.7] (llama3.2:3b, hybrid) to
  24.7 [18.0, 31.3] (qwen2.5:7b, BM25). These are correct answers where one of the two needed paragraphs was
  missing. It's a looser notion of "lucky": the model had half the evidence.
- UTM is high (see the next section), but not because it is public.

## The UTM result is mostly a measurement artifact

- **Boilerplate answers.** 74 of the 150 UTM questions have an answer whose text appears in 10 or more of the 125
  calendar chunks ("In Class", "Science"). These questions produce 234 of the 270 UTM lucky-pass records.
  - Every course entry carries those fields, so another course's chunk holds the same answer string. "No gold
    chunk retrieved" doesn't mean the answer was missing from the context.
- **Post-hoc sensitivity check (not pre-registered).** With those questions removed, the UTM rate falls to 1.3–11.8%
  (n = 75–76 per cell); with a stricter 5-chunk threshold it is 1.5–13.2% (n = 67–68). Example: qwen2.5:7b with
  hybrid falls from 15.3 [10.0, 21.3] (n = 150) to 3.9 [0.0, 7.9] (n = 76).
- **Error analysis of 30 random lucky passes** (one per question and model; 28 are UTM because 270 of the 279
  core lucky passes are UTM). These categories are Claude's reading, not human labels:
  - bad question, 11: it names no course or program, e.g. "How is the course delivered?";
  - the answer is in a retrieved non-gold chunk, 11: duplicated or boilerplate text;
  - judge error, 6: an incomplete answer was accepted, e.g. "36" for "36L/12T", or one program of two;
  - memory, 1: NQ, "won";
  - guess from related passages, 1: HotpotQA "Suffolk", where 3 retrieved distractors are Suffolk County hamlets.
- **What it means:** a lucky-pass count is only as good as the gold labels. When a fact appears in several chunks
  but only one is labelled gold, a correct, grounded answer is scored as lucky. Question generation should reject
  questions with boilerplate answers, and every chunk that holds the answer should be marked gold. This is a
  methods finding for the paper.

## H2 — lucky passes rise as retrieval weakens: **mixed**

**Paired tests on the same questions** (`results/comparisons.json`; diff = weaker minus stronger, exact McNemar p).

**k = 1 vs k = 5** (qwen2.5:7b, hybrid):

| Dataset | Diff | McNemar p |
|---|---|---|
| UTM | +12.0 [6.7, 18.0] | 0.0001 |
| HotpotQA | +1.3 [0.0, 3.3] | 0.5 |
| NQ | +2.0 [0.0, 4.7] | 0.25 |
| Invented | 0 | – |

The UTM rate is 27.3 [20.7, 34.7] at k = 1, 23.3 [16.7, 30.7] at k = 3 and 15.3 [10.0, 21.3] at k = 5.

**BM25 vs hybrid at k = 5:**
- UTM: +9.3 to +10.7 for all three models, p ≤ 0.003.
- HotpotQA and NQ: +0.0 to +1.3, p ≥ 0.5.

**Secondary rule:** BM25 is clearly worse than hybrid on HotpotQA, by +9.3 to +13.3 (p ≤ 0.0013), and on NQ, by +4.7
(p ≤ 0.04). The k = 1 vs k = 5 difference under this rule (HotpotQA +46.0) is mostly mechanical: at k = 1 a
two-paragraph question can never have both gold paragraphs.

**Reading:** the direction is right everywhere, but the main-rule effect is large and significant only on UTM, which
is the artifact-driven dataset. On the public benchmarks it is within about 2 points and not significant.

## H3 — larger models have more memory-lucky passes: **not supported**

- Memory-lucky passes are rare everywhere: at most 4.0 [1.3, 7.3] (UTM, qwen2.5:7b, BM25) and 0.0–1.3% on HotpotQA
  and NQ.
- **llama3.1:8b vs llama3.2:3b** (same family, hybrid k = 5), memory-lucky difference:
  - HotpotQA and NQ: +0.0;
  - UTM: +0.7 [0.0, 2.0] (n = 149).

  The main-rule lucky-pass difference on UTM is +2.7 [-0.7, 6.0], McNemar p = 0.22.
- Larger models do know more closed-book: HotpotQA 23.3 vs 20.7, NQ 42.7 vs 34.0. But that knowledge doesn't turn
  into lucky passes when retrieval already finds gold.
- Only 3B to 8B models were tested, so a larger range might differ.

## H4 — a dataset's closed-book accuracy predicts its lucky-pass rate: **not supported**

- Across the 12 hybrid k = 5 cells (dataset x model), Spearman rho = -0.57, permutation p = 0.06. That's the
  opposite sign from H4.
- The negative sign comes from UTM: low closed-book accuracy (1.3–18.0%) but the most lucky passes.
- Without UTM the lucky-pass rate is 0 in all 9 cells, so the correlation is undefined.
- NQ has the highest closed-book accuracy (34.0–42.7%) and still 0 lucky passes at hybrid k = 5.

## Judges

- **Contains-match vs the LLM judges:** they agree on 6809 of 8750 items where both ran (77.8%). The table is in
  `results/core/summary.json`, `judge_agreement`.
- **The two kinds of item are sampled differently.**
  - Every answer that contains-match rejects goes to the LLM judge. Of those, the LLM accepted 1896 of 7280
    (26.0%).
  - Only a 25% sample of the answers contains-match accepts goes to the LLM. Of those, the LLM rejected 45 of 1470
    (3.1%).
  - Both percentages are derived from the table's counts.
- Many of the 1896 accepts are paraphrases. The error sample shows the LLM judge also accepts incomplete answers to
  list questions, which inflates UTM lucky passes.
- The selected judges agreed with reference labels at 90.3% on 144 pilot items. Those labels were written by Claude
  Opus, not by a human, and the judges were selected on the same items, so this is optimistic. Ali's audit is the
  unbiased check.

## Run notes

- **Core:** 4479 records. One call never completed: utm:a834714a3824cdcd:1 with llama3.1:8b, a 14-course exclusion
  list. It timed out on the run and on the retry, so 3 UTM cells have n = 149. It was left out rather than changing
  the timeout or output length after the fact.
- **k-sweep:** 1494 records, none failed. Its k = 5 cells match core's qwen2.5:7b hybrid cells exactly.
