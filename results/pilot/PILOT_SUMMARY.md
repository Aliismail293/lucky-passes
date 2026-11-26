# Lucky passes: pilot summary (1 page)

**Question.** When a RAG answer is scored correct, how often was the right passage never retrieved? We call
those **lucky passes**. Answer-only evaluation counts them as successes, so they inflate the score by exactly the
lucky-pass rate.

**Pilot setup (2026-11-25).**
- **Models:** generator `qwen2.5:7b`. Contains-match decides first; any other answer must be accepted by two LLM
  judges from other model families (`llama3.1:8b` and `gemma2:9b`).
- **Retrieval:** BM25, dense (`nomic-embed-text`), and hybrid (reciprocal rank fusion), all at top k = 5.
- **Controls:** every question is also answered **closed-book** (no passages) and **oracle** (gold passages only).
- Seed 13; 95% bootstrap CIs (1000 resamples).
- **HotpotQA** distractor dev: 100 questions sampled from 6947 non-yes/no questions. The passage pool is every
  dev-set paragraph, 66581 after deduplication.
- **Invented corpus:** 38 made-up documents about a fictional coastal survey office, which no model has seen. 48
  questions passed generation and cross-model verification.

| HotpotQA (n = 100) | BM25 | Dense | Hybrid |
|---|---|---|---|
| Answer accuracy (what answer-only eval reports) | 54.0 [45.0, 64.0] | 63.0 [54.0, 72.0] | 62.0 [53.0, 71.0] |
| **Lucky pass, main rule (pre-registered): correct, no gold passage in top 5** | **1.0 [0.0, 3.0]** | **2.0 [0.0, 5.0]** | **0.0 [0.0, 0.0]** |
| Any gold passage in top 5 | 92.0 [87.0, 97.0] | 96.0 [92.0, 99.0] | 100.0 [100.0, 100.0] |
| All gold passages in top 5 (multi-hop needs both) | 37.0 [28.0, 46.0] | 67.0 [58.0, 76.0] | 69.0 [60.0, 78.0] |
| **Lucky pass, secondary rule: correct, not *all* gold passages in top 5** | **22.0 [15.0, 30.0]** | **9.0 [4.0, 15.0]** | **4.0 [1.0, 8.0]** |

Closed-book accuracy is 22.0 [14.0, 30.0] and oracle accuracy 89.0 [83.0, 95.0], for every retriever.

**Invented corpus (n = 48), all three retrievers:**
- Lucky passes: 0.0 under both rules.
- Answer accuracy: 97.9 to 100.0.
- Closed-book accuracy: 10.4 [2.1, 18.8].

**What the pilot shows**
1. **Under the pre-registered main rule (correct, but no gold passage in the top 5), lucky passes are rare at
   k = 5.**
   - HotpotQA (n = 100 per retriever): BM25 1.0% [0.0, 3.0], dense 2.0% [0.0, 5.0], hybrid 0.0% [0.0, 0.0].
   - Invented corpus (n = 48): 0.0% [0.0, 0.0] under every retriever.
   - The 3 HotpotQA lucky passes were all answered right closed-book too ("memory lucky").
   - HotpotQA questions name one of their two entities, so retrieval almost always finds one gold paragraph.
2. **Under the secondary "all gold passages retrieved" rule, the gap is large and depends on the retriever.**
   HotpotQA questions need two paragraphs, so this rule also counts a correct answer as lucky when either one is
   missing from the top 5.
   - HotpotQA (n = 100 per retriever): BM25 22.0% [15.0, 30.0], dense 9.0% [4.0, 15.0], hybrid 4.0% [1.0, 8.0].
   - Invented corpus (n = 48): 0.0% [0.0, 0.0] under every retriever (each question has one gold passage, so
     the two rules agree there).
   - That is the effect the full study measures: how much weaker retrieval inflates answer-only scores on public
     data.
3. **Memory helps on public data, but not only there.**
   - Closed-book accuracy is 22% on HotpotQA vs 10.4% on the invented corpus.
   - On the invented corpus, part of that is guessable questions (e.g. "every 15 minutes"), and part is judge
     error, still under review.
4. **The judge was made stricter after the first pilot,** because the first judge accepted wrong answers. The
   accuracy of the current judges will be checked on a fresh, hand-labelled sample.

**Next.** The full run covers 4 datasets (adding Natural Questions and a university course calendar), 3 models
(3B to 8B) and 3 retrievers, plus a k = 1, 3, 5 sweep. Code and every result file are public.
