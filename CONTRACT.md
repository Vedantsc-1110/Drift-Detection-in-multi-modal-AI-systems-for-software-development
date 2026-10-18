# Shared extraction contract for the enterprise context project

Reviewed 2026-10-17. This contract belongs to the earlier September extraction
brief, whose section references differ from the supplied Revision 2 Word
proposal. It defines the implemented extraction interchange; it is not the
Revision 2 twelve-type agent/specification schema. See
[implementation status](docs/implementation-status.md).

The consolidated project lives at this repository root. Shared Python
helpers are imported within that package. Parts exchange extracted data through
the Turtle files below; Part 4's extraction hook invokes a configured external
command. The earlier prohibition on all cross-part Python imports does not
describe the current merged layout.

## 1. Namespaces / Prefixes

```
@prefix ctx:  <http://context.example.org/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
```

## 2. Ontology Classes (proposal §3.1)

Code-level:      ctx:Module, ctx:Service, ctx:Entity, ctx:Field, ctx:JavaClass,
                 ctx:JavaMethod, ctx:ECA
Workflow-level:  ctx:DAG, ctx:Task, ctx:Workflow, ctx:Job, ctx:Step
Document-level:  ctx:Document, ctx:BusinessConcept, ctx:Policy, ctx:BusinessRule,
                 ctx:Contract, ctx:Clause, ctx:Party,
                 ctx:Filing, ctx:Section, ctx:RiskFactor

## 3. Ontology Properties (proposal §3.1 and extraction sections)

§3.1 declared:   ctx:calls (JavaMethod→JavaMethod),
                 ctx:implementedBy (Service→JavaMethod),
                 ctx:hasField (Entity→Field),
                 ctx:relatesTo (Entity→Entity),
                 ctx:invokesService (Task→Service),
                 ctx:constrains (Policy→Service),
                 ctx:mentionsEntity (Document→Entity),
                 ctx:hasClause (Contract→Clause),
                 ctx:belongsToConcept (Service→BusinessConcept),
                 ctx:referencesModule (Filing→Module),
                 ctx:mentionsProcess (Section→Service)

Used by extractors:
                 ctx:engine, ctx:hasInputParam, ctx:hasOutputParam,
                 ctx:hasParameter, ctx:hasTask, ctx:dependsOn,
                 ctx:scheduledAt, ctx:operatorType, ctx:triggeredBy,
                 ctx:hasStep, ctx:usesAction, ctx:clauseType,
                 ctx:imports, ctx:definedIn, ctx:atLine, ctx:sourceLocation,
                 ctx:sourceHash, ctx:businessPurpose,
                 ctx:confidence, ctx:factType, ctx:extractedBy, ctx:supportType

Provenance (PROV-O): prov:wasGeneratedBy, prov:hadPrimarySource,
                 prov:generatedAtTime

## 4. Named Graphs and Ownership

| Named Graph              | Contents                                    | Writer | Reader |
|--------------------------|---------------------------------------------|--------|--------|
| <urn:ofbiz_structural>   | OFBiz services, entities, classes, methods, calls | Part 1 | Parts 2,3,4 |
| <urn:airflow>            | Airflow DAGs, tasks, dependencies, schedules | Part 1 | Parts 3,4 |
| <urn:cicd>               | CI/CD workflows, jobs, steps, triggers      | Part 1 | Parts 3,4 |
| <urn:ofbiz_semantic>     | OFBiz business purposes, concepts, rules    | Part 2 | Parts 3,4 |
| <urn:document_semantic>  | Document-derived policies, rules, references| Part 2 | Parts 3,4 |
| <urn:cuad>               | Contract clauses, parties, obligations      | Part 2 | Parts 3,4 |
| <urn:edgar>              | Filing sections, risk factors, mentions     | Part 2 | Parts 3,4 |

Bridge edges (proposal §3.4) are written by Part 3, connecting across the graphs
above via the shared `ctx:` vocabulary. Part 4 additionally creates versioned
graphs and agent-snapshot graphs (see §7).

## 5. Fact metadata contract and implementation limits

The fields below are the intended metadata envelope. Most current contract
writers attach them to a subject rather than reifying every assertion. Presence
checks vary: `ContractStore.verify_metadata` requires confidence, factType,
wasGeneratedBy, and hadPrimarySource, but does not enforce all fields below.
Do not infer per-triple evidence coverage from that check. The older baseline
uses another namespace and metadata scheme.

- ctx:confidence     : xsd:decimal. 1.0 for deterministic facts;
                       0.0–1.0 for probabilistic facts.
- ctx:factType       : string, "deterministic" or "probabilistic".
- ctx:extractedBy    : string, e.g. "llama-3.3-70b", "qwen3.5:4b" (probabilistic only).
- ctx:supportType    : DIRECT | INDIRECT | SYNTHETIC | UNRESOLVED
                       (probabilistic document facts only, §2.2).
- prov:wasGeneratedBy: one of ctx:TreeSitterExtractor, ctx:GroqLLMExtractor,
                       (Ollama extractor), (xml.etree extractor), etc.
- prov:hadPrimarySource: source URI, e.g. <file:///ofbiz/accounting/servicedef/services.xml>
- ctx:sourceLocation : "line 142" or "section 3.2" style string.
- ctx:sourceHash     : SHA-256 hex of the source file/content (Part 1, Part 4).
- prov:generatedAtTime: ISO-8601 timestamp, e.g. "2026-09-22T10:30:00Z".

## 6. Output Files

Deterministic (Part 1):  outputs/ofbiz_structural.ttl, outputs/airflow.ttl,
                         outputs/cicd.ttl
Probabilistic (Part 2):  outputs/*_semantic.ttl / cuad.ttl / edgar.ttl
                         (same Turtle format, one file per Named Graph above)
Ontology (Part 3):       ontology .ttl + SHACL shapes .ttl (both authored in .ttl)

All .ttl files are Turtle-serialized RDF, loadable by Oxigraph (pyoxigraph)
via rdflib, and are intermediate artifacts: inspectable, shareable, reloadable.

## 7. Drift-Detection Constants (proposal §7.3 — fixed, do not change)

Severity = Σ (weight × factor_score), range 0.0–1.0:

| Factor                | Weight |
|-----------------------|--------|
| Criticality of affected entity | 0.15 (critical=1.0, high=0.8, normal=0.5, low=0.2) |
| Contract/API breakage | 0.35 (signature break=1.0, additive change=0.3, cosmetic=0.0) |
| Directness (hop dist) | 0.20 (1-hop=1.0, 2-hop=0.5, 3+=0.25) |
| Assumption invalidated| 0.10 (yes=1.0, no=0.0) |
| Constraint violated   | 0.10 (yes=1.0, no=0.0) |
| Conflicting code      | 0.10 (yes=1.0, no=0.0) |

Remediation selection:
- score = 0.0              → CONTINUE (no action)
- 0.0 < score < 0.35       → REFRESH (send updated facts / "context patch")
- 0.35 ≤ score < 0.60      → RE-BRIEF (summary of what changed and why)
- 0.60 ≤ score < 0.85      → RE-PLAN (discard current plan, re-plan)
- score ≥ 0.85             → ROLLBACK (revert to last known-good checkpoint)

Typed impact-traversal path (blast radius):
Symbol →calls→ Symbol →implementedBy→ Service →constrainedBy→ Policy
→mentionedIn→ Contract/Filing →dependsOn→ DAG Task →assignedTo→ Agent/System

Canonical scenario (§7.3): Agent A score 0.725 → RE-PLAN;
Agent B score 0.0 → CONTINUE; Agent C score 0.82 → RE-PLAN.

## 8. Independence and fixtures

Every part ships its own `fixtures/` directory containing small sample inputs and
sample .ttl files that follow this contract, so it can be developed and tested
alone. The consolidated implementation shares package helpers; extracted
artifacts retain the named-graph boundaries described by this contract.

## 9. Decisions and known schema extensions

- Bridge edges are stored in `urn:bridges`, written by Part 3. The seven graphs
  in section 4 remain the extraction source graphs.
- `ctx:relatedTo` is used by document bridge rules but is not formally declared
  in the current contract ontology. `ctx:assignedTo` is followed when supplied
  to traversal but has no complete agent lifecycle/schema here. These are gaps,
  not evidence that the Revision 2 agent ontology exists.
- Agent C's exact fixture score uses high criticality, signature break, 3+-hop
  directness, and assumption/constraint/conflicting flags true: 0.12 + 0.35 +
  0.05 + 0.10 + 0.10 + 0.10 = 0.82. No weights were changed.
- Corroboration is `max(raw, 0.95)` on normalized triple matches; unmatched
  scores clamp to 0.70–0.85. Confidence is not calibrated truth probability.
- Timestamp predicate: `prov:generatedAtTime`. Turtle files contain triples,
  with named graph assignment at load time.
- Fixture graph IDs: `urn:version_n`, `urn:version_n1`, and
  `urn:agent_snapshot_A/B/C`. Stored version history is Turtle plus SQLite;
  comparison named graphs are temporary rdflib datasets.
- Snapshot registration is currently a caller-supplied mapping of agent names
  to graphs. Remediation values are recommendations, not executed actions.
- The implemented levels are the five in section 7. The Word proposal's sixth
  level, RESTART, and its specialized drift-type workflows are still absent.
