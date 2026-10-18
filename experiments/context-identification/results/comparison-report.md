# Context Identification Experiment: comparison report

Adjudication coverage: 9/9 (100.0%). Accuracy-style metrics use adjudicated items only.

| Metric | A deterministic | B probabilistic | C hybrid |
|---|---|---|---|
| Extracted facts | 8 | 1 | 8 |
| Adjudicated | 8 | 1 | 8 |
| Correct | 8 | 0 | 8 |
| Unsupported | 0 | 1 | 0 |
| Pending review | 0 | 0 | 0 |
| Accuracy (adjudicated only) | 1.0 | 0.0 | 1.0 |
| Execution time (s) | 0.83 | 0.24 | 1.07 |

Provenance coverage (all extracted, not just adjudicated):
- A_deterministic: {"covered": 8, "rate": 1.0, "total": 8}
- B_probabilistic: {"covered": 1, "rate": 1.0, "total": 1}

Repeatability (rerun agreement, volatile timestamps excluded):
- A_deterministic: {"identical_content": true, "items_a": 4555, "items_b": 4555}
- B_probabilistic: {"identical_content": true, "items_a": 1, "items_b": 1}

Graph validation (SHACL):
- A_deterministic: {"conforms": true, "violations": 0, "warnings": 20}
- C_hybrid: {"conforms": true, "violations": 0, "warnings": 20}
- B_probabilistic: n/a (proposals are not graph triples)

> Stub-client B numbers measure plumbing only, never LLM quality.
> C validation covers the deterministic graph; accepted proposals are not merged into it.
