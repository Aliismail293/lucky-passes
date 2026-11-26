# Fact sheet: Limitations

These are notes for Ali, who writes every sentence; this file is not paper text. Each item says what the limitation
is, which way it biases the results, and what the study does about it. Tagged numbers are checked by
`scripts/check_factsheets.py`.

## Scope
- **Small local models only.**
  - The models: 3 open-weight generators of 3B–8B parameters (qwen2.5:7b, llama3.1:8b, llama3.2:3b;
    `configs/core.yaml`).
  - Bias: larger or hosted models memorise more, so their memory-lucky share is probably larger. The results don't
    speak directly to those models.
- **Four datasets, English only.**
  - The datasets: HotpotQA, Natural Questions, one invented corpus and one university calendar.
  - The invented corpus is small: 48 questions `[src: results/core/summary.json#meta/datasets/invented/verified_questions]`.
    So its rates have wide intervals.

## Measurement
- **Gold labels undercount retrieval.**
  - A "lucky pass" may really be a retrieved non-gold passage that also contains the answer (cite `cho2026rare`).
  - This is more likely in the large HotpotQA pool of 66581 passages `[src: results/pilot/summary.json#meta/datasets/hotpotqa/corpus_passages]`,
    where other paragraphs mention the same entities.
  - Bias: it inflates lucky passes. The main rule (hit_any) biases the other way, as a lower bound.
  - What the study found: on UTM this is the main source of lucky passes (see below). On HotpotQA and NQ, lucky
    passes are rare anyway.
- **An LLM judges correctness when contains-match can't decide.**
  - The judges were chosen on the same 144 items `[src: results/judge_selection/summary.json#results/gemma2:9b/n]`
    they were scored on.
  - Those items carry reference labels from a stronger model (Claude Opus), **not human labels**. So the selection
    agreement is optimistic.
  - What the study does: Ali's own labels on a fresh 50-item audit sample give the unbiased estimate. That number
    goes in Results.
  - The llama generators' judge (qwen2.5:7b, prompt v3) was chosen using answers written by qwen2.5:7b. Its
    accuracy on llama answers may differ.
- **The pilot sanity gate failed; Ali chose to proceed** (research-progress.md, 2026-11-25).
  - The pre-registered bar was invented closed-book accuracy of at most 5%. The pilot gave 10.4% [2.1, 18.8], n = 48
    `[src: results/pilot/summary.json#cells[dataset=invented,retriever=hybrid]/rates/closed_accuracy]`.
  - The 5 invented closed-book answers scored correct (NEEDS_ALI.md item A, attempt-1 diagnosis):
    - 2 are plausible default guesses, matched exactly: "every 15 minutes" and "3 years";
    - 1 is arguably correct: "6 hours" for "at most 6 hours old";
    - 2 are errors that both judges accepted: "8 AM - 5 PM" for "07:00 to 15:00", and the wrong items for a list of
      two required certificates.
    - So even a perfect judge would leave 3 of 48, above the 5% bar.
  - Bias: guess lucky passes and judge false accepts are overstated by about this much.
- **Generated questions.**
  - Questions for the invented corpus and the calendar were written by qwen2.5:7b, which is also a generator under
    test, so its own questions may suit it.
  - A verifier from a different family (llama3.1:8b) checks each question. That limits the problem but doesn't
    remove it.
- **The prompt allows memory.**
  - The RAG prompt asks the model to use the passages but doesn't forbid its own knowledge, as in a typical
    application.
  - Bias: a strict "passages only" prompt would probably lower memory-lucky passes. This wasn't tested.
- **Possible bad gold answers.** The pilot review flagged 2 HotpotQA questions whose gold answer doesn't answer the
  question (`results/pilot/PILOT_REPORT.md`). They were kept, not cherry-picked out.
- **UTM gold labels are incomplete, and some UTM questions are bad.** Found after the run, so it is reported as a
  post-hoc sensitivity analysis.
  - Many answers are boilerplate shared by many chunks, and some questions name no course.
  - Bias: UTM lucky passes are strongly inflated. Most of the UTM rate is this artifact (results fact sheet,
    section 3).
  - The fix for future work: mark every chunk that holds the answer as gold, and reject boilerplate-answer and
    underspecified questions at generation time.
- **One missing call.** llama3.1:8b never answered one UTM question with a long exclusion list. It timed out on the
  run and on the retry (temperature 0, so the output is the same each time).
  - 3 UTM cells have n = 149 `[src: results/core/summary.json#cells[dataset=utm,model=llama3.1:8b,retriever=hybrid]/n]`
    instead of 150.
  - The timeout and output length were not changed after the fact.
- **The LLM judge accepts some incomplete answers to list questions.** Of 30 sampled lucky passes, 6
  `[src: results/core/error_sample.csv#count[category_claude=judge error]]` were such judge errors (Claude's reading).
  - Bias: it inflates accuracy and lucky passes, mostly on UTM. Ali's audit measures how often it happens.

## Guiding questions for writing this section
- Which limitation would most change the headline number if it went the other way? Put that one first.
- For each one: which direction does it bias the result, and what did you do about it?
- Is there anything you'd now design differently? Say so.
