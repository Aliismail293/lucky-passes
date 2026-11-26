# Fact sheet: Results (to be filled after the full run)

These are notes for Ali, who writes every sentence; this file is not paper text. Claude fills this file from
`results/core/summary.json`, `results/ksweep/summary.json` and `results/FINDINGS.md` once the full run and Phase 5
are done. Every number will carry a source tag checked by `scripts/check_factsheets.py`.

## What will be here
- **Main table:** per dataset × generator × retriever at k = 5, each rate with its n and 95% CI.
  - Rates: accuracy, true pass, lucky pass (hit_any, main) and lucky pass (hit_all, secondary).
  - Lucky passes split into memory lucky and guess lucky.
  - Closed-book and oracle accuracy.
- **H1 to H4:** each with the test, the effect size with its CI, and held / not held.
- **The k-sweep:** the lucky-pass rate against k, with paired comparisons.
- **Judge accuracy on Ali's 50-item audit** (Ali's own labels), next to the selection-time agreement, which is
  optimistic.
- **The hand categorisation of lucky passes** from the audit (non-gold passage holds the answer / memory / guess /
  bad gold).

## Guiding questions for writing this section
- What's the one number a reader should remember? Give its CI and n.
- Which hypothesis surprised you? Report it as plainly as the ones that held.
- Does the audit change any headline number? Say which, and by how much.
