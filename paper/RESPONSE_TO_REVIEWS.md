# Response to the internal reviews (Phase 7)

Three reviewer passes were run as separate sub-agents on 2026-11-26. Each worked from the fact sheets, the code and
the results; there was no paper prose to review, because Ali writes every sentence. The reviews are in
`paper/reviews/`:

| Review | File | Score | Confidence |
|---|---|---|---|
| Sceptical NLP | `review_nlp.md` | 2/5 | 4/5 |
| Statistics | `review_stats.md` | 3/5 | 4/5 |
| Busy practitioner | `review_practitioner.md` | 2/5 | 4/5 |

**What happened overall.** The three reviews agree on the main point, and it is right: the public-benchmark null is
mostly a *no-opportunity* result. Retrieval rarely misses every gold passage, so a lucky pass rarely has a chance to
happen. When retrieval does miss, a correct answer is not rare.

Every fix that could be made from the existing records was made. No model was run. Fixes that need new runs, or that
are Ali's to decide (framing, prose, a new UTM question set), are listed at the end and in NEEDS_ALI.md item F.

**Where the fixes live:**
- branch `phase-5-analysis`, PR #7:
  - `scripts/extra_analyses.py` → `results/extra_analyses.json`;
  - `lp/stats.py`;
  - `scripts/compare_conditions.py`;
  - `scripts/utm_sensitivity.py`;
  - `results/FINDINGS.md`;
  - `README.md`;
- branch `phase-6-paper`, PR #6: the fact sheets.

**Labels:**
- **Fixed:** changed in the code, the results or the fact sheets.
- **Ali:** a writing or framing decision, or something only Ali can do.
- **Run:** needs new model runs, which need Ali's OK.
- **Not changed:** with the reason.

## Shared points (raised by two or three reviewers)

| Point | Raised by | Response |
|---|---|---|
| The public null comes from no opportunity: misses are rare, and a correct answer after a miss is not rare. | NLP W2; Stats W1; Practitioner W1 | **Fixed.** `extra_analyses.json` gives, per cell, the number of questions with no gold retrieved and the accuracy given a miss, with exact intervals. Pooled: HotpotQA 11.1% of 45 miss records, NQ 7.0% of 57. FINDINGS' headline now says this. Results fact sheet §1b. |
| The [0.0, 0.0] intervals are wrong at 0. | NLP W9; Stats W2; Practitioner minor | **Fixed.** `stats.clopper_pearson` gives exact intervals for every lucky-pass and memory-lucky rate: 0/150 → [0.0, 2.4], 0/48 → [0.0, 7.4]. FINDINGS and the fact sheets use them. The pre-registered bootstrap stays in `summary.json` and is labelled as such. **Ali:** the generated tables still show the bootstrap; choose which interval the paper reports. |
| H2 is mostly mechanical. | NLP W1; Stats W7 | **Fixed.** UTM accuracy given a miss is flat across k: 46.1% (n = 89), 49.3% (n = 71), 43.4% (n = 53). FINDINGS and fact sheet §4 now say H2's rise is "more misses, not more luck per miss". |
| The invented control is vacuous: it had 0 misses under dense and hybrid. | NLP W2; Stats W1; Practitioner W5 | **Fixed** in FINDINGS and Limitations ("can't test H1"). **Run:** a forced-miss control (remove the gold passage from the invented corpus) would make it informative. |
| H4 can't be tested: 12 cells are really 4 datasets, with 9 tied zeros. | NLP W8; Stats W5 | **Fixed.** The verdict is now "not testable here". |
| The judges aren't validated on NQ or UTM, and their errors run in opposite directions. | NLP W6; Stats W3 | **Fixed** in Limitations and fact sheet §7: the 16.0% false-accept and 17.4% false-reject profiles, and the selection items covering HotpotQA and invented only. A judge-free (contains-only) rate was added: UTM still has 8.0–19.5%, so the judge isn't the main driver. **Ali:** the audit (item E) has 29 UTM and 16 NQ items and is the real check. **Run:** re-judging every generator with one judge would remove the confound. |
| The UTM sensitivity analysis used a threshold chosen after seeing the data. | NLP minor; Stats W4 | **Fixed.** It now uses whole-word matching and sweeps thresholds 2–20 (the conclusion holds). A threshold-free rule was added: a lucky pass whose retrieved context contains the answer. That leaves 2.7–6.0% on UTM. |
| The artifact came from the author's own tool, and the tool is unevaluated. | NLP W10; Practitioner W3 | **Partly.** FINDINGS says plainly that the UTM questions came from ragaudit's single-chunk pipeline, and gives the fix. **Ali:** whether ragaudit stays a contribution, and whether to change it (every answer-containing chunk marked as gold; reject boilerplate and underspecified questions). |
| The framing doesn't fit the results; the one-sentence takeaway is unclear. | Practitioner W1; NLP W5 | **Ali.** It's a framing decision. Fact sheet guiding questions and NEEDS_ALI item F give the candidate takeaway: "with good retrieval, answer-only scores barely overstate retrieval, and apparent overstatement is mostly incomplete gold labels; when retrieval misses, models still answer 7–11% right." |

## Sceptical NLP review (`review_nlp.md`)

| # | Point | Response |
|---|---|---|
| W1 | H2 is close to a tautology. | Fixed (see the shared table). |
| W2 | The public null is built into the design: easy NQ pool, HotpotQA names an entity. | Fixed in Limitations (new "Design" section). **Run:** NQ on the full BEIR corpus, or hard negatives. |
| W3 | Jonah et al. use a different denominator. | **Fixed.** Accuracy given not-all-gold on HotpotQA is 17.9–44.6% (n = 54–92). Fact sheet §1b says it *partly reproduces* their result. **Ali:** the related-work wording. |
| W4 | Passage IDs vs attribution. | **Fixed:** a DPR-style answer-in-context rule is now reported for every cell. Karpukhin et al. 2020, Rashkin et al. (AIS) and Gao et al. (ALCE) were added to the verified references, with notes in `related_work_notes.md`. **Ali:** whether to rename "lucky pass" or add "unlabelled-gold pass". |
| W5 | The memory/guess split rests on about 9 public lucky passes. | Agreed; it is now stated in FINDINGS (H3 "not testable"). **Ali:** drop it as a headline contribution. |
| W6 | Judging error and asymmetry. | Fixed in the text (see the shared table); the audit is pending. |
| W7 | qwen wrote the UTM questions (18.0% vs 1.3–3.4% closed-book); the too-lexical filter applies only to generated sets. | Fixed in Limitations, with the number. **Run:** questions from a third model family would remove it. |
| W8 | H4 can't be tested. | Fixed. |
| W9 | Intervals at 0. | Fixed. |
| W10 | The tool is unevaluated. | Ali (see the shared table). |
| Q1 | Accuracy given no gold, per cell and k. | Fixed: `extra_analyses.json`, `core` and `ksweep`. |
| Q2 | Harder pools. | Run (item F). |
| Q3 | The answer-containment rule. | Fixed. |
| Q4 | Which HotpotQA gold paragraph holds the answer span. | **Not changed.** It needs per-paragraph span matching, and the secondary rule is already labelled weak evidence. A cheap follow-up if Ali wants it. |
| Q5 | Why hit_any as the main rule. | Pre-registered before the full run. Method now says it is *not* a lower bound on true lucky passes. |
| Q6 | Where the pre-registration is timestamped. | `research-design/research-progress.md`, which is outside the repo. **Ali:** copy the dated decisions into the repo or an appendix before submission. |
| Q7 | Same-judge closed-book gap. | Run (re-judging). |
| Q8 | What the audit measures. | Judge correctness only. Whether a lucky pass was grounded is measured by the answer-in-context rule. |
| Q9 | A "passages only" prompt. | Not tried. It is in Limitations; Run (item F). |
| Minor | Fact-sheet table pointer | Fixed. |
| Minor | Substring matching | Fixed: whole words now. |
| Minor | "Lower bound" wording | Fixed in Method. |
| Minor | NQ join coverage | Fixed: 2255/3452, now tagged in Method. |
| Minor | Missing related work | Fixed: 6 references verified and added (`citations_verified.md` rows 28–33). |
| Minor | The hedged-list `clean_answer` concern | Not changed (no evidence of it yet). The audit will show it. |

## Statistics review (`review_stats.md`)

| # | Point | Response |
|---|---|---|
| W1 | No-opportunity nulls. | Fixed (see the shared table). |
| W2 | Degenerate intervals. | Fixed. |
| W3 | Judge validity. | Fixed in the text; audit pending; Run. |
| W4 | Post-hoc threshold. | Fixed: a threshold sweep plus a threshold-free rule. "Analysis decisions after seeing the results" are now listed in FINDINGS and the fact sheet. |
| W5 | H4 | Fixed. |
| W6 | Multiple comparisons and clustering. | **Fixed for multiplicity.** Holm over all 60 McNemar tests (`p_holm`). UTM k = 1 vs 5 survives (Holm p = 0.007). UTM BM25 vs hybrid survives only for llama3.2:3b. The NQ secondary-rule effects don't survive. **Not changed for clustering:** every test is paired within one model and question set, and pooled "accuracy given a miss" is now labelled as counting records, not questions. A mixed model is overkill at these counts. |
| W7 | H2 tautology. | Fixed. |
| Q1 | A threshold for "high" | None was pre-registered. FINDINGS says so, and says the 4.7% upper bound rules out any reading where 5% is low. |
| Q2 | Did Ali edit the reference labels? | No. FINDINGS now says "Ali edited none". |
| Q3 | Audit stratification and weighting. | The audit has 25 lucky passes and 25 others, from the core run (29 UTM, 16 NQ, 5 HotpotQA). The accuracy will be reported per stratum, not reweighted. |
| Q4 | Post-hoc decisions. | Listed. |
| Q5 | Judge-free rate. | Fixed: `lucky_contains_only_exact`. |
| Q6 | Untested closed-book claim. | Fixed: NQ p = 0.015, HotpotQA p = 0.58. FINDINGS now claims only NQ. |
| Minor | Overall 77.8% agreement | Fixed: dropped as an estimate; the stratum rates are used. |
| Minor | Missing call bounds | Fixed: 24.7–25.3%, with nothing changing. |
| Minor | Error-sample intervals | Fixed: judge error 20.0% [7.7, 38.6], read as an existence claim. |
| Minor | "p ≤ 0.04" | Fixed: exact values given. |
| Minor | "Largest rates" selection | Fixed: FINDINGS gives the full range, 0.0–1.3%. |
| Minor | Shared bootstrap seed across cells | Not changed. Each interval is valid, and the seed is fixed for reproducibility, as documented. |
| Minor | Ratio interval drops zero denominators | Not changed. `lucky_share_of_correct` isn't used in any claim. |
| Minor | eval_judges seed | Not changed. It equals the config seed (13); a later tidy-up. |

## Busy practitioner review (`review_practitioner.md`)

| # | Point | Response |
|---|---|---|
| W1 | Framing and takeaway. | Ali (candidate sentence in the shared table). |
| W2 | UTM rests on one corpus, post hoc, with LLM labels. | Agreed, and now stated: post hoc, Claude's categories, exact intervals. The threshold-free rule doesn't rely on labels. Audit pending. **Run:** a second real corpus would make it general. |
| W3 | The author's tool made the artifact. | See the shared table. |
| W4 | No detection recipe. | **Fixed:** the README has a 4-step "Checking your own RAG app" section: bound by misses, count, check gold labels by answer-in-context, closed-book on the rest. |
| W5 | Invented control, and the qwen-wrote-UTM signal. | Fixed in Limitations (both). |
| W6 | Figures: zeros invisible, UTM bars dominate. | **Partly fixed:** zero bars are now labelled "0". **Ali:** captions and which figures to use. Showing "accuracy given a miss" instead of the raw rate would answer the dominance point; a figure for it can be generated if wanted. |
| W7 | Stale README. | **Fixed:** real results; the "score drops on private documents" claim removed; the recipe added; `LP_UTM_CORPUS` documented for your own corpus. |
| W8 | Narrow model range. | Already in Limitations. Not changed. |
| Q1 | One sentence | Ali. |
| Q2 | ragaudit changed? | Not yet. Ali. |
| Q3 | Audit split | Will be reported per stratum. |
| Q4 | Does qwen's 18% come from the boilerplate questions? | **Checked (ad hoc, from the core records, hybrid cells):** partly. 15 of qwen2.5:7b's 27 closed-book hits on UTM are boilerplate-answer questions (≥ 10 chunks), but 12 aren't, against 2 or fewer for each llama model (llama3.1:8b 5 hits, 3 boilerplate; llama3.2:3b 2 hits, 0 boilerplate). So qwen still does better on its own questions. These counts aren't in a results file; add them to `extra_analyses.py` before citing them. |
| Q5 | Isn't the secondary rule the real finding? | Agreed it's the larger gap. Reported, with the "half the evidence" caveat. Ali decides the emphasis. |
| Q6 | Answer-in-context instead of gold labels | Fixed (reported for every cell). |
| Q7 | Passages-only prompt | Run. |
| Minor | Table display names | Fixed. |
| Minor | Fact-sheet table pointer | Fixed. |
| Minor | [0, 0] intervals | Fixed (exact). |
| Minor | Hard-coded figure titles | Ali (captions). |
| Minor | "Lucky" naming | Ali. |
| Minor | Agreement direction | Fixed. |

## Not done here, and why

These need Ali's OK, because they are new model runs; the pre-approval covered only core and the k-sweep:
- **a forced-miss invented control**: remove each question's gold passage, about 48 questions × 3 models;
- **NQ with the full BEIR corpus** or hard negatives;
- **a "passages only" prompt** on a subset;
- **re-judging all generators with one judge**;
- **a regenerated UTM question set** with every answer-containing chunk marked as gold, and boilerplate or
  underspecified questions rejected.

They are listed with rough costs in NEEDS_ALI.md item F.

These are writing decisions that only Ali can make:
- the framing;
- the one-sentence takeaway;
- whether the tool stays a contribution;
- captions;
- naming;
- which interval the paper reports;
- the related-work wording.
