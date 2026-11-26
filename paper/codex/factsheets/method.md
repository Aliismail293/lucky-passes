# Fact sheet: Research Methodology

These are notes for Ali, who writes every sentence of the paper; this file is not paper text. Each number carries a
source tag. `uv run python scripts/check_factsheets.py` resolves every tag and fails if a number doesn't match its
source.

- Counts of things in the design (3 generators, 3 retrievers, 4 datasets) come from the configs and aren't tagged:
  `configs/core.yaml`, `configs/ksweep.yaml`.
- Every decision below has its reason and date in `research-design/research-progress.md`.

## What is measured
- **Outcome classes.** Each (question, generator, retriever, k) gets two binary facts: is the answer correct, and
  is a gold passage in the top k (hit@k). Crossing them gives four classes:
  - **true pass:** correct, gold retrieved;
  - **grounding failure:** wrong, gold retrieved;
  - **lucky pass:** correct, no gold retrieved;
  - **miss:** wrong, no gold retrieved.
- **The measure.** How much an answer-only score overstates retrieval: accuracy − true-pass rate = the lucky-pass
  rate.
- **Main rule (pre-registered): hit_any.** A question counts as retrieved if *any* gold passage is in the top k.
  - *Why:* it's the stricter of the two rules, so it counts fewer lucky passes than hit_all, and it was fixed
    before the full run.
  - It is **not** a lower bound on true lucky passes. Incomplete gold labels and judge false accepts push the
    other way (see Limitations, and the answer-in-context check in the results fact sheet).
- **Secondary rule: hit_all.** A question counts as retrieved only if *every* gold passage is in the top k. This
  only matters for multi-hop HotpotQA.
  - Every pilot HotpotQA question has 2 gold paragraphs: computed from `results/pilot/records.jsonl` (100 of 100
    questions). That file has no single field to tag.
- **Memory lucky vs guess lucky.** Each question is also answered **closed-book** (no passages) and **oracle** (gold
  passages only).
  - A lucky pass whose closed-book answer is also correct is *memory lucky*; otherwise it is *guess lucky*.
  - *Why:* this separates "the model knew it" from "the other passages or chance produced it".
  - The oracle condition is the ceiling, and it flags questions whose gold answer may be wrong.

## Datasets
Every dataset uses n = 150 questions in core; the invented corpus uses all it has.
- Sources: `configs/core.yaml` sets n = 150 `[src: configs/core.yaml#datasets/0/n]`.
- Sampling uses a fixed seed, 13 `[src: configs/core.yaml#seed]`.

**HotpotQA, distractor dev split (multi-hop).**
- The split has 7405 questions `[src: results/pilot/summary.json#meta/datasets/hotpotqa/available]`.
- 6947 remain after yes/no questions are dropped `[src: results/pilot/summary.json#meta/datasets/hotpotqa/after_yes_no_filter]`.
  - *Why drop yes/no:* a coin flip answers half of them, which would inflate guess-lucky passes.
- **Passage pool:** every paragraph of every dev question, deduplicated by title, 66581 passages
  `[src: results/pilot/summary.json#meta/datasets/hotpotqa/corpus_passages]`.
  - 63 titles had clashing texts; the first text seen is kept
    `[src: results/pilot/summary.json#meta/datasets/hotpotqa/corpus_title_text_clashes]`.
  - *Why the full pool:* the first pilot used only each question's own 10 paragraphs. Retrieval then always found
    gold (hit@5 = 100%), so lucky passes couldn't happen; the full pool fixed that (rerun 1, pre-registered).

**Natural Questions.**
- Questions and gold passages come from BEIR `nq`, joined on normalised question text with NQ-open short answers.
  - 2255 of 3452 BEIR queries matched `[src: results/core/summary.json#meta/datasets/nq/matched_to_nq_open]`.
  - Whether the join favours some question types wasn't checked.
- **Corpus:** every gold passage, plus a fixed-seed reservoir sample of 20000 distractors
  `[src: lp/config.py#nq_distractors]`.
- The BEIR files are pinned to Hugging Face revisions (`scripts/download_data.py`).

**Invented corpus (control).**
- Documents about a fictional coastal survey office that no model can have seen; the corpus is the bundled demo of
  Ali's tool (anonymised in the paper as `\toolname`).
- 38 chunks `[src: results/pilot/summary.json#meta/datasets/invented/chunks]` gave 48 verified questions
  `[src: results/pilot/summary.json#meta/datasets/invented/verified_questions]`.
- **Rejected questions, by reason:**
  - too lexical: 34 `[src: results/pilot/summary.json#meta/datasets/invented/rejected/too_lexical]`;
  - ambiguous: 8 `[src: results/pilot/summary.json#meta/datasets/invented/rejected/ambiguous]`;
  - unsupported: 6 `[src: results/pilot/summary.json#meta/datasets/invented/rejected/unsupported]`;
  - unanswerable: 4 `[src: results/pilot/summary.json#meta/datasets/invented/rejected/unanswerable]`;
  - relative time: 2 `[src: results/pilot/summary.json#meta/datasets/invented/rejected/relative_time]`;
  - verifier output unparseable: 1 `[src: results/pilot/summary.json#meta/datasets/invented/rejected/verifier_unparseable]`.
- *Why:* if lucky passes come from memory, an unseen corpus should show almost none. That is H1's control.

**UTM calendar.**
- Public UTM course-calendar pages; real and niche, so only partly memorised.
- Questions are generated and verified the same way as for the invented corpus.
- 125 chunks `[src: results/core/summary.json#meta/datasets/utm/chunks]` gave 150 verified questions
  `[src: results/core/summary.json#meta/datasets/utm/verified_questions]`.
- **Rejected questions, by reason:**
  - too lexical: 59 `[src: results/core/summary.json#meta/datasets/utm/rejected/too_lexical]`;
  - unsupported: 19 `[src: results/core/summary.json#meta/datasets/utm/rejected/unsupported]`;
  - ambiguous: 10 `[src: results/core/summary.json#meta/datasets/utm/rejected/ambiguous]`;
  - unanswerable: 2 `[src: results/core/summary.json#meta/datasets/utm/rejected/unanswerable]`.
- **Found after the run:** the verifier passed questions that name no course ("How is the course delivered?") and
  questions with boilerplate answers. See the results fact sheet, section 3.

**Question generation (invented and UTM).**
- Generator: qwen2.5:7b. Verifier: llama3.1:8b, from a different family (`lp/config.py`, `question_generator` and
  `question_verifier`).
- *Why a different family:* a verifier from the same family shares the generator's blind spots.

## Models and decoding
- **Generators:** qwen2.5:7b, llama3.1:8b and llama3.2:3b, run locally in Ollama.
- **Decoding:** temperature 0, seed 13; context window 4096 tokens `[src: lp/config.py#num_ctx]`.
- **Prompt:** asks for a short answer and, in the RAG and oracle conditions, to use the passages.
  - It does **not** forbid answering from memory.
  - *Why:* a typical application prompt doesn't forbid it either.

## Retrieval
- **BM25** (k1 = 1.5, b = 0.75, `lp/retrieve.py`).
- **Dense:** nomic-embed-text, with its "search_query: " and "search_document: " prefixes.
- **Hybrid:** reciprocal rank fusion of the BM25 and dense rankings, with constant k = 60 `[src: lp/retrieve.py#RRF_K]`.
  - Each ranking is fused to depth max(10 × depth, 50).
  - Retrieval depth is 10 `[src: lp/config.py#retrieval_depth]`; the top k is then taken.
- Retrieval doesn't depend on the generator, so it runs once per dataset and is cached.
- **Core grid:** all 3 retrievers × all 3 generators at k = 5 (`configs/core.yaml`).
- **k-sweep:** hybrid retrieval, qwen2.5:7b only, k ∈ {1, 3, 5} (`configs/ksweep.yaml`).
  - Ali's runtime rule would have cut it to {1, 5} if core plus the k-sweep had exceeded 40 h. The check at 300
    pairs estimated about 15 h, so all three values ran (research-progress.md, 2026-11-25 23:13).

## Judging correctness
1. **Contains-match:** the normalised gold answer appears in the prediction → correct.
2. **Non-answers** (empty, "unknown", "not specified", ...) are wrong by rule. This is deterministic, added in Phase 3b.
3. **Everything else goes to LLM judges from a different model family than the generator.**
   - *Why:* a same-family judge may share the generator's errors.
   - **qwen2.5:7b answers:** two judges, llama3.1:8b **and** gemma2:9b, must both accept. Prompt v2: strict, with
     invented worked examples.
   - **llama answers:** qwen2.5:7b judges, with prompt v3 (v2 plus rules for numbers, times and ranges, and for
     lists of required items).
4. **Agreement sample:** 25% of contains-match "correct" decisions are also sent to the LLM judges, to measure how
   well the two signals agree `[src: lp/config.py#judge_agreement_sample]`.

**How the judges were chosen** (before the full run, pre-registered):
- **Items:** agreement with reference labels on 144 judged pilot items
  `[src: results/judge_selection/summary.json#results/gemma2:9b/n]`.
  - Of those, 69 are labelled correct `[src: results/judge_selection/summary.json#reference_labels/correct]` and 75
    incorrect `[src: results/judge_selection/summary.json#reference_labels/incorrect]`.
  - 5 unclear items were excluded `[src: results/judge_selection/summary.json#reference_labels/unclear]`.
- **The reference labels were written by a stronger model (Claude Opus) and spot-checked by Ali. They are not human
  labels.** Ali's edits override them.
- **Selection rule:** the highest agreement among other-family judges. The bar was ≥ 90%
  `[src: results/judge_selection/summary.json#min_agreement]`.

**Judges on prompt v2** (`results/judge_selection`):
- The first pilot's judge, llama3.1:8b with prompt v1: 47.9% [39.6, 56.3], n = 144
  `[src: results/judge_selection/summary.json#results/llama3.1:8b (v1 prompt, pilot)/agreement]`.
  - It accepted every wrong answer: false-accept rate 100.0% [100.0, 100.0], n = 75
    `[src: results/judge_selection/summary.json#results/llama3.1:8b (v1 prompt, pilot)/false_accept_rate]`.
- llama3.1:8b: 81.9% [75.7, 87.5], n = 144 `[src: results/judge_selection/summary.json#results/llama3.1:8b/agreement]`.
- gemma2:9b: 84.7% [79.2, 90.3], n = 144 `[src: results/judge_selection/summary.json#results/gemma2:9b/agreement]`.
- qwen2.5:7b: 88.9% [83.3, 93.8], n = 144 `[src: results/judge_selection/summary.json#results/qwen2.5:7b/agreement]`.
- **llama3.1:8b + gemma2:9b: 90.3% [85.4, 94.4], n = 144**
  `[src: results/judge_selection/summary.json#results/llama3.1:8b+gemma2:9b/agreement]`. Chosen for the qwen
  generators.
  - False accepts: 16.0% [8.0, 25.3], n = 75
    `[src: results/judge_selection/summary.json#results/llama3.1:8b+gemma2:9b/false_accept_rate]`.
  - False rejects: 2.9% [0.0, 7.2], n = 69
    `[src: results/judge_selection/summary.json#results/llama3.1:8b+gemma2:9b/false_reject_rate]`.

**Judges on prompt v3** (`results/judge_selection_v3`, pilot fix attempt 2, pre-registered):
- qwen2.5:7b: 90.3% [85.4, 95.1], n = 144 `[src: results/judge_selection_v3/summary.json#results/qwen2.5:7b/agreement]`.
  Beats its v2 score, so it is **chosen for the llama generators**.
  - False accepts: 2.7% [0.0, 6.7], n = 75
    `[src: results/judge_selection_v3/summary.json#results/qwen2.5:7b/false_accept_rate]`.
- llama3.1:8b + gemma2:9b: 88.9% [83.3, 93.8], n = 144
  `[src: results/judge_selection_v3/summary.json#results/llama3.1:8b+gemma2:9b/agreement]`.
  Below its v2 score of 90.3%, so **the qwen generators keep v2**.

**Caveats:**
- The judges were selected and scored on the same 144 items, so these agreements are optimistic.
- The unbiased estimate is Ali's own labels on a fresh 50-item audit sample (Phase 5, `audit/audit_sheet.csv`).
- The llama generators' judge was chosen using answers written by qwen2.5:7b.

## Statistics
- **Intervals:** every rate gets a 95% percentile bootstrap interval over questions, with 1000 resamples
  `[src: results/pilot/summary.json#meta/bootstrap_resamples]` and a fixed seed, and is reported with its n.
- **Comparisons on the same questions** (two retrievers, or two values of k): a paired bootstrap of the difference,
  plus an exact McNemar test.

## Hypotheses (written before the full run)
- **H1:** the lucky-pass rate is high on public datasets and near zero on the invented corpus.
- **H2:** it rises as retrieval weakens (smaller k; BM25).
- **H3:** larger models have more memory-lucky passes.
- **H4:** a dataset's closed-book accuracy predicts its lucky-pass rate.

## Guiding questions for writing this section
- Could a reader rebuild the experiment from your text alone? What's the minimum they need?
- Which choices would a reviewer question (the judge, generated questions, the full HotpotQA pool)? Give the
  one-line reason for each.
- Where do you say plainly that the reference labels are a model's, not a human's?
