# PART 1 PLAN — Deterministic Extraction (Proposal §7.2 Stage 1, Algorithm 1)

> **Status reviewed 2026-10-17.** This is the earlier enterprise-extraction
> task plan. Its section numbers refer to a brief different from the supplied
> `Context_Drift_Detection_Complete_Proposal.docx` Revision 2. Task acceptance
> targets below are not a claim of completion. See the
> [implementation status](docs/implementation-status.md)
> and [brutal review](BRUTAL_REVIEW.md).

Part 1 lives in `src/contextgraph/`: `file_scanner.py`,
`contract_pipeline.py`, `triple_builder.py`, `serializer.py`, and `parsers/`.
Fixtures and tests are under the project `tests/` directory.

Hard rules:
- Use only the documented stack: Python 3.x, lxml (source lines and XPath), tree-sitter +
  tree-sitter-java + tree-sitter-python, PyYAML, rdflib 7.x, GitPython (only for
  scanning; commit tracking is Part 4's job).
- Every fact: ctx:confidence 1.0, ctx:factType "deterministic", PROV-O
  provenance (prov:wasGeneratedBy, prov:hadPrimarySource, ctx:sourceLocation,
  ctx:sourceHash), per CONTRACT.md §5.
- Do not add features beyond §7.2 Stage 1 / Algorithm 1 / §8 tools table.

Current folder layout (workspace view; task commands run inside the project):
```text
enterprise-context-graph/
  src/contextgraph/{file_scanner,contract_pipeline,triple_builder,serializer}.py
  src/contextgraph/parsers/
  tests/fixtures/
  tests/test_*.py
  outputs/
```

## TASK 1.1 — Project scaffold + SHA-256 content-hash scanner
- Goal: Incremental file scanner per Algorithm 1 "File Scanner" (§10, Alg. 1).
- Inputs: any directory of source files.
- Steps: Implement `src/contextgraph/file_scanner.py`: recursively scan for .xml, .java,
  .groovy, .gradle files (extensions per Alg. 1); compute SHA-256 per file;
  compare against a JSON cache (`outputs/.hash_cache.json`); return only changed
  or new files; update cache after processing. Airflow .py and workflow .yml
  files are scanned the same way in Tasks 1.5/1.6.
- Output: `changed_files` list; updated hash cache.
- TEST GATE: `pytest tests/test_file_scanner.py` — (a) first run returns all
  files; (b) second run with no edits returns empty list; (c) editing one file
  returns exactly that file; (d) cache stores valid SHA-256 hex.
- DONE CRITERIA: all tests green; scanner handles missing cache file.

## TASK 1.2 — OFBiz XML extractor: servicedef + entitydef (§7.2 1.1)
- Goal: Parse OFBiz Order/Accounting/Party service and entity definitions.
- Inputs: `fixtures/ofbiz/applications/{order,accounting,party}/servicedef/*.xml`
  and `entitydef/*.xml` (create small but realistic fixtures modeled on OFBiz
  24.09 structure).
- Steps: `src/contextgraph/parsers/service.py` + `src/contextgraph/parsers/entity.py` using lxml.etree. From
  `<service>`: name, engine (java/groovy), location, invoke method, description,
  input/output parameters with types and modes. From `<entity>`: entity name,
  table name, primary key, all fields with types, all relations (one-to-one,
  one-to-many) with FK mappings. Record file path, line number, XPath.
- Output: internal fact dicts; RDF triples per example in §7.2 1.1:
  ctx:createInvoice a ctx:Service ; rdfs:label ... ; ctx:engine "java" ;
  ctx:implementedBy ... ; ctx:hasInputParam ... ; ctx:hasOutputParam ... ;
  ctx:definedIn <file://...> ; ctx:atLine 142 ; provenance fields.
- TEST GATE: `pytest tests/test_ofbiz_xml.py` — every extracted `<service>`
  yields a ctx:Service with all documented attributes; every `<entity>` yields
  ctx:Entity + ctx:Field triples (ctx:hasField) + ctx:relatesTo for FK
  relations; provenance fields present on every subject.
- DONE CRITERIA: fixture extraction matches a hand-written expected fact list.

## TASK 1.3 — OFBiz ECA + controller.xml + build.gradle (§7.2 1.1)
- Goal: Extract event-condition-action rules, routes, module dependencies.
- Inputs: fixtures `entitydef/eecas.xml` and `servicedef/secas.xml` (event-condition-actions),
  `controller.xml`, `build.gradle` in the three module fixture trees.
- Steps: Parse `<eca>`: triggering entity, action type, condition expressions,
  service calls on trigger → ctx:ECA facts. Parse controller.xml: URL routes,
  request-to-event mappings. Parse build.gradle: module dependencies.
- Output: triples in the same style as Task 1.2 (all deterministic).
- TEST GATE: `pytest tests/test_ofbiz_eca.py`, `test_ofbiz_controller.py`,
  `test_ofbiz_gradle.py` — each `<eca>` yields one ctx:ECA with trigger/action/
  conditions/service calls; routes and gradle dependencies present as typed
  triples with source location.
- DONE CRITERIA: all fixture artifacts produce triples with 1.0 confidence.

## TASK 1.4 — tree-sitter Java/Groovy AST extractor (§7.2 1.1)
- Goal: Class/method/call facts from .java and .groovy files (Algorithm 1).
- Inputs: fixture .java and .groovy files (a few small classes with imports and
  method calls).
- Steps: `src/contextgraph/parsers/java_ast.py` with tree-sitter-java: class declarations,
  method signatures (name, parameters, return type), import statements,
  method-call edges (which function calls which). Record file path + line
  number. (tree-sitter-python is used for Airflow in Task 1.5 — or Python's
  built-in ast module per §7.2 1.2; use built-in ast for Airflow as documented.)
- Output: ctx:JavaClass, ctx:JavaMethod, ctx:calls, ctx:imports triples.
- TEST GATE: `pytest tests/test_ofbiz_ast.py` — every class and method in the
  fixture appears; every call edge in the fixture appears as ctx:calls; line
  numbers correct (verified against fixture by hand).
- DONE CRITERIA: fixture fully covered.

## TASK 1.5 — Airflow DAG extractor (§7.2 1.2)
- Goal: Extract DAGs, tasks, dependencies from Python DAG files.
- Inputs: 2–3 fixture DAG files (ETL/data-pipeline style) with `DAG()`
  constructors, `PythonOperator`/`BashOperator` instances, `>>`/`<<` chains,
  docstrings/comments.
- Steps: `src/contextgraph/parsers/airflow_dag.py` using Python's built-in `ast` module:
  DAG ID, schedule interval, default args; operator instances → task ID,
  operator type; `>>`/`<<` → ctx:dependsOn task-to-task edges; docstrings and
  comments recorded for semantic enrichment.
- Output: Named Graph <urn:airflow> facts: ctx:DAG, ctx:Task (operator type is a literal);
  ctx:hasTask, ctx:dependsOn, ctx:scheduledAt, ctx:operatorType.
- TEST GATE: `pytest tests/test_airflow_dag.py` — every DAG/task/edge in the
  fixture is extracted; operator types and schedules match; triples carry full
  provenance.
- DONE CRITERIA: fixture DAGs fully covered.

## TASK 1.6 — CI/CD GitHub Actions YAML extractor (§7.2 1.3)
- Goal: Extract workflow structure from GitHub Actions YAML.
- Inputs: 2 fixture workflow files (`.github/workflows/*.yml`).
- Steps: `src/contextgraph/parsers/cicd_yaml.py` with PyYAML: workflow name, triggers
  (push, pull_request, schedule), jobs, steps; per step `uses:` (reusable
  actions), `run:` (commands), `needs:` (job dependencies); environment
  variable references and secrets usage.
- Output: Named Graph <urn:cicd> facts: ctx:Workflow, ctx:Job, ctx:Step;
  ctx:triggeredBy, ctx:hasStep, ctx:usesAction, ctx:dependsOn.
- TEST GATE: `pytest tests/test_cicd_yaml.py` — every job/step/trigger/needs
  edge extracted; secrets and env references recorded.
- DONE CRITERIA: fixture workflows fully covered.

## TASK 1.7 — RDF triple builder + Turtle serializer (§7.2 1.4)
- Goal: Normalize all facts to Turtle (.ttl) via rdflib, per §7.2 1.4.
- Inputs: fact dicts from Tasks 1.2–1.6; CONTRACT.md §1–§6.
- Steps: `src/contextgraph/triple_builder.py` maps facts to OWL classes/properties and
  attaches provenance (confidence 1.0, factType "deterministic",
  prov:wasGeneratedBy, prov:hadPrimarySource, ctx:sourceLocation,
  ctx:sourceHash). `src/contextgraph/serializer.py` serializes with rdflib to:
  outputs/ofbiz_structural.ttl, outputs/airflow.ttl, outputs/cicd.ttl.
  Each .ttl is wrapped in its Named Graph on load (Parts 3/4 wrap; files
  themselves are plain Turtle graphs — see OPEN QUESTIONS).
- Output: the three .ttl files.
- TEST GATE: `pytest tests/test_serializer.py` — each .ttl parses with rdflib;
  re-parsed triple count equals in-memory count; every subject has provenance
  metadata; sample triples match the §7.2 1.1 example shape exactly.
- DONE CRITERIA: files load cleanly into a fresh rdflib Dataset.

## TASK 1.8 — Fixtures & unit test suite
- Goal: Complete fixture set + full unit suite so the part runs standalone.
- Inputs: everything built so far.
- Steps: Finalize fixtures covering all six extractor behaviors; ensure `pytest`
  runs green from a clean checkout without network access (fixtures only).
- TEST GATE: `python scripts/run_offline_tests.py` — selected self-contained tests pass; no network calls (mock/LLM-free — this
  part uses no LLM at all).
- DONE CRITERIA: clean-room run passes.

## TASK 1.9 — PART INTEGRATION TEST (§11.1 metrics)
- Goal: End-to-end run proving the Part 1 metrics.
- Inputs: full Apache OFBiz 24.09 applications/order + accounting + party
  (cloned separately at test time; keep out of the repo) OR the fixture tree if
  the full repo is unavailable (record which was used).
- Steps: run the full pipeline end to end on the three modules; measure
  wall-clock time; count triples.
- Output: run report (JSON or Markdown) with metrics.
- TEST GATE / metrics (§11.1):
  1. Deterministic coverage >95% of services, entities, methods vs. manual
     inventory count (count XML `<service>`/`<entity>` elements and AST symbols;
     extracted/actual > 0.95).
  2. Extraction time < 5 minutes for 3 modules (wall clock).
  3. Graph size ≈ 5000+ deterministic triples for OFBiz core (report actual).
- DONE CRITERIA: all three metrics met or deviation documented in the run
  report with cause.

## TASK 1.10 — HANDOFF — CONTRACT.md compliance
- Goal: Prove Part 1 outputs conform to the shared contract.
- Steps: Write `tests/test_contract_compliance.py`: loads each outputs/*.ttl
  with rdflib, asserts every triple's subject metadata matches CONTRACT.md §5
  (confidence=1.0, factType="deterministic", provenance present), asserts only
  documented ctx: classes/properties are used, asserts file names match §6.
- TEST GATE: `pytest tests/test_contract_compliance.py` green.
- DONE CRITERIA: green; outputs/*.ttl ready for Parts 2, 3, 4 to consume.
