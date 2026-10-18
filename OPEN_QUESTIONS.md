# Decisions and remaining implementation questions

Reviewed 2026-10-17 against the current code. The original questions mostly
concerned the earlier enterprise-extraction brief, whose numbering does not match
the supplied Revision 2 Word proposal. These decisions describe the implementation;
they are not retroactive approval of a different product specification.

## Decisions already expressed in the code

| Original question | Implemented decision / evidence |
|---|---|
| 1. Agent C severity | `drift/severity.py` uses high criticality 0.8, signature break 1, 3+-hop directness 0.25, and assumption/constraint/conflicting flags all true. Weighted sum = 0.82. The alternative 0.825 belongs to different inputs. |
| 2. Criticality source | Caller-supplied labels; defaults to normal for a changed agent. No automatic criticality classifier. |
| 3. Ollama model | `prob/client.py::OllamaClient` takes the model string from the caller. No validated universal Qwen/Owen default is specified here. The old live smoke test uses its own configured model. |
| 4. Timestamp predicate | `prov:generatedAtTime` in the contract path; the earlier baseline has its own extraction metadata. |
| 5. Version URI scheme | Fixtures use `urn:version_n`, `urn:version_n1`, and `urn:agent_snapshot_A/B/C`. APIs accept graph IDs; version history is Turtle/SQLite, not permanently registered Oxigraph checkpoints. |
| 6. Turtle graph assignment | `.ttl` files are plain Turtle graphs. `ContractStore.load_file` assigns the target named graph; no `GRAPH` blocks are stored in Turtle. |
| 7. Ten query questions | Six API queries plus four `DERIVED_QUERIES` in `tests/test_part3_integration.py`. Their fixture expectations are not an independent real-enterprise benchmark. |
| 8. Contract shape target | `ontology/contract-shapes.ttl` targets `ctx:Contract`. |
| 9. Corroboration boost | `max(raw, 0.95)` for a normalized triple match. Unmatched scores are clamped to 0.70–0.85. This is a heuristic, not calibrated confidence. |
| 10. Support types | Current semantic processors also attach support types beyond documents. Actual validation strength varies by processor. |
| 11. DAG/workflow sources | Synthetic local fixtures under `tests/fixtures/airflow` and `tests/fixtures/cicd`. They are not production repository coverage. |
| 12. Snapshot lifecycle | `drift_pipeline.run` receives `{agent: rdflib.Graph}`. There is no agent registration API, heartbeat, checkpoint delivery, or acknowledgment protocol. |
| 13. Model response schema | `prob/json_validator.py` accepts a claim array or `{claims: [...]}` with nonempty subject/predicate/object, confidence in [0,1], and optional string evidence list. Validation errors are returned. |
| 14. Hardware baseline | Integration reports record their machine and fixture scale. They do not establish portable end-to-end extraction/detection latency. |
| 15. EDGAR company list | Still unspecified and unvalidated for a live 10–20-company run; only fixture and optional fetch interfaces exist. |

## Remaining product and research decisions

1. Which ontology is authoritative: the extraction contract or Revision 2's
   Project/Requirement/Agent/Assumption/Checkpoint schema? A mapping is required.
2. How should runtime agents register their actual dependencies and receive,
   acknowledge, and safely apply patches? Current patch dictionaries are insufficient.
3. How should deleted source files map to graph removals and snapshot invalidation?
   How should versions and their manifests commit transactionally?
4. What operational policy implements RESTART and actual rollback, and who owns
   checkpoints and conflict resolution? Current thresholds return labels only.
5. Which independent real-change corpus and raters will measure false positives,
   missed drift, semantic quality, actual restart savings, and full-pipeline latency?
6. Which live model/data versions are available, reproducible, and acceptable for
   the intended environment? Recorded fixtures do not settle that question.

These gaps are documented rather than filled with invented metrics or simulated
live state. See [implementation status](docs/implementation-status.md)
and [brutal review](BRUTAL_REVIEW.md).
