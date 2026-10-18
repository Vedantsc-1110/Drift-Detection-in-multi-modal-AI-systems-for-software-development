# PART 4 PLAN — Context Drift Detection (Proposal Part 2, §7.3, Algorithm 3)

> **Status reviewed 2026-10-17.** This is the earlier enterprise-extraction
> task plan. Its section numbers refer to a brief different from the supplied
> `Context_Drift_Detection_Complete_Proposal.docx` Revision 2. Task acceptance
> targets below are not a claim of completion. See the
> [implementation status](docs/implementation-status.md)
> and [brutal review](BRUTAL_REVIEW.md).

Part 4 lives in `src/contextgraph/drift/`. Snapshots
and labels are supplied as Python data. Versions are Turtle files plus a SQLite
manifest, with temporary rdflib named graphs during comparison. Persistent
Oxigraph checkpoint orchestration and real agent remediation are still missing.

Hard rules:
- Stack per §8: pyoxigraph (SPARQL), GitPython (commit tracking / diff
  analysis), SQLite (version manifest + event log), rdflib (fixture .ttl).
- Use the EXACT severity weights, factor scores, and remediation thresholds
  from CONTRACT.md §7 (proposal §7.3 Step 6–7). Do not tune them.
- Versioning discipline (§7.3 Step 3): new Named Graph for V(n+1); copy
  unchanged triples from V(n); apply additions/removals/modifications; V(n)
  remains queryable — never mutated (Iceberg-inspired, §3.1 item 10).
- Event log is append-only, never deleted (§7.3 Step 9).
- The re-extraction hook (Step 2) calls the Part 1/2 pipelines as an external
  command/configurable callback — never as an import. For standalone
  development, fixtures simulate the extractor output.

Current folder layout (workspace view; task commands run inside the project):
```text
enterprise-context-graph/
  src/contextgraph/drift/  # detection, extraction hook, versions, diff, scores, patches
  tests/fixtures/drift/
  tests/test_drift_*.py
```

## TASK 4.1 — Fixtures: V(n), agent snapshots, change events
- Goal: Standalone test bed reproducing the §7.3 scenario inputs.
- Steps: hand-make fixture Turtle: V(n) graph containing ctx:findOrders a
  ctx:Service (with provenance per CONTRACT.md §5); agent snapshots
  <urn:agent_snapshot_A> (references createOrder + findOrders, 1-hop),
  <urn:agent_snapshot_B> (Accounting-only facts), <urn:agent_snapshot_C>
  (etl_task →ctx:invokesService→ findOrders); fixture "re-extraction output"
  where findOrders is renamed searchOrders with new required input param
  partyId; a small local git repo fixture for GitPython.
- Output: fixtures/*.ttl, fixture repo.
- TEST GATE: `pytest tests/test_drift_fixtures.py` — fixtures parse; snapshots
  contain the documented triples.
- DONE CRITERIA: green.

## TASK 4.2 — Change event detection (§7.3 Step 1)
- Goal: Detect git commits / document updates / config changes.
- Steps: `src/contextgraph/drift/change_detector.py` using GitPython: given a repo path, detect
  the new commit, list changed file paths, classify them (source/config vs.
  document) to route to the right extractor.
- TEST GATE: `pytest tests/test_drift_change_detector.py` — committing a file change
  in the fixture repo yields the changed path list and commit SHA.
- DONE CRITERIA: green.

## TASK 4.3 — Incremental re-extraction hook (§7.3 Step 2)
- Goal: Re-run extractors ONLY for changed files via SHA-256 content-hash
  caching.
- Steps: `src/contextgraph/drift/incremental.py`: compute SHA-256 of each file, compare to
  cached hashes, skip unchanged, invoke the configured extractor command
  (subprocess/CLI callback) for changed files only; merge returned .ttl into
  the new extraction result. Fixture mode: a fake extractor command returns
  pre-baked .ttl.
- TEST GATE: `pytest tests/test_drift_incremental.py` — unchanged files skipped;
  exactly one changed file re-processed; hash cache updated.
- DONE CRITERIA: green.

## TASK 4.4 — Immutable ContextVersion V(n+1) + SQLite manifest (Step 3)
- Goal: Versioned graph states, never mutated.
- Steps: `src/contextgraph/drift/versioning.py` (including manifest functions): create Named Graph
  for V(n+1); copy unchanged triples from V(n); apply new/modified/removed
  triples; record in SQLite manifest {version_id, named_graphs[],
  commit_sha, timestamp}; V(n) stays queryable. Provide time-travel query:
  "load graph as of version V(k)".
- TEST GATE: `pytest tests/test_drift_versioning.py` — after a change, V(n) triple
  count unchanged; V(n+1) contains the rename (searchOrders present,
  findOrders service triple removed, new hasInputParam partyId added);
  manifest rows correct; time-travel returns the old state.
- DONE CRITERIA: green.

## TASK 4.5 — SPARQL cross-graph diff (§7.3 Step 4)
- Goal: Diff each agent snapshot vs. V(n+1) with the documented query shape.
- Steps: `src/contextgraph/drift/sparql_diff.py`: for each snapshot graph, run the §7.3 query
  pattern (GRAPH <urn:version_n1> ?subject ?predicate ?newObject /
  GRAPH <urn:agent_snapshot_X> ?subject ?predicate ?oldObject /
  FILTER new != old) producing additions (in V(n+1), not in snapshot),
  removals (in snapshot, not in V(n+1)), modifications (same subject,
  different value). No diffs → CONTINUE for that agent.
- TEST GATE: `pytest tests/test_drift_diff.py` — Agent A snapshot diffs: findOrders
  rename detected (modification/removal+addition); Agent B: empty diff;
  Agent C: etl_task→invokesService→findOrders flagged (removal).
- DONE CRITERIA: green; empty-diff agents short-circuit to CONTINUE.

## TASK 4.6 — Typed impact traversal (§7.3 Step 5)
- Goal: Blast radius via typed dependency paths.
- Steps: `src/contextgraph/drift/traversal.py`: walk the CONTRACT.md §7 path (Symbol →calls→
  Symbol →implementedBy→ Service →constrainedBy→ Policy →mentionedIn→
  Contract/Filing →dependsOn→ DAG Task →assignedTo→ Agent/System) from changed
  triples; return affected entities with hop distance.
- TEST GATE: `pytest tests/test_drift_traversal.py` — from the changed findOrders
  symbol, traversal reaches the invoking Airflow task at distance per fixture;
  hop distances recorded.
- DONE CRITERIA: green.

## TASK 4.7 — Severity scoring (§7.3 Step 6)
- Goal: 6-factor weighted model, exact weights.
- Steps: `src/contextgraph/drift/severity.py`: Severity = Σ(weight × factor_score) with
  CONTRACT.md §7 weights and value scales (criticality 1.0/0.8/0.5/0.2;
  contract breakage 1.0/0.3/0.0; directness 1.0/0.5/0.25; yes/no factors
  1.0/0.0).
- TEST GATE: `pytest tests/test_drift_severity.py` — Agent A inputs
  (criticality normal=0.5, signature break=1.0, 1-hop=1.0, assumption
  invalidated=yes) → 0.15×0.5 + 0.35×1.0 + 0.20×1.0 + 0.10×1.0 + 0 + 0 =
  0.725 exactly; Agent B → 0.0; Agent C → documented expected value 0.82
  (resolved fixture inputs: high, signature break, 3+-hop, three true flags; see OPEN_QUESTIONS.md).
- DONE CRITERIA: green; exact float equality on fixture expectations.

## TASK 4.8 — Remediation + context patch + event log (Steps 7–9)
- Goal: Graduated remediation, structured patch, append-only log.
- Steps: `src/contextgraph/drift/remediation.py`: thresholds per CONTRACT.md §7 (0 CONTINUE;
  0–0.35 REFRESH; 0.35–0.60 RE-BRIEF; 0.60–0.85 RE-PLAN; ≥0.85 ROLLBACK).
  `src/contextgraph/drift/patch.py`: per affected agent generate patch = {diff summary
  with specific triples, invalidated assumptions, recommended remediation with
  evidence, new context snapshot}. `src/contextgraph/drift/event_log.py`: append-only SQLite
  log of {change event details (commit SHA, file paths, timestamp), new
  version ID, affected agents with severity scores and remediation actions}.
- TEST GATE: `pytest tests/test_drift_remediation.py` — 0.725→RE-PLAN; 0.0→CONTINUE;
  0.82→RE-PLAN; boundary probes (0.3499→REFRESH, 0.35→RE-BRIEF, 0.5999→
  RE-BRIEF, 0.60→RE-PLAN, 0.8499→RE-PLAN, 0.85→ROLLBACK); patch contains all
  four documented sections; log rows append and never delete.
- DONE CRITERIA: green.

## TASK 4.9 — Canonical 3-agent scenario end-to-end (§7.3 scenario)
- Goal: Reproduce the proposal's worked example exactly.
- Steps: wire 4.2→4.8 into `drift_pipeline.py`; run on fixtures.
- TEST GATE: `pytest tests/test_drift_scenario.py` — Agent A: diff found, impact
  direct, severity 0.725 → RE-PLAN; Agent B: no diff → CONTINUE (undisturbed);
  Agent C: service no longer exists, severity 0.82 → RE-PLAN; report shows
  "Agent B continues undisturbed; A and C receive context patches".
- DONE CRITERIA: green.

## TASK 4.10 — PART INTEGRATION TEST (§11.2 metrics)
- Goal: Metrics of Part 2 of the proposal.
- Steps: run the full pipeline repeatedly and on negative sets.
- TEST GATE / metrics (§11.2):
  1. Undisturbed-agent proxy >90% (not measured executed restart savings): count undisturbed agents /
     total agents > 0.90 (scenario above: 1/3 undisturbed is a demo floor;
     current fixture: 21 agents, 2 affected, 19 undisturbed).
  2. Detection latency < 500 ms at demo scale (~500 triples): wall-clock of supplied-graph comparison to drift report; extraction, change detection, and delivery excluded.
  3. Precision: comment-only / formatting-only commits → zero findings.
  4. Correct remediation: all labelled scenarios map to expected levels.
  5. Determinism: 30 repeated runs → identical SHA-256 of sorted verdict
     output.
- DONE CRITERIA: all five green or deviation documented.

## TASK 4.11 — HANDOFF — CONTRACT.md compliance
- Steps: `tests/test_drift_compliance.py`: version/agent-snapshot graph URIs,
  diff query shape, weights, thresholds, and scenario expected values match
  CONTRACT.md §7 exactly.
- TEST GATE: green.
- DONE CRITERIA: pipeline ready for the merged end-to-end run.
