# Review: "Lucky passes" in small local RAG (fact-sheet submission, branch phase-6-paper)

Reviewer angle: NLP methodology, evaluation / RAG track. I reviewed the framing and novelty notes, the four fact
sheets, `results/FINDINGS.md`, the code they depend on, and the committed results. Unless I say otherwise, the numbers
below are from `results/core/summary.json`, `results/ksweep/summary.json`, `results/core/records.jsonl` and
`results/comparisons.json`. A few are my own arithmetic on those files, and I label those.

## Summary

The submission sorts each RAG answer by two things: is it correct, and was a gold passage in the top k? A
"lucky pass" is a correct answer with no gold passage retrieved. Lucky passes are split again by whether the same
model also answers correctly closed-book ("memory lucky") or not ("guess lucky"). The setup is 3 local generators
(llama3.2:3b, qwen2.5:7b, llama3.1:8b), 3 retrievers (BM25, dense, hybrid RRF) at k = 5, plus a k-sweep (k = 1, 3, 5)
for one model. There are four datasets: HotpotQA (150 questions, pool of 66,581 distractor-setting paragraphs), NQ
(150 questions, gold passages plus 20,000 random BEIR passages), a 38-chunk invented corpus (48 generated questions)
and a 125-chunk university calendar, "UTM" (150 generated questions). Correctness is decided by contains-match plus
other-family LLM judges.

The four pre-registered hypotheses come out as follows. H1 (lucky passes high on public data, ~0 on the invented
corpus) is reported as not supported: 0–1.3% on HotpotQA and NQ. H2 (lucky passes rise as retrieval weakens) is
"mixed", with a large effect only on UTM. H3 (larger models have more memory-lucky passes) and H4 (closed-book
accuracy predicts the lucky-pass rate) are not supported. A post-hoc analysis traces most UTM lucky passes to
boilerplate answers and under-specified generated questions. The authors now pitch the work (FRAMING.md) as a
replication of Jonah et al. (2026) plus the memory/guess split, H2–H4 and an open tool.

The write-up is unusually honest about its negative results, and the engineering is careful. My concern is that
the construct and the design decide the headline numbers more than the phenomenon does. The negative public-data
result and the positive UTM result are both largely artifacts of how "retrieved gold" was operationalised.

## Strengths

- **Transparency.** Pre-registered rules are kept and reported even when they go against the hypotheses. Post-hoc
  analyses are labelled as post-hoc (`results/FINDINGS.md`, the UTM section). The limitations fact sheet states which
  way each bias goes. The failed pilot sanity gate is disclosed (`limitations.md`, "The pilot sanity gate failed").
- **Reproducibility.** Results are cached and deterministic, data revisions are pinned, a fresh-clone rerun matched
  field by field, and every number in the fact sheets is checked by `scripts/check_factsheets.py`. Per-question
  records are released, which is what made the re-analyses below possible.
- **Reasonable design hygiene.** Judges come from a different family than the generator. The question generator
  and verifier also come from different families. Yes/no HotpotQA questions are removed. Comparisons are paired
  (bootstrap + exact McNemar). The novelty note openly concedes that H1 is not new.
- **A useful negative lesson.** "A lucky-pass count is only as good as the gold labels" is correct and practically
  relevant, and the UTM case shows it concretely.

## Weaknesses

1. **H2 is close to a tautology. On the one dataset where it "holds", the effect is entirely mechanical.**
   `lucky_pass = correct ∧ ¬hit@k`. Raising k turns misses into hits, so the unconditional lucky-pass rate has to
   fall unless accuracy among the remaining misses rises. The informative quantity is the conditional rate
   P(correct | no gold in top k). I computed it from `results/ksweep/summary.json` (lucky_pass × n / misses, my
   arithmetic). For UTM it is flat: 46.1% at k = 1 (89 misses), 49.3% at k = 3 (71), 43.4% at k = 5 (53). The
   headline "UTM: +12.0 [6.7, 18.0], p = 0.0001" (`results.md` §4) only says that k = 5 retrieves more gold chunks
   than k = 1. The same holds for BM25 vs hybrid: UTM any-gold hit@5 is 51.3% vs 64.7%, while the conditional
   accuracy is 50.7% vs 43.4%. H2 as stated cannot fail for this reason, so the McNemar p-values are not evidence
   about memory or luck. Please restate H2 on the conditional rate, or on a decomposition that separates "fewer
   misses" from "more correct answers among the misses".

2. **The pre-registered measure, together with corpus construction, guarantees the public-benchmark null (H1).**
   Any-gold hit@5 under hybrid retrieval is 99.3% on HotpotQA and 97.3% on NQ (`results.md` §1). That leaves 1 and 4
   of 150 questions that *could* be lucky. The rate is then bounded by about 0.7% and 2.7% whatever the models know.
   Two design choices produce the high hit rates:
   - NQ uses 20k *random* distractors (`lp/datasets.py`, `load_nq`) instead of the 2.68M-passage BEIR corpus, which
     removes almost all hard negatives and same-article passages.
   - HotpotQA's pool is the 66k distractor-setting paragraphs rather than full Wikipedia, and each passage is indexed
     with its title (`Passage.as_text`), while HotpotQA questions usually name at least one gold title.

   So "answer-only scores barely overstate retrieval on public benchmarks" (FINDINGS headline) is really a statement
   about near-saturated toy retrieval. It does not show that the phenomenon is small. The invented control has the
   same problem, worse: hit@5 is 100% under dense and hybrid (0 misses), and under BM25 there is 1 miss in 48. The
   "0.0 in all 9 cells" therefore cannot distinguish H1 from its negation. A control has to have misses to be a
   control.

3. **The comparison with Jonah et al. uses a different denominator. Measured on their terms, the data partly
   *replicate* their result rather than contradict it.**
   - NOVELTY.md says Jonah et al.'s 0.35–0.71 "is our 2×2 table's lucky pass cell". It is not. Theirs is accuracy
     *conditional on incomplete evidence* (not every gold item retrieved), which corresponds to the hit_all rule
     here and is conditional rather than unconditional.
   - Computed that way from `results/core/summary.json` (lucky_pass_all × n / (n − hit_all·n), my arithmetic),
     HotpotQA gives 18–45% across the 9 cells, e.g. qwen2.5:7b 40.2% (BM25), 44.6% (dense), 31.5% (hybrid). That sits
     at or just below the lower end of their range, with weaker models and k = 5.
   - The paper should report this conditional quantity as the like-for-like replication. It should also drop the
     framing that H1 failed on public data, which comes from comparing two different measures.

   The hit_all rule has a construct problem of its own. Min et al. (2019, "Compositional questions do not
   necessitate multi-hop reasoning") showed that many HotpotQA questions are answerable from one paragraph, so
   "correct with one of two gold paragraphs" is often grounded, not lucky. Neither rule tells you whether the
   *answer-bearing* paragraph was retrieved, and that is the variable the construct needs.

4. **The construct is defined by passage IDs, but the question it answers is about attribution.** "Lucky"
   assumes that no gold ID in the context means the answer did not come from the context. On UTM that assumption
   fails for most cases: 234 of 270 lucky records are boilerplate-answer questions (`utm_sensitivity.json`), and in
   the 30-item error sample 22 of 30 are "bad question" or "answer in a non-gold retrieved chunk" (`error_sample.csv`).
   The standard fix has existed since DPR (Karpukhin et al., 2020, not cited): count a hit when a retrieved passage
   *contains the answer string*. Attribution/AIS-style checks (Rashkin et al.; ALCE, Gao et al. 2023) and
   counterfactual removal tests do the same job more carefully. The records already contain everything needed to
   recompute every cell under an "answer-in-context" rule for all four datasets, NQ included, since BEIR-NQ qrels
   are known to be sparse. Without that, the UTM "methods finding" is a rediscovery of a known evaluation pitfall,
   reported post hoc on one dataset.

   The overstatement measure (accuracy − true-pass rate) has the mirror-image problem. It treats every
   correct-with-gold answer as retrieval-attributable, even though the closed-book run shows the model often knew
   it (NQ closed-book accuracy is 34–43%). The released closed-book and oracle conditions would support a more
   direct attribution measure, e.g. correct_RAG ∧ ¬correct_closed. Please report it.

5. **The memory/guess split, the claimed main novelty (FRAMING.md, contribution 1), has almost no data
   behind it and its "guess" label is mislabelled.**
   - On HotpotQA and NQ there are 9 lucky-pass records in total, across 18 cells × 150 questions (8 memory,
     1 guess; `records.jsonl`). On UTM, 250 of 270 are "guess lucky".
   - The error analysis shows "guess" is a residual bin, dominated by label artifacts and judge errors. Only 1 of 30
     sampled lucky passes was a real guess.
   - "Memory lucky" is also only co-occurrence: a correct closed-book answer does not show that the RAG answer came
     from memory rather than from a non-gold passage.

   As measured, the split cannot support a claim. It needs (a) an answer-in-context category before it, and (b)
   enough misses to estimate anything, which brings us back to Weakness 2.

6. **Judging is a material and asymmetric source of error, and it is not yet validated by humans.**
   - The judges were chosen and scored on the same 144 items, labelled by Claude Opus rather than humans
     (`method.md`, "How the judges were chosen").
   - The judge pair used for the qwen generators has a false-accept rate of 16.0% [8.0, 25.3]. That error lands
     disproportionately on the lucky-pass cell, because no-gold answers are the ones most likely to need the LLM.
   - Rough arithmetic (mine): on UTM qwen/hybrid there are 53 no-gold questions and 23 lucky passes. A 16%
     false-accept rate on the roughly 30–35 truly wrong answers would add 5 or so spurious lucky passes, about a
     third of the reported 15.3%.
   - The LLM judge also accepts 26.0% of answers that contains-match rejects (FINDINGS, "Judges").
   - Cross-model comparisons are confounded by the judging setup. qwen answers need *two* judges to agree with prompt
     v2. llama answers need *one* judge, with prompt v3 (`lp/config.py`, `judges` / `judge_prompt_by_family`). H3
     compares within the llama family, so it is not affected. Every qwen-vs-llama contrast in the tables is.
   - The planned audit (`audit/audit_sheet.csv`) shows the labeller the `llm_judge` verdict and `gold_retrieved`.
     That anchors the "unbiased" estimate. Please hide those columns.

7. **The generated datasets are confounded with one of the systems under test, and with the retriever.**
   - qwen2.5:7b wrote the UTM and invented questions and is also a generator under test. On UTM its closed-book
     accuracy is 18.0%, against 3.4% for llama3.1:8b and 1.3% for llama3.2:3b. That is a 5–14× gap on a niche
     corpus, which looks more like question-style affinity (or the judge asymmetry above) than memory.
   - llama3.1:8b is at once the question verifier, a generator and a judge.
   - The "too lexical" filter (`limitations.md`; 34 and 59 rejections) removes high-overlap questions only for the
     generated datasets. That makes BM25 artificially weak there (UTM BM25 hit@5 is 51%), while HotpotQA and NQ keep
     their natural overlap. So dataset (public vs generated) is confounded with question-construction and retrieval
     difficulty, which undercuts the H1 contrast and H4.
   - The verifier passed questions that name no course (11 of 30 error-sample items).

8. **H4 is not testable as designed.** The analysis uses 12 cells, but they are 4 datasets × 3 models, so the
   effective n is 4. The permutation test treats the cells as exchangeable. Lucky passes are identically 0 in 9 of
   the 12 cells (`results.md` §6). The analysis should be dropped or presented as descriptive only.

9. **The intervals for zero counts are wrong.** The percentile bootstrap gives "0.0 [0.0, 0.0]" for 0/150 and 0/48
   (`results.md` §1, FINDINGS table), which states certainty the data do not have. Exact (Clopper–Pearson) upper
   bounds are about 2.4% for n = 150 and about 7.4% for n = 48. For the invented control, that bound is above the
   pre-registered 5% bar. Use Wilson or exact intervals for binomial rates near the boundaries. There is also no
   correction for multiple comparisons across the 24 + 4 + 4 paired tests in `comparisons.json`.

10. **The tool contribution is unevaluated, and the paper's own results argue against it.** "ragaudit" is listed as
    a contribution (FRAMING.md, item 3; NOVELTY.md table), but it is not evaluated anywhere. Worse, UTM was built
    with ragaudit's own question pipeline and single-source-chunk gold labelling (`lp/datasets.py`,
    `generate_questions_for_chunks` / `load_generated`), and the paper attributes most UTM lucky passes to exactly
    that pipeline. As it stands, the evidence says the tool produces false lucky-pass flags on real documents. If
    the tool is a contribution, it needs a precision/recall evaluation of its flags against human-verified
    attribution.

## Questions for the authors

1. What is P(correct | no gold in top k), with exact CIs, for every cell and every k? Does any H2 effect survive
   when stated on that quantity?
2. If NQ used the full BEIR corpus (or at least hard negatives from the same Wikipedia articles), and HotpotQA used
   the full-wiki setting without titles in the indexed text, how many misses would there be, and what would the
   lucky-pass rate be?
3. Can you recompute all cells with a "retrieved passage contains a normalised gold answer" hit rule (DPR-style)
   next to hit_any and hit_all? How many lucky passes remain on each dataset, and what share of the 279 is then
   memory vs guess?
4. For the HotpotQA hit_all analysis, what happens if you mark which gold paragraph contains the answer span and
   condition on that paragraph being retrieved?
5. Why was hit_any chosen as the main rule when the stated prior work (Jonah et al.) uses evidence completeness? Was
   the near-100% any-gold hit rate known from the pilot before the full run was pre-registered?
6. Where is the pre-registration timestamped? `research-design/research-progress.md` lives outside the repository
   (`lp/config.py`, `Paths.research_dir`). Several rules (judge prompt v3 per family, the full HotpotQA pool) changed
   after the pilot.
7. How large is the qwen-vs-llama gap in UTM closed-book accuracy when all generators are judged by the *same*
   judge and prompt? Can you re-judge closed-book answers with a single fixed judge to separate judge strictness
   from question-generator affinity?
8. What do the 50 audit items measure: judge correctness only, or also whether a lucky pass was grounded in a
   non-gold passage? The second is the construct-validity question that matters here.
9. Was a strict "passages only" prompt tried on any subset? Without it, memory-lucky and true-pass-from-memory
   cannot be told apart.

## Minor issues

- `results.md` §1 points to `paper/tables/core/main_table.tex`, while the latest commit names
  `headline_hybrid_k5.tex` as the main table. Pick one.
- `scripts/utm_sensitivity.py`, `answer_frequency`: `normalize(a) in t` is a raw substring test, not whole-word, so
  short answers ("Science", "36") over-count. It also counts occurrences in the whole corpus, not in the *retrieved*
  chunks of each record, which is the relevant test.
- `lp/generate.py`, `clean_answer`: keeps the first line and truncates to 300 characters, and `contains_match` then
  accepts any answer that mentions the gold. A hedged list ("Science or Social Science") passes. Report how many
  correct answers contain more than one candidate.
- "Lower bound" (`lp/classify.py` docstring, `method.md`) is only true relative to hit_all. Incomplete gold labels
  push the other way, so hit_any is not a lower bound on the true construct. State this precisely.
- The UTM boilerplate threshold (10 chunks) was chosen post hoc. Showing the full curve across thresholds would be
  more convincing than two points.
- NQ answers come from NQ-open joined on normalised question text, and only 2,255 of 3,452 BEIR queries matched.
  Say whether that join biases the sample, e.g. towards shorter questions.
- The citation of Jonah et al. rests on the abstract plus the sections read. Confirm their HotpotQA corpus setting
  (per-question distractors vs pooled) before claiming a "new setting".
- Missing related work: Karpukhin et al. 2020 (DPR, answer-containment retrieval accuracy); Min et al. 2019
  (single-hop solvability of HotpotQA); Chen et al. 2017 (DrQA distant supervision); work on sparse/incomplete
  qrels (e.g. Arabzadeh et al. 2022); attribution evaluation (Rashkin et al. AIS; Gao et al. 2023 ALCE); Kandpal et
  al. 2023 (long-tail knowledge and memorisation).

## Score

**2 / 5 (weak reject for a workshop in its current form).**

The engineering, the transparency and the honest reporting of nulls are commendable. But the central quantities
are not measured in a way that supports the claims. The public-data null is guaranteed by near-saturated retrieval
and a near-empty control. H2's significant result is mechanical. The novel memory/guess split rests on 9 public
lucky passes and a mislabelled residual. The like-for-like comparison with Jonah et al. is not made, and when it is
made it partly agrees with them.

Most of the fixes need no new model inference, because they are re-analyses of the released records: conditional
rates, an answer-in-context hit rule, exact intervals, and same-judge re-judging. If those were done, the human
audit completed blind, and a harder retrieval setting run for NQ/HotpotQA, this could become a solid short paper on
how gold-label choices make "unattributed accuracy" estimates swing. That framing is honest, and I think it is more
novel than the current one.

**Confidence: 4 / 5.** I checked the key numbers against the released files and the code paths for classification,
judging, retrieval and dataset construction. I have not read Jonah et al. in full.
