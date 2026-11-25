# Paper framing after the novelty gate (Pivot A)

Decided by Ali on 2026-11-24. Evidence: `paper/NOVELTY.md`. These are notes for Ali, who writes the Abstract,
Introduction, Discussion and Conclusion (spec B4); they are not draft prose.

## What changes
- **H1 is a replication, not the discovery.** Jonah et al. 2026 (arXiv 2607.16604) already report on HotpotQA
  that "raw accuracy can overstate retrieval-attributable performance". We cite them where H1 is introduced and say
  we test the same effect on small local models, with a purpose-built invented corpus as the control.
- **The new parts lead:** (1) the memory-lucky vs guess-lucky split, per question; (2) how lucky passes move with
  retriever type and k (H2); (3) with model size, 3B–8B (H3); (4) closed-book accuracy as a predictor (H4);
  (5) ragaudit, an open tool that flags lucky passes on your own documents.
- **The working title in spec B1 claims the discovery** ("How Answer-Only Scores Overstate RAG"). Ali picks a new
  one. Shapes that fit Pivot A, for illustration only:
  - "Lucky Passes in Small Local RAG: Memory, Retrieval Depth and a Tool to Flag Them"
  - "When RAG Is Right for the Wrong Reason: Measuring Lucky Passes on Your Own Documents"

## Contribution list order (Introduction and Abstract)
1. Memory/guess split and H2 (the effect vs retriever and k), with paired tests.
2. H3 and H4.
3. The tool, and the invented-corpus control as a recipe others can reuse.
4. Replication of the H1 effect (Jonah et al.) in a new setting: small local models, an Ollama-only stack.

## Claims to avoid
- "We show for the first time that answer-only scores overstate RAG." Jonah et al. did.
- Anything that rests on the pilot alone (n = 100 / 48, one model, one retriever).
- Calling judge accuracy "validated by humans" before the Phase 5 audit: the judge was chosen using reference
  labels from a stronger model (Claude Opus), spot-checked by the author, not human labels.

## Questions for Ali's Introduction
- Why should someone running RAG on their own documents care whether a correct answer came from retrieval?
- What does the closest prior work (Jonah et al.) leave open that a practitioner would still need?
- If H2 comes out flat, is the tool plus the memory/guess split still enough? (If not: Pivot B, the tool paper.)
