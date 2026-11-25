# Lucky passes: pilot summary (1 page)

**Question.** When a RAG answer is scored correct, how often was the right passage never retrieved? We call
those **lucky passes**. Answer-only evaluation counts them as successes, so they inflate the score by exactly the
lucky-pass rate.

**Pilot setup (2026-11-24).** Generator `qwen2.5:7b`; judge `llama3.1:8b` (a different family), with
contains-match first; hybrid retrieval (BM25 + `nomic-embed-text`, reciprocal rank fusion), top k = 5; seed 13;
95% bootstrap CIs (1000 resamples). Every question was also answered **closed-book** (no passages) and
**oracle** (gold passages only).
- **HotpotQA** distractor dev: 100 questions sampled from 6947 non-yes/no questions. Corpus: each question's
  paragraphs (gold plus distractors), pooled into one shared corpus.
- **Invented corpus**: 38 made-up documents about a fictional coastal survey office, which no model has seen.
  48 questions passed generation and cross-model verification.

| | HotpotQA (n = 100) | Invented (n = 48) |
|---|---|---|
| Answer accuracy (what answer-only eval reports) | 88.0 [81.0, 94.0] | 100.0 [100.0, 100.0] |
| True pass (correct, gold retrieved) | 88.0 [81.0, 94.0] | 100.0 [100.0, 100.0] |
| **Lucky pass (correct, no gold retrieved)** | **0.0 [0.0, 0.0]** | **0.0 [0.0, 0.0]** |
| Retrieval: any gold in top 5 | 100.0 | 100.0 |
| Retrieval: all gold in top 5 | 73.0 [64.0, 81.0] | 100.0 |
| Lucky pass if multi-hop needs *all* gold | 21.0 [13.0, 30.0] | 0.0 |
| Closed-book accuracy | 59.0 [49.0, 68.0] | 22.9 [12.5, 35.4] |
| Oracle accuracy | 95.0 [91.0, 99.0] | 100.0 [100.0, 100.0] |

**What the pilot shows**
1. **Under the main rule (any gold passage counts), there are no lucky passes on either dataset.** Retrieval
   found at least one gold passage for every question, so a lucky pass couldn't happen. At k = 5 this setup is
   too easy to test the idea: HotpotQA questions name their entities, and the invented corpus has only 38
   chunks. The full run's weaker settings (BM25 alone, k = 1) are where lucky passes can appear.
2. **For multi-hop questions, 21.0% [13.0, 30.0] were answered correctly without all the needed paragraphs**,
   against 0.0 on the invented corpus. That's the direction we expected, but see point 3.
3. **The LLM judge is too lenient, so accuracy and closed-book numbers are overstated.** Contains-match and the
   LLM judge agree on only 146 of 295 items (49.5%). Every disagreement goes one way: 149 answers the LLM judge
   called correct that contains-match didn't, and 0 the other way. Spot checks show clear errors (a different
   person's name accepted as correct). Closed-book accuracy of 22.9 on documents no model has seen is a symptom.
   The judge has to be fixed and checked against human labels before the full run.

**Cost.** 60.3 min wall time, 0 failures; 27.2 min per 100 questions per model. Projected for the full grid at
this speed: core 27.2 h, k-sweep 9.1 h (before cuts).

Code and data: https://github.com/Aliismail293/lucky-passes (all numbers from `results/pilot/summary.json`).
