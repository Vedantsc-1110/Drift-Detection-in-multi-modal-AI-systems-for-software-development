# Brutal review of the current solution

Reviewed **2026-10-17**. Scope: the supplied Word proposal, original project
Markdown, source modules, entrypoints, schemas, fixtures, archived outputs, and
available tests. This is an implementation review, not an independent security
audit or a validation of live model quality.

## Verdict

**This is a useful context-extraction research prototype with a working graph
explorer and a controlled drift demonstration. It is not the complete parallel
agent drift detection and remediation platform described in the Word proposal.**

The largest issue was not CSS. The repository mixed three generations of scope:
an older OFBiz baseline, a four-part extraction contract, and a broader Revision 2
drift proposal. Their ontologies, test claims, section numbers, storage models,
and remediation levels differ. The updated documentation now makes that explicit.

## What was actually broken and fixed

| Defect | Consequence | Repair and evidence |
|---|---|---|
| Dropdown and canvas shared `id="graph"` | Renderer targeted a select element; UI tests only checked text hooks | Unique container/filter IDs; actual canvas click, drag, zoom browser checks |
| Almost no layout or visual hierarchy | Purpose and next actions were hard to discover | Responsive CSS system; visible problem/solution, guide, evidence inspector |
| Reload constructed another network without destroying the old one | Repeated render lifecycle could accumulate canvases/listeners | Destroy previous network; browser check confirms one canvas after repeated reload |
| Several relationship predicates were omitted | Services, implementations, fields, and clauses appeared disconnected | Expanded contract relationship list, including calls/implementedBy/hasField/hasClause |
| Repeated subject rows created duplicate visual IDs | Cross-graph or multiply typed nodes could break the renderer | Deduplicate by URI while retaining classes and graph memberships |
| Source filter did not scope edge queries | A selected graph could show relationships asserted elsewhere | Scope node, edge, and selected evidence queries; regression tests |
| Node/graph IRIs were interpolated without validation | Malformed inputs could alter or break query syntax | Validate IRIs; serialize search terms as RDF literals; injection regressions |
| Unbound optional query values became the string `None` | Missing evidence looked like returned textual data | Return JSON null; inspector uses explicit unavailable labels |
| Failed HTTP responses were not handled consistently | Errors or stale evidence could be shown as valid data | HTTP checks, timeouts, retries, selection sequencing, explicit stale-refresh state |
| Server only recognized its original five fixture filenames | Canonical pipeline outputs and some source graphs could not be served correctly | Canonical seven-graph loader plus bridges and fixture aliases; loader tests |
| Server cleared `stores/serve-demo` on every startup | Startup reused and erased a persistent project store | Read source files into a temporary runtime store |
| Incremental outputs used only filename stems | Same-named files in different directories overwrote each other | Preserve relative path and source suffix; collision regression |
| Hash cache skipped files even when their extraction outputs were gone | A fresh output folder could receive no facts | Rebuild when the corresponding cached artifact is absent |
| Report generator always said base entities were outside scope | The dependency report claimed entities absent while counting 112 of them | Generate scope/relations text from data; rebuild JSON/MD from archived RDF |
| README, run guide, plan paths, and open questions were stale | New readers received conflicting or nonexistent instructions | Current entrypoints, status mapping, resolved decisions, and prerequisite-aware checks |

## Remaining limitations that materially affect the project

### 1. The supplied proposal is only partly implemented

The Word document specifies an EARS spec registry, twelve project/spec/agent
types, five drift types, six remediation levels, agent notification/resume,
and live event/agent displays. The implementation primarily follows the older
OFBiz extraction plans instead. See the requirement-by-requirement
[comparison](docs/implementation-status.md).

There is no complete spec registry, environment lifecycle, assumption-conflict
detector, or design-decision-to-code intent validator. Reading requirements as
documents does not implement spec drift. Passing metadata SHACL checks does not
establish compliance with architectural decisions.

### 2. Remediation is a recommendation, not an action

`drift/remediation.py` maps a number to one of five labels. `drift/patch.py`
returns structured data. There is no connector to a running coding agent, delivery
acknowledgment, checkpoint restoration, worktree rollback, or resumed execution.
RESTART is absent. A ROLLBACK result does not actually revert code.

### 3. The drift engine receives its world from the caller

`drift/drift_pipeline.py::run` accepts the new graph, snapshots, and labels.
There is no continuous end-to-end watcher/service wiring commit detection,
source ownership, extraction, version assembly, notification, and event logging
into one operational loop. Individual components and fixture integration are
present; a deployed coordination service is not.

### 4. Severity is partly declared and heuristic

Criticality, constraint violation, and conflicting-code flags are caller-supplied.
Directness comes from change-shape rules in `derive_inputs`, rather than the
shortest path returned by `traverse`. Traversal is predicate-based BFS; it does
not enforce the entire claimed class-by-class dependency path.

Agent C's 0.82 follows the fixture's high criticality, signature break, 3+-hop,
and three true flags. It is arithmetically valid for those inputs, not an
independently established prediction of real agent impact. The weights and
thresholds have not been empirically calibrated.

### 5. Snapshot coverage limits what drift can be seen

`sparql_diff.py` restricts comparison to subjects already in an agent snapshot.
It can miss newly introduced subjects relevant to an agent's broader task.
An agent that fails to record a dependency can appear unaffected. Query results
are converted to strings; literal datatype/language distinctions can be lost.
Multi-valued modifications are paired combinatorially, not interpreted as
semantic edits. There is no soundness or completeness proof.

### 6. Versioning is not the persistent named-graph design described in the proposal

`drift/versioning.py` writes Turtle files and a SQLite manifest. Comparison builds
temporary rdflib named graphs. Contract source storage separately uses Oxigraph.
There is no single transactional, persistent ground-truth/checkpoint system tying
the two together. File creation and manifest insertion are not one atomic commit,
and concurrent version writers are not comprehensively handled.

### 7. Incremental extraction is not a complete state-maintenance system

The collision and missing-output bugs are fixed. `run_incremental` still returns
the changed-file delta, not the whole current repository graph. The caller must
carry unchanged facts forward and explicitly map deleted files/symbols to removed
subjects. Those responsibilities are not automatically orchestrated. The Part 1
contract pipeline itself performs a full rebuild despite maintaining scan hashes.

### 8. Bridge links are lexical heuristics, not verified semantics

`bridges.py` uses name substrings and shared words to propose relationships.
A policy naming a service does not prove it constrains that service. A document
pair sharing a word does not prove meaningful relatedness. Unclaimed filing
sections can be shared across filing matching, increasing false-link risk.

Bridge confidence 1.0 reflects deterministic rule execution, not semantic truth.
Bridge record identifiers use a sorted ordinal; rebuilding a changed collection
can shift identities. The UI now avoids implying that endpoint provenance proves
an arrow, but the underlying linking quality still needs independent evaluation.

### 9. Confidence and support labels are not calibrated truth estimates

`prob/corroboration.py` matches normalized final URI segments, which can collapse
different namespaces. Known endpoints produce INDIRECT support without proving
the relationship. Evidence presence can produce SYNTHETIC support; that does not
establish the origin of a statement. Uncorroborated scores are clamped to
0.70–0.85, so even a very low input can be raised to 0.70. Evidence text is not
universally verified as a source quotation.

### 10. Live semantic extraction quality is unproven

The committed Part 2 report uses recorded responses. It reports 309 triples
against a roughly 500-triple target, DIRECT support 0/20, and DIRECT+INDIRECT
10/20 against a greater-than-60% target. The human accuracy column is unfilled;
the greater-than-80% accuracy target is not established. The sample contains
20 claims rather than 50 and includes repeated facts across document formats.

CUAD ingestion reads a custom adapted JSON schema; the original Hugging Face
dataset adapter is deferred. Live EDGAR has an optional dependency and has not
been validated over the planned 10–20-company collection in this review.

### 11. Structural extraction has a limited supported syntax

Java/Groovy AST extraction is useful but is not a compiler or full name-resolution
engine. Groovy uses a Java grammar; dynamic syntax is incompletely covered.
Airflow and YAML parsers recover supported static patterns, not runtime-generated
workflows. Service I/O parameter names do not establish database reads/writes.
The old baseline's Java/Groovy-body limitation remains true for that baseline,
even though the separate contract path now has AST extraction.

### 12. Provenance is not uniformly per assertion

Most contract metadata lives on subjects. Multiple statements or graph-specific
observations can share that metadata. The explorer's node API returns one
deterministically selected observation, not a complete provenance history. The
edge payload identifies its graph but does not expose verified per-edge source,
line, extractor, and calibrated confidence. The older baseline has richer reified
statement provenance in some paths; the two approaches are not unified.

### 13. Two schemas coexist without a general migration

The baseline `ofbiz` vocabulary/default graph and the newer `ctx` contract/named
graphs are different data models. Archived 117,788-triple baseline output does
not prove that the current dashboard or contract queries operate correctly at
that scale. No general conversion into the Revision 2 project/spec/agent schema
is implemented.

### 14. The dashboard is an explorer, not live monitoring

It now works and explains its scope, but has no event stream, active-agent
registry, diff/time-travel view, remediation execution, or live agent state.
There is no automatic source refresh. Filters show an induced graph: hiding a
neighbor also hides its edge. Choosing only `urn:bridges` may mostly show bridge
records because endpoint definitions live in other graphs.

The canvas is not fully screen-reader navigable; the HTML node directory and
connection buttons provide an alternative. Mobile users may need to zoom or use
that directory. No large-graph pagination, clustering, or bounded query/render
budget exists. Fit-to-view cannot make thousands of nodes legible.

### 15. Current metrics do not prove the headline claims

The drift test's greater-than-90% metric is the fraction of supplied fixture
agents left undisturbed, achieved by adding unaffected agents. It is not measured
restart savings against a running baseline. The timed test measures supplied-graph
drift calculation on padded data; it excludes detection, extraction, external
models, persistence, and patch delivery. One formatting-only case is not a
general false-positive study. Thirty identical fixture verdict hashes establish
repeatability for that fixture, not semantic correctness.

The Part 3 ten-query and twenty-bridge results use declarative fixtures with
handwritten expectations. They test implementation behavior, not independent
real-enterprise generalization. This review did not authenticate the proposal's
competitive novelty claims or bibliographic references.

### 16. Real-data reproduction is incomplete in this checkout

Apache OFBiz is intentionally absent. The initial unrestricted test run produced
10 failures, 71 setup errors, 181 passes, and 9 skips. These failures were not
silently converted into passes. The new offline runner explicitly excludes the
twelve real-source modules and reports skips.

Corpus checks found 20 documents, 72 facts, 18 negatives, and 78 cross-document
links. All 20 source/distribution Markdown document pairs are identical. The
validator still fails 40 source-path checks because the referenced OFBiz files
are unavailable. Archived counts have not been rerun against the original source.

### 17. This is a local development service

There is no authentication, tenant isolation, bounded raw-query interface,
deployment hardening, or full dependency lock. The raw SPARQL endpoint has
limited error/result-shape handling. Provenance can contain local paths. The
server binds to loopback by default; that is the supported context here.
PyPDF2 and current TestClient integration emit deprecation warnings.

The installed design skill references an accessibility subskill that is absent,
and the security skill's detailed ASVS reference files are missing. This review
applied safe rendering/input handling and keyboard/responsive checks; it makes
no ASVS certification or complete WCAG-conformance claim.

## What the verification does support

- Self-contained Python tests, including the new API/loader/incremental/report regressions, pass.
- Six real-browser flows pass: canvas interactions, filters/history, keyboard directory/relationships, renderer failure, API retry/stale state, and responsive layout.
- Desktop and 390-pixel mobile screenshots were visually inspected.
- UI/graph defects above are reproducible regressions with concrete fixes.
- Stored historical data and synthetic ground truth were not rewritten to manufacture better benchmark scores.

See [HowToRun.md](HowToRun.md) for exact commands and current test totals.

## Work needed before claiming the proposal is complete

1. Freeze one authoritative ontology and requirement set; define how the extraction
   graph maps to specs, agents, assumptions, environments, and checkpoints.
2. Wire an end-to-end change service with agent registration, reliable snapshot
   coverage, deleted-source handling, transactional versions, and actual delivery.
3. Implement dedicated spec/environment/coordination/intent workflows and safe,
   reviewable remediation execution, including the proposed restart policy.
4. Evaluate independent real changes and all three proposal scenarios, with held-out
   labels, false-positive/negative rates, actual restart savings, and end-to-end latency.
5. Add a live event/agent interface after a real backend feed exists; profile and
   bound queries and rendering at representative repository scale.
