# NOVELTY: is "lucky passes" new?

**Short answer: the core finding is not new. Parts of the design are.** A paper from July 2026 already showed, on
HotpotQA, that answers are often correct without the gold evidence and that raw accuracy overstates retrieval.
Our H1 is a replication of that. What's left that's ours: the **memory-vs-guess split**, **how the gap moves
with retriever type and k**, **small local models**, and a **per-question flag that people run on their own
documents**. That's a real contribution for a student journal or a workshop, but it is not the paper's original
pitch.

Scope of this check: web searches on 2026-11-24 for knowledge leakage, parametric vs retrieved knowledge,
closed-book baselines, RAG evaluation frameworks, answer-correctness metrics and contamination-free RAG
benchmarks, plus the papers in spec A3. 27 references verified (`citations_verified.md`). "Not found" below means
not found in this search, not proven absent.

---

## The 3 closest papers

### 1. Jonah et al. 2026, *Controlled Evaluation of Graph and Multimodal Augmentation in RAG* (arXiv 2607.16604). **Closest.**
- **What they did:** per-question gold-evidence completeness (is every gold item in the retrieved set?), then
  accuracy reported separately for complete-evidence and incomplete-evidence questions. Corpora: HotpotQA
  (distractor, 300 questions), SPIQA, PubLayNet. Hosted generators (GPT-4o-mini, Gemini 3.1 Flash-Lite, Llama 4
  Scout/Maverick through an API), one dense retriever at k=3.
- **What they found:** *"Accuracy on incomplete-evidence questions reaches 0.35--0.71 on widely disseminated
  corpora, compared with 0 on PubLayNet, indicating that raw accuracy can overstate retrieval-attributable
  performance."* That is our 2×2 table's "lucky pass" cell, on the same dataset, plus a low-memory contrast corpus.
- **What it doesn't do** (abstract plus the full-text sections read): no per-question closed-book run, so there's no
  memory-lucky vs guess-lucky split. No BM25/dense/hybrid comparison and no k-sweep. No model-size comparison
  within a family. No small local models. Not packaged as a tool for your own documents. Their main topic is
  graph and multimodal augmentation; the overstatement finding is a side result.
- **Consequence:** H1 can't be presented as new. It has to be framed as "we replicate the finding of Jonah et al.
  with small local models and a purpose-built invented corpus".

### 2. Astaraki et al. 2026, *When Iterative RAG Beats Ideal Evidence* (arXiv 2601.19827)
- **What they did:** 11 large LLMs on a chemistry multi-hop dataset under No Context / Gold Context / Iterative
  RAG. Each correct answer is labelled by the condition it needed (parametric / gold-dependent /
  iterative-only).
- **Overlap with us:** our closed-book and oracle conditions are their No Context and Gold Context. They already
  do a per-question "was memory enough?" decomposition.
- **What it doesn't do:** no crossing with whether the *real retriever* found gold (their retrieval-coverage check
  is a string-mention proxy, reported only on questions memory couldn't answer). One domain, large hosted models,
  fixed top-k, no unseen control corpus.

### 3. Liu et al. 2026, *Generating Leakage-Free Benchmarks for Robust RAG Evaluation* (SeedRG, arXiv 2605.08838)
- **What they did:** named "knowledge leakage" (*"cases where RAG tasks are solvable without retrieval"*). They
  fix it by generating new benchmark items via entity replacement and filtering out anything answerable
  closed-book.
- **Overlap:** same problem statement and motivation.
- **Difference:** they *remove* leaked items to make a cleaner benchmark. We *measure* how much leakage inflates
  the score of a given RAG setup, per question. That's the view of someone who can't swap benchmarks because
  they're evaluating their own app.

Also close: Yigit-Sert 2026 (2606.07783) uses a per-question closed-book baseline, but for robustness to
misinformation. OKBench, IRB, HybridRAG-Bench and RetrievalQA all build memory-proof benchmarks.

**Correction to spec A3:** A3 says RARE (2604.19047) "splits end-to-end accuracy by 'correct without retrieval' ×
'retrieval found the evidence'". Its abstract is about redundancy-aware *retrieval* evaluation and says nothing
like that. Unless the full text shows it, don't cite RARE for that. RARE is still useful for a different reason:
a "lucky pass" can be a retrieved non-gold document that holds the same evidence.

---

## What ours adds, precisely

| Claim | New? | Evidence |
|---|---|---|
| Answers are often right without gold retrieved; raw accuracy overstates RAG (H1) | **No.** Shown by Jonah et al. 2026 on HotpotQA | quote above |
| The gap is ~0 when the corpus can't be memorised | **Partly.** Jonah et al. show 0 on PubLayNet (a layout corpus, not built for this); we use a purpose-built invented corpus plus a niche real one (UTM) | |
| Split lucky passes into memory-lucky vs guess-lucky, per question | **Not found** in this search. Astaraki et al. have closed-book labels but don't cross them with real retrieval hits | |
| The gap vs retriever (BM25/dense/hybrid) and k (1/3/5), with paired tests (H2) | **Not found** | |
| The gap vs model size, 3B to 8B (H3) | **Not found** for this metric; Roberts et al. 2020 shows closed-book QA scales with size | |
| Closed-book accuracy predicts lucky-pass rate across datasets (H4) | **Not found** as a tested relationship | |
| Small local models (Ollama, 3–8B) only | **Different setting**, not a contribution by itself | |
| Open tool flagging lucky passes per question on your own documents (ragaudit) | **Not found**; RAGAS/ARES/RAGChecker score components but have no such flag (we haven't tested whether they could be configured to) | |

## Blunt assessment
- If we pitch "answer-only scores overstate RAG" as the discovery, a reviewer who knows Jonah et al. will reject it.
- The defensible paper: "lucky passes are common on public benchmarks (replicating Jonah et al.), they're mostly
  *memory* not guessing, they grow as retrieval weakens, and here's a free tool that flags them on your own docs."
  H2 and the memory/guess split carry the novelty. H1 is the setup, not the punchline.
- Nothing found does all of it, and the practitioner tool angle is clearly open. For a student journal, that's
  enough. For a workshop, H2 has to come out with a clear, CI-backed effect.

## Recommendation for the gate
**Pivot A** (a replication on small local models plus an open practitioner tool), keeping the full experiment.
In practice that's the same experiment with a different framing: the title and Introduction lead with H2 and the
tool, and cite Jonah et al. for H1. Pick **Go** only if you're happy to keep the current pitch *and* cite Jonah
et al. as prior evidence. **Pivot B** (tool paper) is the fallback if H2 comes out flat in the pilot.
