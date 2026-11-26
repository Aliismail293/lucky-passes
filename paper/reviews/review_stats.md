# Review: "Lucky passes" in retrieval-augmented generation (statistics review)

Reviewer focus: are the intervals, tests and claims statistically sound? I reviewed the fact sheets
(`paper/codex/factsheets/method.md`, `results.md`, `limitations.md`), `results/FINDINGS.md`, the analysis code
(`lp/stats.py`, `lp/report.py`, `scripts/compare_conditions.py`, `scripts/utm_sensitivity.py`,
`scripts/eval_judges.py`) and the result files. I re-derived the main numbers from `results/core/records.jsonl`,
`results/ksweep/records.jsonl` and the judge-selection `items.jsonl` files (read-only; scratch scripts outside the
repo). Numbers below marked "recomputed" are mine, not the authors'.

## Summary

The study splits RAG answers into true pass, grounding failure, lucky pass (correct, no gold passage in the top k)
and miss, over 3 small local generators x 3 retrievers x 4 datasets (HotpotQA, NQ, n = 150 each; a UTM course
calendar, n = 150; an invented corpus, n = 48), plus a k-sweep. Rates carry 95% percentile-bootstrap intervals over
questions; same-question comparisons use a paired bootstrap and an exact McNemar test; H4 uses a Spearman
correlation over 12 cells with a permutation p-value. The headline is a null: under the pre-registered any-gold rule
lucky passes are 0.0-1.3% on the public benchmarks, 0 on the invented corpus, and 12.7-24.8% on UTM, which a
post-hoc analysis attributes mostly to boilerplate answers and incomplete gold labels. H1, H3 and H4 are reported
"not supported" and H2 "mixed".

The reporting is unusually transparent (source-tagged numbers, pre-registration, post-hoc analyses labelled as such,
the model-written reference labels disclosed). My main concern is inferential: most of the "not supported" verdicts
come from a design in which the event of interest had almost no chance to occur (retrieval nearly always finds a
gold passage), and the statistics used (unconditional rates, percentile bootstrap at 0, Spearman on 12 cells) hide
that rather than show it. The quantities and claims need reframing more than the experiments need re-running.

## Strengths

1. **Pre-registration and honest labelling.** The main rule (hit_any), hypotheses, judge-selection rule and bar
   were fixed before the full run. Post-hoc analyses (UTM sensitivity, error sample) are labelled as such in
   `results.md` section 3 and in the docstring of `scripts/utm_sensitivity.py`. The nulls against H1/H3/H4 are
   reported rather than buried.
2. **Paired design where it matters.** Retriever and k comparisons are on the same questions, and
   `compare_conditions.py` correctly restricts to the paired intersection (n = 149 for the three llama3.1:8b UTM
   cells). The exact McNemar implementation in `lp/stats.py` is correct (I checked it against the discordant counts
   in `results/comparisons.json`), and so is the tie-averaged rank function behind the Spearman.
3. **Every number traceable.** Fixed seeds, rates reported with n, a fact-sheet checker, and k-sweep k = 5 cells
   matching core exactly make the results reproducible and auditable.
4. **Limitations state the direction of each bias** (`limitations.md`), including the judge being selected on its
   own evaluation items and the reference labels coming from a model.
5. **The UTM gold-label artifact is a real, useful methods finding**, and it holds up beyond the authors' own
   post-hoc filter (see Weakness 4: a threshold-free reanalysis gives the same answer).

## Weaknesses

**W1. The headline nulls (H1 public half, H3, and the invented "control") are mostly no-opportunity results, not
evidence about model behaviour. The unconditional lucky-pass rate is the wrong statistic for the hypotheses as
worded.**
- The lucky-pass rate is P(correct AND no gold in top k) = P(no gold) x P(correct | no gold). On the public
  benchmarks P(no gold) is tiny, so the product is near 0 whatever the model does. Recomputed from
  `results/core/records.jsonl`, the number of questions with *no* gold passage in the top 5 (the only questions
  that *can* be lucky passes) is:
  - HotpotQA hybrid: **1 of 150**; dense: 4; BM25: 10.
  - NQ hybrid: **4 of 150**; dense: 1; BM25: 14.
  - Invented hybrid and dense: **0 of 48**; BM25: 1.
  - UTM hybrid: 52-53 of 150.
- So the "invented half holds: 0 in every cell" claim (`results.md` section 2, FINDINGS H1) is **vacuous**: at hybrid
  and dense k = 5 retrieval never missed on the invented corpus, so a lucky pass was impossible. The 0/48 says
  nothing about memory versus no memory. The control quantity H1 actually needs is closed-book accuracy, and that
  is 6.2-10.4% on the invented corpus (`summary.json`, hybrid cells), i.e. *not* near zero. That is itself a problem
  for the control (guessing plus judge false accepts; see `limitations.md` on the failed sanity gate).
- Conditional on a retrieval miss, the public benchmarks are not near zero at all (recomputed): NQ BM25 2/14
  (qwen2.5:7b); HotpotQA dense 2/4; k-sweep k = 1 HotpotQA 2/15 and NQ 3/17. Pooled over the 18 public core cells,
  9 of 102 no-gold records are correct, from only 28 distinct no-gold questions. These intervals are very wide
  (e.g. 3/17, Clopper-Pearson [3.8, 43.4]%), which is the point: on the public benchmarks the study has roughly
  1-17 informative questions per cell, not 150.
- H3 is untestable by construction. A memory-lucky pass needs a lucky pass *and* a correct closed-book answer. At
  hybrid k = 5 the opportunity set is 1 question (HotpotQA) and 4 (NQ), and on UTM the llama models are
  closed-book correct on only 5/149 (8B) and 2/150 (3B). The largest attainable McNemar discordance gives p >= 0.0625
  on UTM and >= 0.125 on NQ. "Not supported" (`results.md` section 5) should read "not testable in this design".
- **Fix:** (a) report P(correct | no gold in top k) per cell with its own n (the opportunity count) as the primary
  behavioural quantity, and keep the unconditional rate as the "how much does answer-only evaluation overstate
  retrieval" quantity, which is a legitimate, separate claim; (b) restate H1's public-benchmark result as "the
  retrievers' any-gold recall is 90.7-99.3%, so the overstatement is small", not as evidence that models rarely
  answer without evidence; (c) drop "the invented half holds", or test it at k = 1/BM25 where misses exist (still
  only 1 miss), or on a retrieval-ablated condition; (d) reword H3 as untestable, and if you want a model-size
  answer, test P(correct | no gold) or closed-book accuracy directly.

**W2. Percentile-bootstrap intervals are degenerate or anti-conservative near 0, and these are the intervals the
paper's headline table rests on.**
- 0/150 gives [0.0, 0.0] (all twelve headline public and invented cells in `results.md` section 1, FINDINGS table,
  and `paper/tables/core/headline_hybrid_k5.tex`). A zero-width interval claims certainty the data can't give. The
  exact (Clopper-Pearson) 95% interval for 0/150 is [0, 2.4]%, and for 0/48 it is **[0, 7.4]%**. The invented
  corpus can't rule out a 7% lucky-pass rate, which matters for "near zero" in H1.
- With few events the percentile bootstrap also under-covers the upper end: 2/150 is reported as [0.0, 3.3], exact
  [0.2, 4.7]. The UTM sensitivity value 3/76 = 3.9% is reported as [0.0, 7.9]: a lower bound of 0 after observing
  3 events (exact [0.8, 11.1]).
- The same applies to the paired-difference intervals with 0-3 discordant pairs ("+1.3% [0.0, 3.3]", "+0.0%
  [0.0, 0.0]" for H3 memory-lucky on HotpotQA in `results.md` section 5), and to the judge-selection false-reject
  rate "2.9% [0.0, 7.2]" (2/69) and false-accept rate "2.7% [0.0, 6.7]" (2/75).
- **Fix:** use Wilson or Clopper-Pearson intervals for single proportions (at least whenever x <= 5 or
  n - x <= 5), and for paired differences an exact interval conditional on the discordant count (or Newcombe's
  method 10). Raise resamples from 1000 to 10,000 for the remaining bootstrap intervals: at 1000 the 2.5/97.5
  percentile endpoints carry visible Monte Carlo error. In the text, give the 0/150 upper bound explicitly
  ("below 2.4% with 95% confidence"), which is a stronger and more honest statement than "0.0 [0.0, 0.0]".

**W3. Judge validity: selected and scored on the same 144 items, those items contain no UTM or NQ answers, and the
two judges have opposite error profiles, which confounds cross-model comparisons.**
- Recomputed from `results/judge_selection/items.jsonl`: the 144 labelled items are HotpotQA (110) and invented
  (34) only. **No UTM and no NQ items.** But UTM is where 270 of the 279 lucky-pass records are, and 74 of those 270
  were accepted by the LLM judge rather than by contains-match (recomputed from `judge_rag.method`). The selection
  agreement therefore says nothing about the judge on the dataset that drives every positive result.
- All 149 reference labels come from Claude: `reference_sources` is `{"claude": 149}` in both summaries, so Ali's
  "spot-check" changed no label. `method.md` should say "no labels were changed".
- Winner's curse: 12 candidates (6 per prompt version) were compared on the same 144 items. The deciding margins are
  1-2 items. Recomputed paired McNemar: qwen2.5:7b v3 vs v2, 2 vs 0 discordant, p = 0.5; the llama+gemma pair
  v2 vs v3, 7 vs 5, p = 0.77. The chosen pair's 90.3% is 130/144, which clears the pre-registered 90% bar by
  **one item**, and its lower bound (85.4) is below the bar. "Meets the bar" is not supported with any confidence.
- Opposite error profiles: the qwen-generator judge (llama+gemma v2) has false-accept 16.0% and false-reject 2.9%;
  the llama-generator judge (qwen v3) has false-accept 2.7% and false-reject 17.4% (12/69). The judge pushes qwen
  lucky-pass and accuracy rates up and llama rates down. Any comparison *across* generator families (the headline
  table's columns, the 12 H4 cells) is confounded with the judge. H3 is not affected (both llama models share a
  judge).
- The qwen judge for llama answers was scored on answers written by qwen2.5:7b, i.e. the same-family setting the
  design says it avoids. Its transfer to llama answers is unmeasured (acknowledged in `limitations.md`).
- The pending audit (`audit/audit_sheet.csv`) can't repair this as planned. Of its 50 items only **12 are
  LLM-judged** (37 contains-match, 1 non-answer). It oversamples lucky passes (25/50), so any population accuracy
  needs inverse-probability weights. A 12-item estimate of LLM-judge accuracy has a 95% interval about +/-25 points
  wide.
- **Fix:** (a) call the selection numbers "in-sample, optimistic" everywhere they appear, and drop the "meets the
  90% bar" framing; (b) stratify the audit, or add a second one, so it has >= 40 LLM-judged items with UTM and NQ
  represented, then report false-accept/false-reject per judge with exact CIs; (c) propagate judge error into the
  headline: a simple bound is lucky_LLM x FA, or a Rogan-Gladen-style correction of accuracy and lucky rates
  using the audited FA/FR, with intervals; (d) avoid cross-family comparisons, or give a sensitivity analysis that
  re-scores every cell with contains-match only (which is judge-free and available in the records).

**W4. The UTM sensitivity analysis is a post-hoc subgroup removal with a researcher-chosen threshold; a
threshold-free reanalysis exists and should replace it as the main evidence.**
- `scripts/utm_sensitivity.py` drops whole questions whose answer string occurs in >= 10 (or >= 5) chunks.
  Problems: the thresholds were chosen after seeing the data (forking paths); dropping questions changes the
  population (n = 76, not 150), so "15.3% to 3.9%" compares different question sets, not a corrected estimate on
  the same set; and the 15.3 vs 3.9 contrast has no interval for the difference.
- Record counts overstate the concentration because the same question is counted in up to 9 cells. "234 of 270
  lucky records" (`results.md` section 3) corresponds to 40 of 57 distinct lucky questions (recomputed), i.e. 70%,
  not 87%.
- In the authors' favour: the answer-frequency distribution is bimodal (45 questions at frequency 1, 57 at >= 28
  chunks), and a recomputed sweep of the threshold over {2, 3, 5, 10, 20} gives pooled UTM lucky rates of
  3.4-6.3%, so the conclusion is not knife-edge. Only at 40 does it rise (11.9%). Show this sweep.
- A cleaner, standard alternative (DPR-style "has-answer" retrieval): count a question as retrieved if any top-k
  chunk contains a gold answer string, and keep all 150 questions. Recomputed: **202 of 270** UTM lucky records
  have the answer string in a retrieved chunk. Removing them leaves 4-9 lucky passes per cell (2.7-6.0%), with an
  opportunity set of 33-37 questions per cell.
- **Fix:** report the answer-containment reclassification on all 150 questions as the primary sensitivity
  analysis, paired with the original classification (McNemar or paired difference with exact CI). Keep the
  threshold version as a secondary check with the full threshold curve, and report counts in distinct questions as
  well as records. Apply the same answer-containment rule to HotpotQA and NQ so the datasets are treated alike.
  It also partly answers W1, because it widens the opportunity set honestly.

**W5. H4: a Spearman over 12 cells is effectively a 4-point comparison of datasets, with 9 tied zeros, and the
verdict should be "untestable", not "not supported".**
- Of the 12 hybrid k = 5 cells, 9 have lucky rate exactly 0 (HotpotQA, NQ, invented). rho = -0.57 only says the
  three UTM cells have lower closed-book accuracy than the median of the rest. The 3 cells within a dataset share
  the same questions and retrieval, so they are not exchangeable units, and the permutation p = 0.06 treats them as
  if they were. With 4 datasets as the real units, the smallest attainable two-sided exact permutation p is
  2/24 = 0.083: the design cannot reject at 0.05 even with perfect ordering.
- The cells also mix judges with opposite error profiles (W3), and the UTM lucky rate is the artifact from W4.
  The "wrong sign" is therefore not interpretable.
- **Fix:** report H4 as not testable with four datasets. If you want something, show the 12 points descriptively
  (the figure exists) and, within datasets, relate *per-question* closed-book correctness to P(correct | no gold)
  using a mixed-effects logistic regression with question random effects. That pools the 3 models properly and
  uses the question as the unit.

**W6. Multiple comparisons and clustering are never addressed.**
- `results/comparisons.json` contains 60 McNemar tests (20 comparisons x 3 measures; on UTM lucky_pass and
  lucky_pass_all are identical, so some are duplicates), plus cell CIs across 36 core + 12 k-sweep cells, all read
  at nominal 5%. Recomputed Holm adjustment: within the 20 main-rule tests, all four UTM H2 results survive
  (p_adj = 0.002-0.044; the llama3.1:8b BM25 vs hybrid test only just does). Over all 60 tests, two of the three
  UTM retriever tests no longer survive (p_adj = 0.068, 0.126). The HotpotQA secondary-rule results survive in
  either family. The **NQ secondary-rule BM25 vs hybrid results (p = 0.016-0.039, FINDINGS "p <= 0.04") do
  not survive** (p_adj >= 0.73), yet FINDINGS calls BM25 "clearly worse" there.
- Cross-cell pooled statements ("270 of 279 core lucky passes are UTM", "direction is right everywhere") treat
  records from the same question in 9 cells as independent. All public-benchmark lucky passes come from **5
  distinct questions** (HotpotQA 3, NQ 2; recomputed).
- UTM questions are clustered within source chunks: 150 questions come from 88 gold chunks, up to 3 per chunk.
  Boilerplate-ness is a chunk-level property, so the question-level bootstrap understates UTM variance somewhat.
- **Fix:** declare test families (e.g. the H2 main-rule tests as one family of 16, the secondary rule as another)
  and report Holm-adjusted p alongside raw p; drop "clearly" for NQ. Report pooled counts as distinct questions.
  Use a cluster bootstrap (resample chunks) for UTM rates, or at least note the design effect.

**W7. H2 "rises as retrieval weakens" is close to tautological under the unconditional rate; the conditional rate
is flat.**
- Weakening retrieval mechanically moves questions from "gold retrieved" to "no gold", so the unconditional lucky
  rate rises whenever P(correct | no gold) > 0. The behavioural question is whether that conditional rate changes.
  Recomputed for UTM, qwen2.5:7b hybrid: k = 1 41/89 (46%), k = 3 35/71 (49%), k = 5 23/53 (43%); BM25 37/73 (51%)
  vs hybrid 23/53 (43%). The +12.0 points (k) and +9.3 points (retriever) are almost entirely the change in
  opportunity. The `results.md` section 4 caveat about mechanical effects under the secondary rule applies, in a
  milder form, to the main rule too.
- **Fix:** decompose each H2 difference into an opportunity term and a conditional-accuracy term (or fit a
  logistic model of correct on hit_any x condition with question random effects), and state H2's result in those
  terms. Note that the conditional comparison is between non-identical question sets, so use a model rather than
  a naive two-sample test.

## Questions for the authors

1. What decision rule was pre-registered for "high" and "near zero" in H1? Without a threshold the H1 verdict can't
   be checked against the pre-registration. If "high" meant, say, >= 5%, the exact upper bound of 2.4% at n = 150
   would make the public-half null a *positive* finding about the overstatement, which is worth saying.
2. Were any reference labels in `audit/pilot_judge_check.csv` changed by Ali? Both judge-selection summaries report
   all 149 labels as Claude's.
3. Was the audit sample drawn with the stated stratification ("half lucky passes") from all cells, and will its
   estimates be reweighted to the population? How many UTM LLM-judged items will it contain?
4. Did any analysis decision after the full run (the UTM thresholds, which cells to report as "largest public-
   benchmark rates", the secondary rule's prominence) depend on seeing the results? A short "analysis decisions
   after unblinding" list would help.
5. What is the contains-match-only (judge-free) lucky-pass rate per cell? It bounds the judge's contribution
   directly.
6. Why is the HotpotQA "larger models know more closed-book" claim (FINDINGS H3: 23.3 vs 20.7) made without a
   test? Recomputed paired McNemar: 17 vs 13 discordant, p = 0.59 (NQ: 19 vs 6, p = 0.015, which does hold).

## Minor issues

- FINDINGS "Judges": the 6809/8750 = 77.8% overall agreement mixes a 25%-sampled stratum with a census stratum, so
  it isn't an estimate of anything. Either drop it or weight the contains-accept stratum by 4 (that gives roughly
  84%). The 26.0%/3.1% stratum rates are the right numbers to report, and `results.md` section 7 already says to
  compare rates.
- `lp/stats.py` uses the same seed for every cell, so cells with equal n share the same resample indices. Each
  interval is still valid, but their errors are correlated. That is harmless for reporting but should not be read
  as independent replications. `eval_judges.py` hard-codes `seed=13` instead of reading the config.
- `bootstrap_ratio_ci` silently drops resamples with zero denominator, which biases the `lucky_share_of_correct`
  interval upward when correct answers are rare. Report how many were dropped, or use a delta-method or
  Fieller-type interval.
- The secondary rule (hit_all) under k = 1 is mechanical, as noted. It is also partly mechanical at k = 5 for
  BM25 vs hybrid, because the retrievers differ in hit_all far more than in hit_any.
- Error analysis (30 items, Claude's categories): give exact CIs, e.g. judge error 6/30 = 20% [7.7, 38.6]. That
  is too wide to support "the judge accepts some incomplete answers" as anything more than an existence claim.
- The missing llama3.1:8b UTM call (n = 149) is plausibly not missing at random, since it was a long list answer.
  A two-line worst/best-case bound (count it as lucky / not lucky) would close this.
- `results.md` section 1 lists "largest public-benchmark rates" after looking at all 18 cells. Give the full range
  rather than the maximum, or flag the selection.
- "p <= 0.04" in FINDINGS is an odd summary of p values in {0.016, 0.016, 0.039}. Give the values.
- The hit_any "lower bound on lucky passes" wording in `method.md` is true only with respect to the rule choice.
  Gold incompleteness and judge false accepts bias the other way, as `limitations.md` already says, so qualify it
  in `method.md` too.

## Score

**3 / 5 (borderline).** The work is careful, transparent and reproducible, and the UTM gold-label finding is a
useful contribution. But the headline nulls are mostly a consequence of retrieval recall leaving 0-4 informative
questions per public cell. The degenerate bootstrap intervals hide this, and H3/H4 are untestable rather than
unsupported. The judge is validated on neither of the datasets that matter for the positive findings (UTM) or for
the null (NQ). Every issue can be fixed with the existing records: conditional rates with opportunity counts, exact
intervals, a judge-free contains-match sensitivity, an answer-containment reclassification, and Holm-adjusted p.
With those, I would move to 4.

**Confidence: 4 / 5.** I recomputed the key quantities from the released records. I did not re-run any model or
inspect individual UTM chunks beyond automated string matching.
