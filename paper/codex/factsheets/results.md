# Fact sheet: Results and Discussion

These are notes for Ali, who writes every sentence; this file is not paper text. Each number carries a source tag.
`uv run python scripts/check_factsheets.py` resolves every tag and fails if a number doesn't match its source.

**Sources:**
- `results/core/summary.json` and `results/ksweep/summary.json`: the runs.
- `results/comparisons.json`: paired tests, from `scripts/compare_conditions.py`.
- `results/core/utm_sensitivity.json`: post-hoc, from `scripts/utm_sensitivity.py`.
- `results/core/error_sample.csv`: Claude's categories, from `scripts/export_error_sample.py`.
- `results/extra_analyses.json`: analyses added after the internal review (Phase 7), from
  `scripts/extra_analyses.py`.

`results/FINDINGS.md` has the same results in plain words.

**Reading the numbers:**
- Rates are % with 95% bootstrap intervals, and n is the number of questions.
- "Lucky pass" means the **pre-registered main rule** (hit_any): correct, with no gold passage in the top k.
- "Secondary rule" means hit_all: correct, but not every gold passage in the top k.

**Pending Ali:** the judge's accuracy on the 50-item audit (`audit/audit_sheet.csv`, NEEDS_ALI item E). Until then,
every rate rests on the LLM judges.

## 1. Headline: hybrid retrieval, k = 5 (main table: `paper/tables/core/headline_hybrid_k5.tex`; all retrievers: `main_table.tex`)
Lucky-pass rate under the main rule:

**HotpotQA:**
- qwen2.5:7b: 0.0% [0.0, 0.0], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=hybrid]/rates/lucky_pass]`
- llama3.1:8b: 0.0% [0.0, 0.0], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=llama3.1:8b,retriever=hybrid]/rates/lucky_pass]`
- llama3.2:3b: 0.0% [0.0, 0.0], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=llama3.2:3b,retriever=hybrid]/rates/lucky_pass]`

**Natural Questions:**
- qwen2.5:7b: 0.0% [0.0, 0.0], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=qwen2.5:7b,retriever=hybrid]/rates/lucky_pass]`
- llama3.1:8b: 0.0% [0.0, 0.0], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=llama3.1:8b,retriever=hybrid]/rates/lucky_pass]`
- llama3.2:3b: 0.0% [0.0, 0.0], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=llama3.2:3b,retriever=hybrid]/rates/lucky_pass]`

**UTM calendar:**
- qwen2.5:7b: 15.3% [10.0, 21.3], n = 150 `[src: results/core/summary.json#cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/rates/lucky_pass]`
- llama3.1:8b: 15.4% [10.1, 21.5], n = 149 `[src: results/core/summary.json#cells[dataset=utm,model=llama3.1:8b,retriever=hybrid]/rates/lucky_pass]`
- llama3.2:3b: 12.7% [8.0, 18.0], n = 150 `[src: results/core/summary.json#cells[dataset=utm,model=llama3.2:3b,retriever=hybrid]/rates/lucky_pass]`

**Invented corpus:**
- qwen2.5:7b: 0.0% [0.0, 0.0], n = 48 `[src: results/core/summary.json#cells[dataset=invented,model=qwen2.5:7b,retriever=hybrid]/rates/lucky_pass]`
- llama3.1:8b: 0.0% [0.0, 0.0], n = 48 `[src: results/core/summary.json#cells[dataset=invented,model=llama3.1:8b,retriever=hybrid]/rates/lucky_pass]`
- llama3.2:3b: 0.0% [0.0, 0.0], n = 48 `[src: results/core/summary.json#cells[dataset=invented,model=llama3.2:3b,retriever=hybrid]/rates/lucky_pass]`

**Largest public-benchmark rates (BM25 or dense):**
- HotpotQA, dense, qwen2.5:7b: 1.3% [0.0, 3.3], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=dense]/rates/lucky_pass]`
- NQ, BM25, qwen2.5:7b: 1.3% [0.0, 3.3], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=qwen2.5:7b,retriever=bm25]/rates/lucky_pass]`

**Context for the same cells** (qwen2.5:7b, hybrid):
- **Answer accuracy:**
  - HotpotQA: 66.0% [58.0, 73.3], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=hybrid]/rates/accuracy]`
  - NQ: 82.7% [76.0, 88.7], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=qwen2.5:7b,retriever=hybrid]/rates/accuracy]`
  - UTM: 72.7% [65.3, 79.3], n = 150 `[src: results/core/summary.json#cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/rates/accuracy]`
- **Any-gold hit@5:**
  - HotpotQA: 99.3% [98.0, 100.0], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=hybrid]/rates/hit_any]`
  - NQ: 97.3% [94.7, 99.3], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=qwen2.5:7b,retriever=hybrid]/rates/hit_any]`
  - UTM: 64.7% [57.3, 71.3], n = 150 `[src: results/core/summary.json#cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/rates/hit_any]`
- *Why it matters:* on the public benchmarks, retrieval almost always finds at least one gold passage, so there is
  little room for a lucky pass under the main rule.

## 1b. Why the public rates are low, and exact intervals (added after the internal review)
- **The bootstrap collapses at 0.** Every [0.0, 0.0] above is the percentile bootstrap, which collapses when
  nothing is observed. The exact (Clopper–Pearson) intervals are:
  - HotpotQA, qwen2.5:7b, hybrid: 0.0% [0.0, 2.4], n = 150 `[src: results/extra_analyses.json#core/cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=hybrid]/lucky_pass_exact]`
  - Invented, qwen2.5:7b, hybrid: 0.0% [0.0, 7.4], n = 48 `[src: results/extra_analyses.json#core/cells[dataset=invented,model=qwen2.5:7b,retriever=hybrid]/lucky_pass_exact]`
  - The highest public cell, HotpotQA, dense, qwen2.5:7b: 1.3% [0.2, 4.7], n = 150 `[src: results/extra_analyses.json#core/cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=dense]/lucky_pass_exact]`
  - UTM, qwen2.5:7b, hybrid: 15.3% [10.0, 22.1], n = 150 `[src: results/extra_analyses.json#core/cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/lucky_pass_exact]`
- **Few chances.** At hybrid k = 5, the number of questions with no gold passage retrieved was:
  - HotpotQA: 1 `[src: results/extra_analyses.json#core/cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=hybrid]/no_gold_retrieved]`;
  - NQ: 4 `[src: results/extra_analyses.json#core/cells[dataset=nq,model=qwen2.5:7b,retriever=hybrid]/no_gold_retrieved]`;
  - invented: 0 `[src: results/extra_analyses.json#core/cells[dataset=invented,model=qwen2.5:7b,retriever=hybrid]/no_gold_retrieved]`;
  - UTM: 53 `[src: results/extra_analyses.json#core/cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/no_gold_retrieved]`, out of 150.
  - So the invented control could not show a lucky pass at all.
- **But misses are often answered right.** Accuracy *given no gold retrieved*, pooled over models and retrievers
  (records, not questions):
  - HotpotQA: 11.1% [3.7, 24.1], n = 45 `[src: results/extra_analyses.json#core/accuracy_given_no_gold_pooled/hotpotqa]`
  - NQ: 7.0% [1.9, 17.0], n = 57 `[src: results/extra_analyses.json#core/accuracy_given_no_gold_pooled/nq]`
  - UTM: 45.9% [41.8, 50.0], n = 588 `[src: results/extra_analyses.json#core/accuracy_given_no_gold_pooled/utm]`
- **HotpotQA, accuracy given that *not all* gold paragraphs were retrieved** (the measure in Jonah et al.):
  - qwen2.5:7b, dense: 44.6% [31.3, 58.5], n = 56 `[src: results/extra_analyses.json#core/cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=dense]/accuracy_given_not_all_gold]`
  - llama3.2:3b, dense: 17.9% [8.9, 30.4], n = 56 `[src: results/extra_analyses.json#core/cells[dataset=hotpotqa,model=llama3.2:3b,retriever=dense]/accuracy_given_not_all_gold]`
  - This partly *reproduces* their finding, so don't frame it as a contradiction.
- *Reading:* the lucky-pass rate = (accuracy given a miss) × (miss rate). It is small on public data because misses
  are rare, not because models can't answer without gold.

## 2. H1, high on public data and near zero on the invented corpus: not supported; the control can't test it
- The invented half is vacuous: with dense or hybrid retrieval there was no question without gold retrieved
  (section 1b).
- The public half doesn't: HotpotQA and NQ are at most 1.3% (section 1).
- **Secondary rule on HotpotQA** (correct, but one of the two needed paragraphs missing):
  - qwen2.5:7b with BM25: 24.7% [18.0, 31.3], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=qwen2.5:7b,retriever=bm25]/rates/lucky_pass_all]`
  - llama3.2:3b with hybrid: 6.7% [2.7, 10.7], n = 150 `[src: results/core/summary.json#cells[dataset=hotpotqa,model=llama3.2:3b,retriever=hybrid]/rates/lucky_pass_all]`
  - *Why it's weaker evidence:* the model had half the evidence, so it is "lucky" only in a loose sense.

## 3. The UTM result is mostly a measurement artifact (post-hoc, not pre-registered)
- **Boilerplate questions.** Of the UTM questions, 74 `[src: results/core/utm_sensitivity.json#thresholds/10/boilerplate_questions]`
  have an answer whose text appears in at least 10 of the 125 calendar chunks `[src: results/core/utm_sensitivity.json#chunks]`
  (e.g. "In Class", "Science"). They produce 234 `[src: results/core/utm_sensitivity.json#thresholds/10/lucky_records_boilerplate]`
  of the 270 `[src: results/core/utm_sensitivity.json#thresholds/10/lucky_records]` UTM lucky-pass records.
  - *Why:* every course entry has those fields, so a non-gold chunk holds the same answer string.
- **Without those questions** (qwen2.5:7b, hybrid): 3.9% [0.0, 7.9], n = 76
  `[src: results/core/utm_sensitivity.json#thresholds/10/cells_without_boilerplate[model=qwen2.5:7b,retriever=hybrid]/rates/lucky_pass]`,
  against 15.3% with them (section 1).
- **Highest remaining cell** (qwen2.5:7b, dense): 11.8% [5.3, 19.7], n = 76
  `[src: results/core/utm_sensitivity.json#thresholds/10/cells_without_boilerplate[model=qwen2.5:7b,retriever=dense]/rates/lucky_pass]`.
- **Stricter threshold, 5 chunks:** it removes 82 `[src: results/core/utm_sensitivity.json#thresholds/5/boilerplate_questions]`
  questions, and the conclusion doesn't change.
- **Error analysis of 30 random lucky passes**, one per question and model. These categories are Claude's reading, not
  human labels:
  - bad question, 11 `[src: results/core/error_sample.csv#count[category_claude=bad question]]`: it names no course
    or program;
  - answer in a non-gold retrieved chunk, 11 `[src: results/core/error_sample.csv#count[category_claude=answer in a non-gold retrieved chunk]]`;
  - judge error, 6 `[src: results/core/error_sample.csv#count[category_claude=judge error]]`: an incomplete answer
    was accepted;
  - memory, 1 `[src: results/core/error_sample.csv#count[category_claude=memory]]`;
  - guess from related passages, 1 `[src: results/core/error_sample.csv#count[category_claude=guess]]`.
  - In the sample, 28 `[src: results/core/error_sample.csv#count[dataset=utm]]` items are UTM, because almost all
    lucky passes are.
- **Threshold-free check:** count only lucky passes whose retrieved passages do *not* contain the gold answer as
  whole words. For UTM, qwen2.5:7b, hybrid: 5.3% [2.3, 10.2], n = 150
  `[src: results/extra_analyses.json#core/cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/lucky_answer_not_in_context_exact]`. With
  BM25: 6.0% [2.8, 11.1], n = 150 `[src: results/extra_analyses.json#core/cells[dataset=utm,model=qwen2.5:7b,retriever=bm25]/lucky_answer_not_in_context_exact]`.
- **Threshold sweep, whole words:** at 2 chunks, 103 `[src: results/core/utm_sensitivity.json#thresholds/2/boilerplate_questions]`
  questions are dropped; at 20, 58 `[src: results/core/utm_sensitivity.json#thresholds/20/boilerplate_questions]`.
  The conclusion holds across the sweep.
- **Not the judge:** counting only contains-match decisions (judge-free), UTM, qwen2.5:7b, hybrid is still
  10.0% [5.7, 16.0], n = 150 `[src: results/extra_analyses.json#core/cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/lucky_contains_only_exact]`.
- **Error-sample intervals (exact):** judge error 20.0% [7.7, 38.6], n = 30 `[src: results/extra_analyses.json#error_sample/judge error]`.
  That's an existence claim, not a rate.
- **The methods point:** a lucky-pass count is only as good as the gold labels. Mark every chunk that holds the answer
  as gold, and reject questions with boilerplate answers.

## 4. H2, rises as retrieval weakens: mixed
**k = 1 vs k = 5** (qwen2.5:7b, hybrid; paired on the same questions):
- UTM: +12.0% [6.7, 18.0], n = 150 `[src: results/comparisons.json#h2_k[dataset=utm]/lucky_pass/diff]`,
  McNemar p = 0.0001 `[src: results/comparisons.json#h2_k[dataset=utm]/lucky_pass/mcnemar/p]`.
- HotpotQA: +1.3% [0.0, 3.3], n = 150 `[src: results/comparisons.json#h2_k[dataset=hotpotqa]/lucky_pass/diff]`,
  p = 0.5 `[src: results/comparisons.json#h2_k[dataset=hotpotqa]/lucky_pass/mcnemar/p]`.
- NQ: +2.0% [0.0, 4.7], n = 150 `[src: results/comparisons.json#h2_k[dataset=nq]/lucky_pass/diff]`,
  p = 0.25 `[src: results/comparisons.json#h2_k[dataset=nq]/lucky_pass/mcnemar/p]`.
- The UTM curve: k = 1, 27.3% [20.7, 34.7], n = 150 `[src: results/ksweep/summary.json#cells[dataset=utm,k=1]/rates/lucky_pass]`;
  k = 3, 23.3% [16.7, 30.7], n = 150 `[src: results/ksweep/summary.json#cells[dataset=utm,k=3]/rates/lucky_pass]`;
  k = 5, 15.3% (section 1). Figure: `paper/figures/ksweep/lucky_vs_k.pdf`.

**BM25 vs hybrid at k = 5:**
- UTM, qwen2.5:7b: +9.3% [4.7, 15.3], n = 150 `[src: results/comparisons.json#h2_retriever[dataset=utm,model=qwen2.5:7b]/lucky_pass/diff]`,
  p = 0.0013 `[src: results/comparisons.json#h2_retriever[dataset=utm,model=qwen2.5:7b]/lucky_pass/mcnemar/p]`.
- HotpotQA, qwen2.5:7b: +0.7% [0.0, 2.0], n = 150 `[src: results/comparisons.json#h2_retriever[dataset=hotpotqa,model=qwen2.5:7b]/lucky_pass/diff]`.
- **Secondary rule, HotpotQA, qwen2.5:7b:** +13.3% [6.7, 20.0], n = 150 `[src: results/comparisons.json#h2_retriever[dataset=hotpotqa,model=qwen2.5:7b]/lucky_pass_all/diff]`,
  p = 0.0003 `[src: results/comparisons.json#h2_retriever[dataset=hotpotqa,model=qwen2.5:7b]/lucky_pass_all/mcnemar/p]`.

**Caveat:** under the secondary rule, k = 1 vs 5 on HotpotQA is mechanical, because one passage can't hold both gold
paragraphs. Don't report it as evidence.

**Multiple comparisons:** every McNemar test in `comparisons.json` is Holm-adjusted as one family of 60
`[src: results/comparisons.json#holm_family_size]`.
- UTM k = 1 vs 5 survives: Holm p = 0.007 `[src: results/comparisons.json#h2_k[dataset=utm]/lucky_pass/mcnemar/p_holm]`.
- UTM BM25 vs hybrid survives only for llama3.2:3b: Holm p = 0.008 `[src: results/comparisons.json#h2_retriever[dataset=utm,model=llama3.2:3b]/lucky_pass/mcnemar/p_holm]`.
  For qwen2.5:7b it doesn't: Holm p = 0.07 `[src: results/comparisons.json#h2_retriever[dataset=utm,model=qwen2.5:7b]/lucky_pass/mcnemar/p_holm]`.

**Mostly mechanical:** on UTM, accuracy given no gold retrieved is flat across k:
- k = 1: 46.1% [35.4, 57.0], n = 89 `[src: results/extra_analyses.json#ksweep/cells[dataset=utm,k=1]/accuracy_given_no_gold]`
- k = 3: 49.3% [37.2, 61.4], n = 71 `[src: results/extra_analyses.json#ksweep/cells[dataset=utm,k=3]/accuracy_given_no_gold]`
- k = 5: 43.4% [29.8, 57.7], n = 53 `[src: results/extra_analyses.json#ksweep/cells[dataset=utm,k=5]/accuracy_given_no_gold]`

So weaker retrieval adds misses, and about the same share of them are answered right. That follows from the
definition.

**Reading:** the direction is right everywhere, but the effect is large and significant only on UTM, the
artifact-driven dataset, and there it is mostly more misses.

## 5. H3, larger models have more memory-lucky passes: not testable here (too few retrieval misses)
**llama3.1:8b minus llama3.2:3b** (same family, hybrid k = 5, paired):
- Memory lucky on UTM: +0.7% [0.0, 2.0], n = 149 `[src: results/comparisons.json#h3_size[dataset=utm]/memory_lucky/diff]`.
- Memory lucky on HotpotQA: +0.0% [0.0, 0.0], n = 150 `[src: results/comparisons.json#h3_size[dataset=hotpotqa]/memory_lucky/diff]`.
- All lucky passes on UTM: +2.7% [-0.7, 6.0], n = 149 `[src: results/comparisons.json#h3_size[dataset=utm]/lucky_pass/diff]`,
  p = 0.22 `[src: results/comparisons.json#h3_size[dataset=utm]/lucky_pass/mcnemar/p]`.

**The highest memory-lucky rate anywhere:** UTM, qwen2.5:7b, BM25: 4.0% [1.3, 7.3], n = 150
`[src: results/core/summary.json#cells[dataset=utm,model=qwen2.5:7b,retriever=bm25]/rates/memory_lucky]`.

**The larger model does know more closed-book:**
- NQ, llama3.1:8b: 42.7% [35.3, 51.3], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=llama3.1:8b,retriever=hybrid]/rates/closed_accuracy]`.
- NQ, llama3.2:3b: 34.0% [26.7, 42.7], n = 150 `[src: results/core/summary.json#cells[dataset=nq,model=llama3.2:3b,retriever=hybrid]/rates/closed_accuracy]`.
- The NQ difference is significant: McNemar p = 0.015 `[src: results/extra_analyses.json#core/closed_book_llama_8b_vs_3b/nq/p]`.
  The HotpotQA one (23.3% vs 20.7%) isn't: p = 0.58 `[src: results/extra_analyses.json#core/closed_book_llama_8b_vs_3b/hotpotqa/p]`.
- That knowledge doesn't become lucky passes while retrieval finds gold.
- **Confound:** qwen2.5:7b wrote the UTM questions, and its closed-book UTM accuracy is 18.0% [12.0, 24.0], n = 150
  `[src: results/core/summary.json#cells[dataset=utm,model=qwen2.5:7b,retriever=hybrid]/rates/closed_accuracy]`.
  The llama models score 1.3–3.4%.

## 6. H4, closed-book accuracy predicts the lucky-pass rate: not testable here
- **Across 12 `[src: results/comparisons.json#h4_closed_vs_lucky/all/cells]` hybrid k = 5 cells:** Spearman
  rho = -0.57 `[src: results/comparisons.json#h4_closed_vs_lucky/all/rho]`, permutation p = 0.06
  `[src: results/comparisons.json#h4_closed_vs_lucky/all/p]`. That's the wrong sign.
  - The sign comes from UTM: low closed-book accuracy, but the most lucky passes.
- **Without UTM**, the lucky-pass rate is 0 in every cell, so rho is undefined. 9 of the 12 points are tied at
  0, so this is really 4 datasets.
- Figure: `paper/figures/core/closed_vs_lucky.pdf`.

## 7. Judges
- **Contains-match vs LLM judges:** they agree on 6809 `[src: results/core/summary.json#judge_agreement/agree]` of
  8750 `[src: results/core/summary.json#judge_agreement/n]` items where both ran.
- **The LLM is more lenient:**
  - It accepted 1896 `[src: results/core/summary.json#judge_agreement/table/llm_only]` answers that contains-match
    rejected.
  - It rejected 45 `[src: results/core/summary.json#judge_agreement/table/contains_only]` that contains-match accepted.
  - The groups are sampled differently: every contains-reject goes to the LLM, but only 25% of contains-accepts. So
    compare rates, not counts. FINDINGS.md derives them as 26.0% and 3.1%.
- **Selection-time agreement:** 90.3% on 144 items (method fact sheet). It is optimistic, the labels came from a
  model, and the items are HotpotQA and invented only, so they don't cover NQ or UTM.
- **The two judge set-ups err in opposite directions:**
  - The qwen answers' pair false-accepts 16.0% (method fact sheet).
  - The llama answers' judge (qwen2.5:7b, v3) false-rejects 17.4% [10.1, 26.1], n = 69
    `[src: results/judge_selection_v3/summary.json#results/qwen2.5:7b/false_reject_rate]`.
  - So differences between model families are confounded with the judge.
- **The overall agreement of 6809 of 8750 isn't an estimate of anything,** because it mixes a census stratum with a
  25% sample. Use the two stratum rates.
- **Audit result:** [pending Ali's labels].

## 8. Run notes (for Limitations or Reproducibility)
- **Core:** 4479 records. One call timed out twice: llama3.1:8b on a 14-course exclusion list. So 3 UTM cells have
  n = 149, as above.
- **Bounds for the missing call** (UTM, llama3.1:8b, BM25): 24.7% [18.0, 32.4], n = 150
  `[src: results/extra_analyses.json#core/missing_call_bounds[retriever=bm25]/if_not_lucky]` to 25.3% [18.6, 33.1], n = 150
  `[src: results/extra_analyses.json#core/missing_call_bounds[retriever=bm25]/if_lucky]`. Nothing changes.
- **k-sweep:** 1494 records. Its k = 5 cells equal core's qwen2.5:7b hybrid cells.
- **Analysis decisions made after seeing the results:**
  - the UTM threshold;
  - the answer-in-context rule;
  - conditioning on a miss;
  - exact intervals;
  - the Holm family;
  - the error-sample categories.

  Say so in the paper.

## Guiding questions for writing this section
- The reviews' strongest point: the public null is mostly "retrieval rarely misses". Does your headline say that,
  and give accuracy given a miss with its n?
- The headline went against H1. How do you say "answer-only scores barely overstate retrieval on public
  benchmarks" without overclaiming? Which CI supports it?
- The UTM artifact is arguably the most useful finding for practitioners. Is it a result, or a limitation? It was
  found post hoc, so say so.
- If the audit finds the judge often accepts incomplete answers, which numbers move, and in which direction?
