# Fact sheet: Results and Discussion

These are notes for Ali, who writes every sentence; this file is not paper text. Each number carries a source tag.
`uv run python scripts/check_factsheets.py` resolves every tag and fails if a number doesn't match its source.

**Sources:**
- `results/core/summary.json` and `results/ksweep/summary.json`: the runs.
- `results/comparisons.json`: paired tests, from `scripts/compare_conditions.py`.
- `results/core/utm_sensitivity.json`: post-hoc, from `scripts/utm_sensitivity.py`.
- `results/core/error_sample.csv`: Claude's categories, from `scripts/export_error_sample.py`.

`results/FINDINGS.md` has the same results in plain words.

**Reading the numbers:**
- Rates are % with 95% bootstrap intervals, and n is the number of questions.
- "Lucky pass" means the **pre-registered main rule** (hit_any): correct, with no gold passage in the top k.
- "Secondary rule" means hit_all: correct, but not every gold passage in the top k.

**Pending Ali:** the judge's accuracy on the 50-item audit (`audit/audit_sheet.csv`, NEEDS_ALI item E). Until then,
every rate rests on the LLM judges.

## 1. Headline: hybrid retrieval, k = 5 (the main table, `paper/tables/core/main_table.tex`)
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

## 2. H1, high on public data and near zero on the invented corpus: not supported (main rule)
- The invented half holds: 0 in every cell (section 1).
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

**Reading:** the direction is right everywhere, but the effect is large and significant only on UTM, the
artifact-driven dataset.

## 5. H3, larger models have more memory-lucky passes: not supported
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
- That knowledge doesn't become lucky passes while retrieval finds gold.

## 6. H4, closed-book accuracy predicts the lucky-pass rate: not supported
- **Across 12 `[src: results/comparisons.json#h4_closed_vs_lucky/all/cells]` hybrid k = 5 cells:** Spearman
  rho = -0.57 `[src: results/comparisons.json#h4_closed_vs_lucky/all/rho]`, permutation p = 0.06
  `[src: results/comparisons.json#h4_closed_vs_lucky/all/p]`. That's the wrong sign.
  - The sign comes from UTM: low closed-book accuracy, but the most lucky passes.
- **Without UTM**, the lucky-pass rate is 0 in every cell, so rho is undefined.
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
- **Selection-time agreement:** 90.3% on 144 items (method fact sheet). It is optimistic, and the labels came from
  a model.
- **Audit result:** [pending Ali's labels].

## 8. Run notes (for Limitations or Reproducibility)
- **Core:** 4479 records. One call timed out twice: llama3.1:8b on a 14-course exclusion list. So 3 UTM cells have
  n = 149, as above.
- **k-sweep:** 1494 records. Its k = 5 cells equal core's qwen2.5:7b hybrid cells.

## Guiding questions for writing this section
- The headline went against H1. How do you say "answer-only scores barely overstate retrieval on public
  benchmarks" without overclaiming? Which CI supports it?
- The UTM artifact is arguably the most useful finding for practitioners. Is it a result, or a limitation? It was
  found post hoc, so say so.
- If the audit finds the judge often accepts incomplete answers, which numbers move, and in which direction?
