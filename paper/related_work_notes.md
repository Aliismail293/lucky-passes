# Related work notes

One entry per verified reference (see `citations_verified.md`). Each has a short note and the **exact quote**
that supports how we cite it. Quotes are copied from the abstract page fetched on 2026-11-24; the raw text is in
`verified_pages.json`. "Use:" says where it goes in the paper.

---

## A. Closest work: answers that don't need retrieval

### 1. liu2026seedrg: Generating Leakage-Free Benchmarks for Robust RAG Evaluation (arXiv 2605.08838)
Names the problem we measure: RAG benchmark questions an LLM can answer from memory. They fix it by generating
new benchmark items (entity swaps over a reasoning graph) and filtering out items answerable without retrieval.
They build a better *benchmark*; we measure the problem *per question* on an existing setup.
> "We refer to this phenomenon as knowledge leakage: cases where RAG tasks are solvable without retrieval."

Use: the term "knowledge leakage", and the motivation that this is a known and growing problem.

### 2. cho2026rare: RARE: Redundancy-Aware Retrieval Evaluation Framework (arXiv 2604.19047)
About retrieval evaluation on corpora full of near-duplicate documents (finance, legal, patents). Standard gold
labels undercount retrievers that find a *different* document with the same evidence. This matters to us: a
"lucky pass" may really be a retrieved non-gold passage that also contains the answer.
> "retrievers can be unfairly undervalued even when they retrieve documents that provide sufficient evidence, because redundancy across documents is not accounted for in evaluation."

Use: Limitations. A gold-label lucky pass can be a redundancy artefact, which is why we categorise 30 lucky passes by hand.
Note: A3 of the spec described RARE as splitting accuracy by "correct without retrieval" × "evidence found".
**The abstract does not say that.** Don't cite it for that claim unless the full text is checked.

### 3. yigitsert2026reliability: Evaluating RAG Reliability under Clean, Misleading, and Mixed Retrieval (arXiv 2606.07783)
Runs a per-question no-retrieval baseline and keeps only questions the model already answers correctly. It then
tests whether clean, poisoned or mixed context overrides that knowledge. Same closed-book-per-question tool as
ours, with a different question (robustness to misinformation, not overstatement).
> "We target correct answers to factoid questions that the model responds to correctly, even when there is no retrieval, and use this to test the system with clean, poisoned, and mixed evidence."

Use: prior use of a per-question closed-book baseline.

### 4. astaraki2026iterative: When Iterative RAG Beats Ideal Evidence (arXiv 2601.19827)
Eleven large LLMs on a chemistry multi-hop dataset under No Context / Gold Context / Iterative RAG. Each correct
answer gets the condition it needed (parametric vs gold vs iterative). That is a per-question decomposition by
*necessary condition*. It is not crossed with whether the real retriever found gold, and it uses large hosted
models, one domain, a fixed top-k, and no unseen control corpus (full text, sections 1–5.2).
> "We benchmark eleven state-of-the-art LLMs under three regimes: (i) No Context, measuring reliance on parametric memory; (ii) Gold Context, where all oracle evidence is supplied at once; and (iii) Iterative RAG"

Use: closest prior per-question decomposition; our closed-book / oracle conditions mirror its No Context / Gold Context.

### 5. jonah2026controlled: Controlled Evaluation of Graph and Multimodal Augmentation in RAG (arXiv 2607.16604)
**The single closest paper.** It conditions accuracy on per-question gold-evidence completeness and finds high
accuracy without complete gold evidence on public corpora (including HotpotQA), but 0 on PubLayNet. Its
conclusion is that raw accuracy overstates retrieval. That is our H1 in one sentence. Their focus is graph and
multimodal augmentation. From the full text (sections read): no per-question closed-book split, one dense
retriever at k=3, hosted models (GPT-4o-mini, Gemini Flash-Lite, Llama 4 via API), and no practitioner tool.
> "Accuracy on incomplete-evidence questions reaches 0.35--0.71 on widely disseminated corpora, compared with 0 on PubLayNet, indicating that raw accuracy can overstate retrieval-attributable performance."

Use: must be cited in the Introduction as prior evidence for H1. Our H1 becomes a replication on small local models.

### 6. li2025okbench: OKBench (arXiv 2511.08598)
Builds fresh news-based QA benchmarks automatically so the answers postdate pretraining. Evaluates with and
without retrieval. It's another "build a clean benchmark" answer to memorisation.
> "Our approach democratizes benchmark creation and facilitates thorough evaluation of retrieval-augmented methods by reducing overlap with pretraining data."

Use: the contamination-free benchmark line of work.

### 7. do2026irb: IRB: Automated Generation of Robust Factuality Benchmarks (arXiv 2602.08070)
Generates RAG factuality benchmarks that frontier models can't solve closed-book. Also reports that better
retrieval may be a cheaper win than a bigger generator, which relates to our H2/H3.
> "Our results demonstrate that IRB poses a significant challenge for frontier LLMs in the closed-book setting."

Use: contamination-free benchmarks; closed-book difficulty as a design goal.

### 8. lin2026hybridrag: HybridRAG-Bench (arXiv 2602.10210)
Builds multi-hop benchmarks from recent arXiv papers so that answers aren't already in model weights. It states
the confound we measure: you can't tell retrieval from recall on old benchmarks.
> "many existing benchmarks increasingly overlap with LLM pretraining data, which means answers or supporting knowledge may already be encoded in model parameters, making it difficult to distinguish genuine retrieval and reasoning from parametric recall."

Use: Introduction, statement of the confound.

### 9. zhang2024retrievalqa: RetrievalQA (arXiv 2402.16457)
A 1,271-question benchmark built so that the needed knowledge is absent from LLMs, used to test *adaptive*
retrieval (deciding when to retrieve). Same idea as our invented-corpus control: questions memory can't answer.
> "The knowledge necessary to answer the questions is absent from LLMs; therefore, external information must be retrieved to answer correctly."

Use: precedent for a "memory can't help" control set.

### 10. salemi2024erag: Evaluating Retrieval Quality in RAG (eRAG) (arXiv 2404.13781)
Argues that relevance labels correlate poorly with downstream RAG quality. Proposes scoring each retrieved
document by whether the LLM gets the answer right from it alone. That's the opposite direction from ours: we ask
when answers are right *without* the labelled passage.
> "evaluation of the retrieval model's performance based on query-document relevance labels shows a small correlation with the RAG system's downstream performance."

Use: retrieval metrics and answer metrics disagree. Part of the explanation is lucky passes.

## B. Parametric vs retrieved knowledge

### 11. mallen2023popqa: When Not to Trust Language Models (PopQA) (arXiv 2212.10511)
Models memorise popular facts and fail on long-tail ones; retrieval helps most on the long tail. This predicts
that lucky passes concentrate on popular-entity questions, i.e. public benchmarks.
> "unassisted LMs remain competitive in questions about high-popularity entities."

Use: background for H1 and H4.

### 12. roberts2020knowledge: How Much Knowledge Can You Pack Into the Parameters (arXiv 2002.08910)
Closed-book QA with fine-tuned T5 is competitive with retrieval systems and scales with model size. This is the
basis for H3 (bigger models, more memory-lucky passes).
> "We show that this approach scales with model size and performs competitively with open-domain systems that explicitly retrieve answers from an external knowledge source when answering questions."

Use: H3 motivation; the closed-book condition.

### 13. lewis2021overlap: Question and Answer Test-Train Overlap (arXiv 2008.02637)
Shows that single aggregate scores on open-domain QA hide memorisation: most test answers appear in training.
Same spirit as ours, aimed at train/test overlap rather than retrieval.
> "single aggregated test set scores do not show the full picture of what capabilities models truly have."

Use: Introduction ("aggregate scores hide what's really happening").

### 14. longpre2021conflicts: Entity-Based Knowledge Conflicts in QA (arXiv 2109.05052)
Formalises parametric vs contextual knowledge and measures over-reliance on memory. It urges practitioners to
check whether models "hallucinate rather than read".
> "Our findings demonstrate the importance for practitioners to evaluate model tendency to hallucinate rather than read"

Use: parametric vs contextual framing; practitioner angle.

## C. RAG and RAG evaluation frameworks

### 15. lewis2020rag: Retrieval-Augmented Generation (arXiv 2005.11401)
The original RAG paper: parametric seq2seq model plus a non-parametric retrieval index.
> "We explore a general-purpose fine-tuning recipe for retrieval-augmented generation (RAG) -- models which combine pre-trained parametric and non-parametric memory for language generation."

Use: definition of RAG.

### 16. es2024ragas: Ragas (arXiv 2309.15217)
The most widely used reference-free RAG evaluation suite: context relevance, faithfulness, answer quality,
scored without human labels. It's the "what practitioners use today" comparison point.
> "With Ragas, we put forward a suite of metrics which can be used to evaluate these different dimensions \textit{without having to rely on ground truth human annotations}."

Use: Related work. Practitioner frameworks score components separately but don't flag lucky passes per question.
(Don't claim RAGAS *can't* detect them; we haven't tested that.)

### 17. saadfalcon2024ares: ARES (arXiv 2311.09476)
Automated RAG evaluation with fine-tuned LM judges for context relevance, faithfulness and answer relevance,
calibrated with a small human-labelled set (PPI).
> "We introduce ARES, an Automated RAG Evaluation System, for evaluating RAG systems along the dimensions of context relevance, answer faithfulness, and answer relevance."

Use: Related work (evaluation frameworks); PPI is a model for our 50-item human audit.

### 18. chen2024rgb: RGB, Benchmarking LLMs in RAG (arXiv 2309.01431)
Tests four RAG abilities, including noise robustness and counterfactual robustness.
> "We analyze the performance of different large language models in 4 fundamental abilities required for RAG, including noise robustness, negative rejection, information integration, and counterfactual robustness."

Use: Related work (RAG benchmarks).

### 19. ru2024ragchecker: RAGChecker (arXiv 2408.08067)
Fine-grained diagnostic metrics for both retrieval and generation, validated against human judgments.
> "we propose a fine-grained evaluation framework, RAGChecker, that incorporates a suite of diagnostic metrics for both the retrieval and generation modules."

Use: Related work (diagnostic frameworks).

## D. Judging answer correctness

### 20. kamalloo2023evaluating: Evaluating Open-Domain QA in the Era of LLMs (arXiv 2305.06984)
Lexical matching badly underestimates LLM QA accuracy on NQ-open. Automated judges help but are imperfect, and
human evaluation is still needed. This is why we use contains-match plus an LLM judge plus a human audit.
> "We also find that more than 50% of lexical matching failures are attributed to semantically equivalent answers."

Use: Method, judge design; Limitations.

### 21. zheng2023judge: Judging LLM-as-a-Judge (arXiv 2306.05685)
LLM judges have position, verbosity and self-enhancement biases. Self-enhancement is the reason our judge comes
from a different model family than the generator.
> "We examine the usage and limitations of LLM-as-a-judge, including position, verbosity, and self-enhancement biases"

Use: Method, cross-family judge.

## E. Datasets and retrievers we use

### 22. yang2018hotpotqa: HotpotQA (arXiv 1809.09600)
Multi-hop Wikipedia QA with sentence-level supporting facts. Those supporting facts are our gold passages.
> "we provide sentence-level supporting facts required for reasoning, allowing QA systems to reason with strong supervision and explain the predictions"

Use: dataset; gold labels.

### 23. kwiatkowski2019nq: Natural Questions (TACL 2019, DOI 10.1162/tacl_a_00276)
Real Google queries with long and short answers annotated on Wikipedia pages. Quote from the ACL Anthology page.
> "Questions consist of real anonymized, aggregated queries issued to the Google search engine."

Use: dataset.

### 24. lee2019latent: Latent Retrieval for Weakly Supervised Open Domain QA (arXiv 1906.00300)
Introduces the open-domain versions of QA datasets, including NQ-open, which gives our NQ answer strings. Its
point that BM25 works when the asker already knows the answer is relevant to H2.
> "On datasets where the questioner already knows the answer, a traditional IR system such as BM25 is sufficient."

Use: dataset (NQ-open); H2 discussion.

### 25. thakur2021beir: BEIR (arXiv 2104.08663)
The IR benchmark whose `nq` split gives our gold passages (qrels). It also finds BM25 a robust baseline.
> "Our results show BM25 is a robust baseline"

Use: dataset (BEIR nq); retriever baselines.

### 26. robertson2009bm25: The Probabilistic Relevance Framework: BM25 and Beyond (DOI 10.1561/1500000019)
Standard reference for BM25. Verified through Crossref; no abstract available, so the quote is the title.
> "The Probabilistic Relevance Framework: BM25 and Beyond"

Use: Method, BM25 retriever.

### 27. cormack2009rrf: Reciprocal Rank Fusion (SIGIR 2009, DOI 10.1145/1571941.1572114)
Standard reference for RRF, which our hybrid retriever uses (k=60). Verified through Crossref; the quote is the title.
> "Reciprocal rank fusion outperforms condorcet and individual rank learning methods"

Use: Method, hybrid retriever.

## D. Added after the Phase 7 internal review (2026-11-26)

Suggested by the NLP reviewer. Notes only; Ali decides whether and where to cite them.

### karpukhin2020dpr: Dense Passage Retrieval for Open-Domain Question Answering (arXiv 2004.04906)
- Verified 2026-11-26 (title and authors match the fetched page).
- Why it matters here: Defines retrieval accuracy by whether a retrieved passage *contains the answer string*, not by gold ids. That is the answer-in-context rule used in the post-review analysis; cite it there.

### min2019compositional: Compositional Questions Do Not Necessitate Multi-hop Reasoning (arXiv 1906.02900)
- Verified 2026-11-26 (title and authors match the fetched page).
- Why it matters here: Shows many HotpotQA questions can be answered from a single paragraph. Explains why hit_any is near 100% on HotpotQA and why the secondary rule's "half the evidence" passes are common.

### kandpal2022longtail: Large Language Models Struggle to Learn Long-Tail Knowledge (arXiv 2211.08411)
- Verified 2026-11-26 (title and authors match the fetched page).
- Why it matters here: Model knowledge depends on how often a fact appears in pre-training. Relevant to memory-lucky passes and to H3 (model size).

### gao2023alce: Enabling Large Language Models to Generate Text with Citations (arXiv 2305.14627)
- Verified 2026-11-26 (title and authors match the fetched page).
- Why it matters here: Evaluates whether generated answers are supported by cited passages. A different way to ask "did retrieval earn this answer?"

### rashkin2021ais: Measuring Attribution in Natural Language Generation Models (arXiv 2112.12870)
- Verified 2026-11-26 (title and authors match the fetched page).
- Why it matters here: Attribution (AIS): is an output attributable to a source. The conceptual neighbour of a lucky pass: a correct answer not attributable to the retrieved context.

### arabzadeh2021shallow: Shallow pooling for sparse labels (arXiv 2109.00062)
- Verified 2026-11-26 (title and authors match the fetched page).
- Why it matters here: Sparse relevance labels miss relevant passages, so evaluations that trust them are biased. The IR version of the UTM gold-label problem.

