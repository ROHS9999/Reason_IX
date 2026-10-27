# Retrieval evaluation

12 documents, 24 questions (12 semantic, 12 exact-term).

| Mode | Hit@1 | Hit@3 | MRR | MRR semantic | MRR exact |
|---|---|---|---|---|---|
| Vector only | 92% | 100% | 0.958 | 1.000 | 0.917 |
| BM25 only | 88% | 100% | 0.938 | 0.875 | 1.000 |
| Hybrid (RRF) | 96% | 100% | 0.979 | 1.000 | 0.958 |
| Hybrid + rerank | 100% | 100% | 1.000 | 1.000 | 1.000 |