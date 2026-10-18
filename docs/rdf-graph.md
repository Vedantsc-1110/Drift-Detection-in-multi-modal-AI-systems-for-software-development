# RDF Context Graph (Turtle)

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

Builder: `src/contextgraph/graph.py` via `python build_graph.py --facts <facts.jsonl> --manifest <manifest.json> --out <graph.ttl>`.
Schema: `ontology/context-ontology.ttl` v0.3. No new dependencies — the writer is
hand-rolled for byte-determinism; `rdflib` is used only by tests to validate.

## Facts → graph mapping

| Facts input | Graph output |
|---|---|
| component / service / entity / view_entity / service_param / entity_field / view_alias / eca / condition / relation | Typed individuals (`ofbiz:Component`, `Service`, `Entity`, `ViewEntity`, `Attribute`, `EntityECA`/`ServiceECA`, `Condition`, `Relation`) with verbatim literal properties |
| service (engine java/groovy/simple + location + invoke) | Synthesized `Method` individual `…/method/{location}#{invoke}` (deduped, direct) + `implementedBy` triple |
| service `default-entity-name` | Verbatim `defaultEntityName` literal on the Service — present even when the Entity is out of scope and no `operatesOn` triple is minted |
| ECA trigger names | Verbatim `triggerEntityName` / `triggerServiceName` literals — present even when trigger targets are out of scope |
| component membership | `containsService` / `belongsToComponent` (and `containsEntity`) for every service/entity of the run's component — single-component runs only, stated, direct |
| edge facts (hasInput/hasOutput/referencesService/triggersService/triggeredOn*/operatesOn/relationTo) | The triple + a reified `rdf:Statement` (`…/statement/{i}`) carrying `definedIn`, `extractionType`, `evidenceLine`; ECA-action mode folded in as `actionMode` |
| trigger edges | Additionally `appliesTo` (super-property), so plain SPARQL finds ECA targets without a reasoner |
| structural links | `hasCondition` (via condition→ECA back-pointer), `hasAttribute` (field→entity, alias→view), `relationFrom` (relation→subject entity) |
| inferred facts | `hasEvidence → Evidence` individuals (`quotedFrom`, line span, verbatim snippet) |
| manifest files | `SourceArtifact` individuals (`filePath`, `sha256`, `artifactType`, `fromRepository`); one deterministic `Extraction` per (version, method) with `extractedAt`, `prov:used`, `prov:wasAssociatedWith` |

Every domain individual carries `definedIn`, `extractionType`, `generatedBy`
(and `evidenceLine`/`sourceXPath` when known). No confidence properties.

## Deliberately kept in facts.jsonl (no ontology class in v0.3)

`resource` / `resource_loader` bindings, `param_override`s, `auto_attributes`
directives, `permission_check`s, `view_member`s, `view_link`s, `eca_action` nodes
(their service link and mode survive via `triggersService` + statement `actionMode`).
Candidates for v0.4 if evidence work needs them as first-class nodes.

## Determinism

IDs derive from repository/path/artifact-name (ECAs/relations/conditions from
file-hash + document order). No timestamps or counters in identifiers;
`extractedAt` is a literal only. Rebuild with `--as-of <timestamp>` for
byte-identical output; the test suite asserts this.
