# Implementation status and proposal reconciliation

Reviewed 2026-10-17 against the supplied Word proposal, the four PART plans,
the shared contract, implementation modules, test fixtures, and reports.

## Two different specifications

`Context_Drift_Detection_Complete_Proposal.docx` is titled *Context Drift Detection
and Remediation for Parallel AI Coding Agents*, Revision 2. It has eleven sections,
a twelve-type project/spec/agent ontology, five drift types, and six remediation
levels. Its section 7 is the technical stack.

The PART plans and CONTRACT instead cite an earlier extraction brief with
sections 7.2/7.3 and 11.1/11.2, an OFBiz/workflow/document ontology, weighted
severity scores, and five remediation levels. Those citations cannot be checked
against the supplied Word document. They are retained as historical task IDs,
not presented as valid citations into Revision 2.

The code largely implements the earlier extraction milestone. No document
should say that this means the Revision 2 drift system is complete. The current
scope and gaps below take precedence over old branch layouts and completion text.

## Where the four parts actually live

All paths here are relative to `enterprise-context-graph/`. The planned
`part1_deterministic/` through `part4_drift/` directories do not exist.

| Part | Actual modules | Useful verification | Limits |
|---|---|---|---|
| 1: structural extraction | `src/contextgraph/file_scanner.py`, `contract_pipeline.py`, `triple_builder.py`, `serializer.py`, `parsers/` | `test_contract_pipeline.py`, `test_part1_integration.py`, `test_contract_compliance.py` and parser tests | Small fixtures; full rebuild; Groovy handled through the Java grammar with limited syntax coverage |
| 2: semantic extraction | `src/contextgraph/prob/` | `test_part2_integration.py`, `test_prob_contract_compliance.py` and extractor tests | Recorded responses; CUAD live adapter deferred; real corpus quality targets unmet/unrated |
| 3: graph and explorer | `contract_store.py`, `bridges.py`, `contract_validate.py`, `contract_api.py`, `dashboard/`, `ontology/contract-*.ttl` | API/dashboard regressions, six browser flows, `test_part3_integration.py` | Label-based bridge heuristics; no live drift feed; subject metadata rather than universal statement-level evidence |
| 4: drift experiments | `src/contextgraph/drift/` | `test_drift_scenario.py`, `test_drift_integration.py`, `test_drift_compliance.py` | Caller-supplied snapshots and labels; no running-agent integration or execution of remediation |

Use [the run guide](../HowToRun.md) for commands. `scripts/run_offline_tests.py`
selects the self-contained suites; `python -m pytest tests -q` also includes
real-source integration tests and the live Ollama probe.

## Revision 2 requirements compared with the code

| Word proposal requirement | Current implementation | Status |
|---|---|---|
| Versioned EARS spec registry, supersedes edges | Synthetic requirements are input documents; no registry or corresponding lifecycle | Missing |
| Twelve node types including Agent, Assumption, Checkpoint, Environment | Contract schema focuses on services, entities, tasks, policies, contracts, filings | Different schema; no complete mapping |
| Code drift detection | Git change inspection, graph diff, fixture rename scenario | Partial |
| Spec drift | Generic document change classification; no implemented spec-version workflow | Partial building blocks |
| Environment drift | No environment registry/version comparison workflow | Missing |
| Coordination drift | No canonical assumption-conflict detector across running agents | Missing |
| Intent drift via design constraints | SHACL primarily checks extraction/contract metadata and structure | Required design-decision checks missing |
| Ground truth and per-agent checkpoint named graphs in persistent Oxigraph | Contract source graphs use Oxigraph; version history uses Turtle files/SQLite; comparisons create temporary rdflib datasets | Partial, different persistence model |
| Dependency-aware agent selection | Predicate-based traversal and caller-supplied snapshot dict | Partial; no agent assignment registry |
| Six actions through RESTART | Five labels through ROLLBACK | RESTART missing; actions returned, not executed |
| Agent notification, patch delivery, acknowledgment and resume | Patch dicts returned to the caller | Missing runtime delivery |
| Live events and agent-state dashboard | Interactive context/evidence graph | Graph explorer implemented; live drift UI missing |
| FinPay, VTOP, MediTrack scenarios | OFBiz findOrders/searchOrders fixtures | Different scenario, incomplete proposal validation |
| More than 90% fewer actual restarts | Test checks 19/21 fixture agents are undisturbed | Proxy only; no executed restarts measured |
| Less than 500 ms event-to-classification | Timed supplied-graph drift calculation at approximately 520 triples | Microbenchmark, excludes upstream extraction and delivery |

## The two RDF paths

The earlier baseline uses `extract.py`, `build_graph.py`, `store_graph.py`,
`ContextStore`, and `ontology/context-ontology.ttl`. It uses the namespace
`http://example.org/ofbiz/0.1/`, direct/inferred classifications, and a default
graph. Reports in `outputs-deps/` describe this baseline.

The contract path uses `contextgraph.contract_pipeline`, `ContractStore`,
`ontology/contract-ontology.ttl`, and named `urn:*` graphs. It uses
`http://context.example.org/` plus confidence and deterministic/probabilistic
metadata. The dashboard consumes this path. The earlier graph cannot simply be
loaded under a new filename and expected to satisfy these queries.

## UI repair acceptance

- Explicit on-page problem, proposed solution, workflow, evidence guide, and scope.
- Distinct IDs for the graph container and source filter; local CSS/JS assets.
- One visual node per URI, retained graph memberships/classes, wider relationship vocabulary.
- Graph-scoped arrows and provenance; missing optional bindings become JSON null.
- Canvas selection, node dragging, pan, zoom, fit, layout toggle, and node directory.
- Source navigator with actual triple counts, Graph/List views, selected-neighborhood
  focus/clear, keyboard shortcuts, and export of the displayed graph and applied filters.
- Filter URLs, browser history, no-match state, retries, retained data on refresh failure.
- Demo labeling based on server input; no invented drift events or agent metrics.
- Desktop/mobile screenshots inspected; real-browser interaction tests pass.

For remaining risks and the evidence behind these judgments, see the
[brutal review](../BRUTAL_REVIEW.md). For documentation changes, see the
[Markdown audit](markdown-audit.md).
