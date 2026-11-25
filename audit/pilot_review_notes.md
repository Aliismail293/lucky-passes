# Pilot review notes (Claude, 2026-11-24)

These notes are kept in `audit/`, not `results/`, on purpose. `check_numbers` treats `results/` files as evidence
for the paper, and the counts marked **Claude's reading** below are my judgments, not measured results. They
become results only once Ali labels `audit/pilot_judge_check.csv`.

## 1. Do the report's numbers match the results files? Yes.
`uv run python scripts/check_pilot_report.py results/pilot results/pilot/PILOT_SUMMARY.md` → OK.
- Every number in `PILOT_REPORT.md` and `PILOT_SUMMARY.md` appears in `summary.json`.
- Every count and rate in `summary.json` (both cells, all records and the oracle-correct subset, plus the judge
  agreement table) recomputes exactly from the 148 rows of `records.jsonl`.

So the report faithfully summarises the records. The problems below are about whether the records are *right*.

## 2. Main problem: the LLM judge is far too lenient
- Contains-match and the `llama3.1:8b` judge disagree on 149 of 295 items, **all in one direction**: the LLM says
  correct and contains-match says no. When contains-match said correct, the LLM agreed 51 of 51 times.
- It isn't a parsing bug. The cached judge replies are clean JSON (`{"correct": true}` / `{"correct": false}`), so
  the model really is returning "true".
- **Claude's reading of all 149** (they're in `audit/pilot_judge_check.csv`): 79 look wrong, 67 look right,
  3 are unclear. By condition:
  - RAG: 23 wrong of 50
  - closed-book: 49 wrong of 57
  - oracle: 7 wrong of 42
  
  Examples the judge accepted: "James Corden" for *Christopher Whitelaw Pine*, "Neil Gaiman" for *Charles Lutwidge
  Dodgson*, "Muhammad Ali" for *Walker Smith Jr.*, "Munich" for *Germany*, and "None", "Not specified" and
  "Not applicable" as answers.
- **What it does to the numbers, if Claude's reading holds:**
  - HotpotQA closed-book: reported 59; about 18 of 100 would really be correct.
  - Invented closed-book: reported 22.9 (11 of 48); about 3 of 48 would be correct. Two of those are
    contains-matches on guessable facts ("every 15 minutes", "3 years").
  - HotpotQA RAG accuracy: reported 88; about 66 of 100.
  
  The closed-book numbers feed H4 and the memory/guess split, so this has to be fixed before the full run.
- The "agreement" figure (49.5%) is also misleading as a statistic. The LLM judge runs on *every* contains-miss
  but only a 25% sample of contains-hits, so the pool is mostly items where disagreement is likely. Report
  agreement on the random sample and LLM overturn rate on the misses as two separate numbers.

**Proposed fix (needs Ali's OK, see NEEDS_ALI):**
1. Stricter judge prompt: "a different person, place or thing is wrong; 'None' / 'not specified' is wrong; a
   less specific answer is wrong unless it names the same thing". Add 3–4 short negative examples.
2. A deterministic rule: refusals and empty-ish answers ("none", "not specified", "not applicable", "unknown")
   are wrong without asking the LLM.
3. **Judge check before the full run:** Ali labels the 149-row CSV, which takes about 20 min. The fixed judge has
   to reach high agreement with Ali on it (suggested: at least 90%) before it's trusted.
4. Re-judge the pilot. Answers are cached, so only judge calls re-run.

## 3. Second problem: retrieval is too easy for lucky passes to happen at k = 5
- HotpotQA: at least one gold paragraph was in the top 5 for 100 of 100 questions. Under the main definition
  (lucky = correct with *no* gold retrieved), a lucky pass was impossible. The questions name their entities and
  the pooled corpus is small (about 10 paragraphs per question).
- Invented corpus: k = 5 of only 38 chunks, and every question's gold chunk was retrieved.
- The multi-hop "all gold" variant does show something: HotpotQA lucky-pass-all 21.0 [13.0, 30.0] vs 0 on the
  invented corpus. But that cell is also inflated by the judge (problem 2).
- **Options (Ali decides):** (a) for HotpotQA, use the all-gold rule as primary (Jonah et al. 2026 condition on
  complete gold evidence, which makes us directly comparable); (b) make retrieval harder: pool a much larger
  HotpotQA corpus (all dev questions' paragraphs), and add distractor documents to the invented corpus so k = 5
  isn't 13% of it; (c) rely on the BM25 and k = 1 cells of the full run. Claude's suggestion is (a) + (b).

## 4. Smaller points
- **Invented corpus gave 48 questions, not 100.** 38 chunks generated candidate questions, and 55 were rejected
  (too_lexical 34, ambiguous 8, unsupported 6, unanswerable 4, relative_time 2, unparseable 1). The core config
  asks for 300, so expect about 48 unless the corpus is chunked smaller or more documents are added. That also
  means the core projection (27.2 h) overstates the invented share. Report n as it is.
- **Oracle failures:** 5 HotpotQA questions are wrong even with only the gold paragraphs (95.0 oracle). By
  Claude's reading, a few more oracle "correct" items are judge errors. Some of these (e.g. "Jeff Martin" for
  *Billy Corgan*, in all three conditions) may be bad question/answer pairs. The oracle-correct subset is already
  reported separately, which handles this.
- **No example lucky passes.** The report's "10 examples" section is empty because there were none (see 3).
- **Runtime:** 60.3 min, 0 failures, 27.2 min per 100 questions per model. Projections: core 27.2 h, k-sweep
  9.1 h. Core is over the 10 h limit, so it needs cuts (options in NEEDS_ALI).

## 5. What the pilot says about the hypotheses (pilot-only, small n, judge not yet fixed)
- H1 (lucky passes high on public data, ~0 on invented): **not testable at this setting.** 0.0 vs 0.0 under the
  main rule, because retrieval never missed. Under the all-gold rule the direction is right.
- H2–H4: not covered by the pilot (one retriever, one k, one model).
