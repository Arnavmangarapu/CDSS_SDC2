# Positioning and comparison boundaries

This matrix records what can be claimed from the verified primary descriptions. It is not a numerical ranking of systems and does not establish novelty by itself.

| Work | Task and mechanism | Relevance to this study | Boundary |
| --- | --- | --- | --- |
| Öğdü et al., IEEE Access 2025, doi:10.1109/ACCESS.2025.3613340 | Adaptive multi-agent biomedical RAG, web retrieval and feedback; QA on three datasets | Architecture antecedent and externally reported QA context | Its selected questions, semantic scorer, models and iteration budget are not reproduced by our diagnosis or fixed-proposal safety experiments |
| MedRAGChecker, Findings EMNLP 2026 | Claim-level textual NLI with selective biomedical KG compatibility adjustment | Direct prior work for general biomedical claim verification | Our checksum/identity checks and bounded medication rules do not implement this general entailment capability |
| CRITIC-RAG, IEEE JBHI 2026, doi:10.1109/JBHI.2026.3687666 | Verification throughout medical retrieval/generation, including evidence filtering and groundedness checks | Direct clinical RAG verification context | Abstract-level mechanism comparison only; no claimed reproduction or superiority |
| MedRAG/MIRAGE, Findings ACL 2024 | Medical QA benchmark and component comparisons across corpora, retrievers and models | Supports matched retrieval and QA evaluation design | Does not make our ten known-passage probes an independent benchmark |
| ALCE, EMNLP 2023 | Generated answers with citation evaluation | Separates citation presence from answer support | A valid citation identifier alone is not faithful claim support |
| SciFact, EMNLP 2020 | Scientific claim support/contradiction with evidence rationales | Separates semantic support from source identity | Scientific-claim benchmark performance does not establish patient applicability |
| Current prototype | Source identity checks, explicit uncertainty handling, one-drug rule scope, graph/text candidate retrieval | Evaluate useful supported warnings, false support, failures and extraction behavior on a bounded task | Reused developer-authored cases; independent clinical support/applicability evaluation remains unavailable |

Primary reference pages:

- https://aclanthology.org/2026.findings-emnlp.399/
- https://pubmed.ncbi.nlm.nih.gov/42139130/
- https://aclanthology.org/2024.findings-acl.372/
- https://aclanthology.org/2023.emnlp-main.398/
- https://aclanthology.org/2020.emnlp-main.609/

The externally reported 47/50, 44/50 and 42/50 base-paper counts were checked against Table 5 on PDF page 12 (printed page 167401). See `paper/BASE_PAPER_COMPARISON_20261031.json` for the source fingerprint and task distinctions. The separate adapted QA pilot remains incomplete and is not pooled with the new safety study.
