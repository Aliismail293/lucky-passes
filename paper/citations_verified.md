# Citations verified

Ground rule B2.3: a reference is used only if its page was fetched and the title and authors match.

**How this was checked (2026-11-24):** `uv run python scripts/verify_citations.py --file paper/references.txt
--out paper/verified_pages.json`. For arXiv and ACL Anthology the script fetches the abstract page and reads its
`citation_title` / `citation_author` / `citation_date` meta tags. For DOIs it fetches the Crossref record. Every
page returned HTTP 200 with a title matching the one we cite. The raw fetched metadata, including abstracts, is in
`paper/verified_pages.json`. The supporting quotes in `related_work_notes.md` are copied from those fetched abstracts.
For Natural Questions the quote comes from the ACL Anthology page (https://aclanthology.org/Q19-1026/), which was also
fetched. The same command re-runs the check (Phase 7, step 4).

27 references, all verified. "Authors" lists the first three as the page gives them; the full list is in the JSON.

| # | Key | Title (as on the page) | Authors (first 3) | Date on page | Link | Status |
|---|---|---|---|---|---|---|
| 1 | liu2026seedrg | Generating Leakage-Free Benchmarks for Robust RAG Evaluation | Liu, Jiayi; Zhang, Jiaxing; Jin, Bowen (4 total) | 2026-05-09 | https://arxiv.org/abs/2605.08838 | verified |
| 2 | cho2026rare | RARE: Redundancy-Aware Retrieval Evaluation Framework for High-Similarity Corpora | Cho, Hanjun; Lee, Jay-Yoon | 2026-04-21 | https://arxiv.org/abs/2604.19047 | verified |
| 3 | yigitsert2026reliability | Evaluating RAG Reliability under Clean, Misleading, and Mixed Retrieval | Yigit-Sert, Sevgi | 2026-06-05 | https://arxiv.org/abs/2606.07783 | verified |
| 4 | astaraki2026iterative | When Iterative RAG Beats Ideal Evidence: A Diagnostic Study in Scientific Multi-hop Question Answering | Astaraki, Mahdi; Saloot, Mohammad Arshi; Kasmaee, Ali Shiraee (5 total) | 2026-01-27 | https://arxiv.org/abs/2601.19827 | verified |
| 5 | jonah2026controlled | Controlled Evaluation of Graph and Multimodal Augmentation in RAG for Document Question Answering | Jonah, Sokipriala; Akinseloyin, Opeoluwa; Ajao-Olarinoye, Michael (4 total) | 2026-07-18 | https://arxiv.org/abs/2607.16604 | verified |
| 6 | li2025okbench | OKBench: Democratizing LLM Evaluation with Fully Automated, On-Demand, Open Knowledge Benchmarking | Li, Yanhong; Xu, Tianyang; Tang, Kenan (6 total) | 2025-10-31 | https://arxiv.org/abs/2511.08598 | verified |
| 7 | do2026irb | IRB: Automated Generation of Robust Factuality Benchmarks | Do, Lam Thanh; Taleka, Bhagyashree; Bhutta, Hozaifa Ammar (6 total) | 2026-02-08 | https://arxiv.org/abs/2602.08070 | verified |
| 8 | lin2026hybridrag | How Much Reasoning Do Retrieval-Augmented Models Add beyond LLMs? A Benchmarking Framework for Multi-Hop Inference over Hybrid Knowledge (HybridRAG-Bench) | Lin, Junhong; Zhang, Bing; Wang, Song (7 total) | 2026-02-10 | https://arxiv.org/abs/2602.10210 | verified |
| 9 | zhang2024retrievalqa | RetrievalQA: Assessing Adaptive Retrieval-Augmented Generation for Short-form Open-Domain Question Answering | Zhang, Zihan; Fang, Meng; Chen, Ling | 2024-02-26 | https://arxiv.org/abs/2402.16457 | verified |
| 10 | salemi2024erag | Evaluating Retrieval Quality in Retrieval-Augmented Generation | Salemi, Alireza; Zamani, Hamed | 2024-04-21 | https://arxiv.org/abs/2404.13781 | verified |
| 11 | mallen2023popqa | When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories | Mallen, Alex; Asai, Akari; Zhong, Victor (6 total) | 2022-12-20 | https://arxiv.org/abs/2212.10511 | verified |
| 12 | roberts2020knowledge | How Much Knowledge Can You Pack Into the Parameters of a Language Model? | Roberts, Adam; Raffel, Colin; Shazeer, Noam | 2020-02-10 | https://arxiv.org/abs/2002.08910 | verified |
| 13 | lewis2021overlap | Question and Answer Test-Train Overlap in Open-Domain Question Answering Datasets | Lewis, Patrick; Stenetorp, Pontus; Riedel, Sebastian | 2020-08-06 | https://arxiv.org/abs/2008.02637 | verified |
| 14 | longpre2021conflicts | Entity-Based Knowledge Conflicts in Question Answering | Longpre, Shayne; Perisetla, Kartik; Chen, Anthony (6 total) | 2021-09-10 | https://arxiv.org/abs/2109.05052 | verified |
| 15 | lewis2020rag | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | Lewis, Patrick; Perez, Ethan; Piktus, Aleksandra (12 total) | 2020-05-22 | https://arxiv.org/abs/2005.11401 | verified |
| 16 | es2024ragas | Ragas: Automated Evaluation of Retrieval Augmented Generation | Es, Shahul; James, Jithin; Espinosa-Anke, Luis (4 total) | 2023-09-26 | https://arxiv.org/abs/2309.15217 | verified |
| 17 | saadfalcon2024ares | ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems | Saad-Falcon, Jon; Khattab, Omar; Potts, Christopher (4 total) | 2023-11-16 | https://arxiv.org/abs/2311.09476 | verified |
| 18 | chen2024rgb | Benchmarking Large Language Models in Retrieval-Augmented Generation | Chen, Jiawei; Lin, Hongyu; Han, Xianpei (4 total) | 2023-09-04 | https://arxiv.org/abs/2309.01431 | verified |
| 19 | ru2024ragchecker | RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation | Ru, Dongyu; Qiu, Lin; Hu, Xiangkun (18 total) | 2024-08-15 | https://arxiv.org/abs/2408.08067 | verified |
| 20 | kamalloo2023evaluating | Evaluating Open-Domain Question Answering in the Era of Large Language Models | Kamalloo, Ehsan; Dziri, Nouha; Clarke, Charles L. A. (4 total) | 2023-05-11 | https://arxiv.org/abs/2305.06984 | verified |
| 21 | zheng2023judge | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | Zheng, Lianmin; Chiang, Wei-Lin; Sheng, Ying (13 total) | 2023-06-09 | https://arxiv.org/abs/2306.05685 | verified |
| 22 | yang2018hotpotqa | HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering | Yang, Zhilin; Qi, Peng; Zhang, Saizheng (7 total) | 2018-09-25 | https://arxiv.org/abs/1809.09600 | verified |
| 23 | kwiatkowski2019nq | Natural Questions: A Benchmark for Question Answering Research | Tom Kwiatkowski; Jennimaria Palomaki; Olivia Redfield (18 total) | 2019-11 (TACL vol. 7) | https://doi.org/10.1162/tacl_a_00276 and https://aclanthology.org/Q19-1026/ | verified |
| 24 | lee2019latent | Latent Retrieval for Weakly Supervised Open Domain Question Answering | Lee, Kenton; Chang, Ming-Wei; Toutanova, Kristina | 2019-06-01 | https://arxiv.org/abs/1906.00300 | verified |
| 25 | thakur2021beir | BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models | Thakur, Nandan; Reimers, Nils; Rücklé, Andreas (5 total) | 2021-04-17 | https://arxiv.org/abs/2104.08663 | verified |
| 26 | robertson2009bm25 | The Probabilistic Relevance Framework: BM25 and Beyond | Stephen Robertson; Hugo Zaragoza | 2009 (Foundations and Trends in IR) | https://doi.org/10.1561/1500000019 | verified (Crossref) |
| 27 | cormack2009rrf | Reciprocal rank fusion outperforms condorcet and individual rank learning methods | Gordon V. Cormack; Charles L A Clarke; Stefan Buettcher | 2009 (SIGIR '09) | https://doi.org/10.1145/1571941.1572114 | verified (Crossref) |

Notes
- Dates are the arXiv first-submission dates shown on each page. Where a paper was later published at a venue, the
  BibTeX in Phase 6 must use the venue version, and that version must be checked again before it is used.
- Refs 26 and 27 were checked through Crossref only; neither page has an abstract. They are cited only for the
  methods their titles name (BM25, RRF). The quote in the notes is therefore the title.
- Two close papers (refs 4 and 5) were also read in full HTML for NOVELTY.md. Claims about their method details
  that go beyond the abstract are marked "(full text)" in the notes and must be re-read before the paper cites them.
