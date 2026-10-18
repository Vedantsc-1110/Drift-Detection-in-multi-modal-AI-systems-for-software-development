# PART 3 PLAN — Normalization, Storage, Query & Visualization

> **Status reviewed 2026-10-17.** This is the earlier enterprise-extraction
> task plan. Its section numbers refer to a brief different from the supplied
> `Context_Drift_Detection_Complete_Proposal.docx` Revision 2. Task acceptance
> targets below are not a claim of completion. See the
> [implementation status](docs/implementation-status.md)
> and [brutal review](BRUTAL_REVIEW.md).

Task references: earlier extraction brief §7.2 Stage 3 + Stage 4.

Part 3 lives in `src/contextgraph/contract_store.py`,
`bridges.py`, `contract_validate.py`, and `contract_api.py`, together with
`dashboard/` and `ontology/contract-*.ttl`. The UI repair
authorized on 2026-10-17 includes a source summary, responsive CSS, accessible
directory, error recovery, and graph controls. It remains a graph explorer.

Hard rules:
- Stack per §8: pyoxigraph (embedded RDF quad store, SPARQL 1.1, Named Graphs),
  rdflib 7.x, PySHACL, FastAPI + uvicorn, vis-network. Optional: Protege 5.x
  for inspecting the ontology (not required to build).
- Author the OWL ontology and SHACL shapes in .ttl exactly as shown in
  proposal §7.2 3.1 and 3.5.
- SHACL violations are REPORTED, never silently discarded (§7.2 3.5).
- The original feature cap is superseded by the 2026-10-17 UI repair request; additions must describe real backend capabilities.

Current folder layout (workspace view; task commands run inside the project):
```text
enterprise-context-graph/
  src/contextgraph/{contract_store,bridges,contract_validate,contract_api}.py
  ontology/contract-ontology.ttl
  ontology/contract-shapes.ttl
  dashboard/{index.html,dashboard.css,dashboard.js,vendor/}
  serve_contract_api.py
  tests/fixtures/contract/
```

## TASK 3.1 — OWL ontology in Turtle (§7.2 3.1)
- Goal: Author the full ontology shown in §7.2 3.1.
- Steps: `ontology/contract-ontology.ttl` declaring every class and property in
  CONTRACT.md §2–§3 with the exact domains/ranges given in §3.1 (e.g.
  ctx:calls rdfs:domain ctx:JavaMethod ; rdfs:range ctx:JavaMethod).
- Output: valid Turtle file.
- TEST GATE: `pytest tests/test_contract_ontology.py` — file parses with rdflib; every
  CONTRACT.md class/property is declared; domains/ranges match §3.1 exactly.
- DONE CRITERIA: green.

## TASK 3.2 — SHACL shapes in Turtle (§7.2 3.5)
- Goal: Author the validation shapes exactly as shown.
- Steps: `ontology/contract-shapes.ttl` with ctx:ServiceShape (every Service must
  have ctx:definedIn, minCount 1), ctx:ProbabilisticFactShape (every
  probabilistic fact must have ctx:confidence and ctx:extractedBy, minCount 1
  each), ctx:ContractShape (every Contract must have at least one
  ctx:hasClause). Messages as documented.
- Output: valid Turtle shapes file.
- TEST GATE: `pytest tests/test_contract_shapes.py` — shapes parse; PySHACL can
  load them; a deliberately invalid fixture graph triggers each message.
- DONE CRITERIA: green.

## TASK 3.3 — Oxigraph store + Named Graph loading (§7.2 3.3, §3.2)
- Goal: Load .ttl files into pyoxigraph with Named Graph isolation; verify
  PROV-O metadata on every triple.
- Inputs: fixture .ttl files standing in for Parts 1/2 outputs (one per Named
  Graph in CONTRACT.md §4).
- Steps: `src/contextgraph/contract_store.py`: create store; load each file into its Named
  Graph (<urn:ofbiz_structural>, <urn:airflow>, <urn:cicd>,
  <urn:ofbiz_semantic>, <urn:document_semantic>, <urn:cuad>, <urn:edgar>);
  export/backup to .ttl; run a verification pass that every triple's subject
  carries the CONTRACT.md §5 metadata (PROV-O provenance, confidence,
  factType).
- Output: populated store (persistent directory) + verification report.
- TEST GATE: `pytest tests/test_contract_store.py` — all seven Named Graphs present and
  isolated (query in one graph does not leak into another); export round-trips;
  metadata verification passes on fixtures, fails loudly on a fixture missing
  provenance.
- DONE CRITERIA: green.

## TASK 3.4 — Bridge edge creation (§7.2 3.4)
- Goal: Create the five documented bridge edge types across artifact graphs.
- Inputs: fixture graphs containing linkable endpoints.
- Steps: `src/contextgraph/bridges.py` implementing the §3.4 table:
  AirflowTask →ctx:invokesService→ OFBizService (e.g. 'etl_sync_orders'
  →'invokesService'→'findOrders'); Policy →ctx:constrains→ Service;
  Contract →ctx:mentionsEntity→ Entity; Filing →ctx:referencesModule→ Module;
  Document →ctx:relatedTo→ Document. Bridge triples are added to the store
  (same shared ctx: vocabulary — §3.3) with provenance.
- Output: bridge triples in the store.
- TEST GATE: `pytest tests/test_bridges.py` — all five edge types created on
  fixtures; each bridge triple has provenance metadata; querying "which
  policies constrain createInvoice" returns the fixture policy.
- DONE CRITERIA: green.

## TASK 3.5 — PySHACL validation (§7.2 3.5)
- Goal: Validate the whole store; report violations.
- Steps: `src/contextgraph/contract_validate.py`: run PySHACL with
  ontology/contract-shapes.ttl over all graphs; emit a validation report listing
  each violation with its sh:message; never modify data to "fix" violations.
- Output: validation report (JSON + console).
- TEST GATE: `pytest tests/test_contract_validation.py` — valid fixture graph → zero
  violations; fixture violating each documented shape → exactly the documented
  message appears.
- DONE CRITERIA: green.

## TASK 3.6 — SPARQL endpoint (§4.1)
- Goal: FastAPI + uvicorn REST API exposing SPARQL with predefined queries.
- Steps: `src/contextgraph/contract_api.py`: POST /sparql (raw SPARQL over the store) plus the six
  predefined endpoints/questions from §4.1:
  1. List all services in the Order module (module→service membership)
  2. What input/output parameters does createInvoice declare? (implemented proxy; verified entity read/write analysis is still missing)
  3. Which Airflow DAGs depend on the findOrders service? (pipeline→code)
  4. Which policies constrain invoice approval? (document→code)
  5. Which contracts mention the Order module? (legal→code)
  6. Show all probabilistic facts with confidence < 0.7 (trust filtering)
- Output: running API returning JSON results.
- TEST GATE: `pytest tests/test_contract_api.py` (TestClient) — all six predefined
  queries return correct fixture answers; raw SPARQL endpoint executes
  CONTRACT.md example queries; confidence filter works.
- DONE CRITERIA: green; `python serve_contract_api.py --demo` serves locally.

## TASK 3.7 — vis-network dashboard (§4.2)
- Goal: Interactive graph dashboard per §4.2.
- Steps: `dashboard/index.html` + JS: node/edge rendering of the Context Graph;
  filters — confidence (high/medium/all), fact type (deterministic/
  probabilistic/both), Named Graph; search by entity/service/document name;
  click any node → provenance panel showing source file, line, extractor,
  confidence.
- Output: dashboard and allowlisted CSS/JS assets served by FastAPI.
- TEST GATE: `pytest tests/test_contract_dashboard.py` — page loads; API-driven smoke
  test verifies filter parameters reach the query layer; provenance panel data
  present in the payload for a fixture node.
- DONE CRITERIA: manual + automated checks pass.

## TASK 3.8 — Fixtures & unit suite
- TEST GATE: `python scripts/run_offline_tests.py` — selected self-contained tests pass, no network.
- DONE CRITERIA: clean-room run passes.

## TASK 3.9 — PART INTEGRATION TEST (§11.1 metrics)
- Goal: End-to-end with real Part 1/2 outputs (or contract-compliant fixtures
  if those are not ready — independence rule).
- Steps: load outputs/ofbiz_structural.ttl, airflow.ttl, cicd.ttl plus the four
  probabilistic .ttl files; build bridges; validate; run API + dashboard.
- TEST GATE / metrics (§11.1):
  1. Query accuracy 9/10: run a test set of ten cross-artifact SPARQL queries
     (the six §4.1 questions plus four derived from them), score correct.
  2. Cross-artifact linking: 20 bridge edges manually verified correct
     (services→policies, contracts→entities, filings→modules, tasks→services,
     documents→documents).
- DONE CRITERIA: both metrics met or deviation documented.

## TASK 3.10 — HANDOFF — CONTRACT.md compliance
- Steps: `tests/test_part3_compliance.py`: ontology declares exactly the
  documented classes/properties; store uses exactly the seven documented Named
  Graphs + bridges; SHACL messages match the doc.
- TEST GATE: green.
- DONE CRITERIA: store + API + dashboard ready for full integration and for
  Part 4 (which reads versioned graph states via SPARQL).
