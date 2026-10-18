# Context Ontology v0.4 (deterministic prototype)

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

Schema: `ontology/context-ontology.ttl` (RDF/OWL, Turtle). Namespace `ofbiz: = http://example.org/ofbiz/0.1/`
(placeholder — replace with the research namespace before publication).
Provenance aligns with PROV-O: `definedIn` / `hasSourceArtifact` are sub-properties of `prov:wasDerivedFrom`;
`SourceArtifact` is a `prov:Entity`.

Rule: **no individual or triple without evidence.** `definedIn` is required on everything except
`SourceArtifact`; `extractionType` is `direct` or `inferred`, nothing else.

## Classes (all justified by OFBiz constructs)

| Class | OFBiz evidence | Notes |
|---|---|---|
| Application | Dataset root + `VERSION` (24.09.07) | Scoping root for one extracted graph version |
| Component | `component-load.xml` `<load-component>` + `ofbiz-component.xml` | e.g. `order`, `datamodel` |
| Service | `servicedef/services*.xml` `<service>` (468 in order scope) | |
| Entity | `*-entitymodel.xml` `<entity>` (112 for order, in `datamodel/`) | |
| ViewEntity ⊂ Entity | `<view-entity>` (53 in `order/entitydef/`) — **added**: distinct construct (member-entities/aliases/view-links, no stored fields) | |
| Method | `location`+`invoke` joined to `src/**.java`, `src/**.groovy`, `minilang/**/ *.xml` simple-methods | Binding stated in service XML; existence validated |
| Attribute | Entity `<field>`, service `<attribute>/<override>`, view `<alias>` — one class, `role` = `entity-field\|service-parameter\|view-alias` | Avoids a Field/Param class split with no behavioural difference at this layer |
| ECA + EntityECA / ServiceECA | `entitydef/eecas.xml` (3, `entity-eca.xsd`) and `servicedef/secas.xml` (108, `service-eca.xsd`) — **subclasses added**: two distinct XSDs | |
| Relation | `<relation>` inside entities (428 in order model) — **added**: reified so `type/fk-name/key-maps` are lossless; a bare triple cannot carry them | |
| Condition | `<condition field-name operator value>`; minilang `if-*`/`compare` later | Syntax verbatim, never interpreted |
| SourceArtifact | Any scanned repo file (`filePath` + `sha256`) | Provenance anchor |

## Relationships

| Relationship | Meaning | OFBiz source field(s) | Direct / Inference | Provenance attached |
|---|---|---|---|---|
| containsComponent (Application→Component) | App ships the component | `component-load.xml` `<load-component component-location>` + component dir | Direct | Both files as artifacts |
| containsService (Component→Service) | Component declares the service | `ofbiz-component.xml` `<service-resource location>` + `<service name>` in that file | Direct | Component XML + services file (+lines) |
| containsEntity (Component→Entity) | Component **defines** the entity | `<entity-resource type="model" location>` + `<entity entity-name>` in that file. View member-refs do NOT count | Direct under this rule | Entity file (+line); defining file only |
| belongsToComponent (Service\|Entity→Component) | Inverse view of the two above | Same as containsService/containsEntity | Direct | Same |
| implementedBy (Service→Method) | Service names its code entry point | `engine` + `location` + `invoke`; target: java `Class#method`, groovy function, `simple-method method-name` | Direct (stated). **Absent by design** for `entity-auto`/`group`/`interface` | Services file (+line); code file (+line) |
| hasInput (Service→Attribute) | Declared input | `<attribute mode="IN"/"INOUT">`, `<override>`, `<auto-attributes>` expansion | Direct for explicit; **inferred** for auto-expansion/`implements`-inherited (cite entity/interface file too) | Services file; + entity file when expanded |
| hasOutput (Service→Attribute) | Declared output | `<attribute mode="OUT"/"INOUT">`, inherited via `<implements service>` | Direct for explicit; **inferred** for inherited (cite chain) | Services file; + interface file when inherited |
| operatesOn (Service→Entity) | **Weak**: service names a default entity | `default-entity-name` only | Direct-as-stated; CRUD meaning valid **only** for `entity-auto`. No exclusivity/intent claims | Services file (+line) |
| hasCondition (ECA→Condition) | ECA guard | `<condition …>` children | Direct | ECA file (+lines) |
| triggersService (ECA→Service) | ECA action fires a service | `<action service mode persist run-as-user>`; mode recorded in `actionMode` | Direct; dangling names reported | ECA file (+line) |
| referencesService (Service→Service) | Stated service→service name ref | `<implements service>`, `<permission-service service-name>`, `<group><invoke name>` | Direct; dangling names reported, never auto-resolved | Services file (+line) |
| triggeredOnEntity (EntityECA→Entity) | What entity op fires the rule | `<eca entity operation event>` → `ecaOperation`/`ecaEvent` | Direct | ECA file (+line) |
| triggeredOnService (ServiceECA→Service) | What service invocation fires the rule | `<eca service event>` → `ecaEvent` | Direct | ECA file (+line) |
| appliesTo (ECA→Entity\|Service) | Super-property of the two trigger links; fires-on target without needing a reasoner | Same as triggeredOnEntity/triggeredOnService | Direct | Same |

Stated-name literals (v0.4, direct, verbatim — present even when the target is
out of scope and no object triple is minted): `triggerEntityName` / `triggerServiceName`
on ECAs, `defaultEntityName` on Services.
| hasAttribute (Entity→Attribute) | Entity field / view alias | `<field>` (+`<prim-key>` → `isPrimaryKey`), `<alias>` | Direct | Entity file (+line) |
| relationFrom / relationTo (Relation→Entity) | Subject/target of a relation | Enclosing `<entity>` / `<relation rel-entity-name>`; `type→relationType`, `fk-name→fkName`, `key-map→keyMap` | Direct; dangling targets reported | Entity file (+line) |
| definedIn (→SourceArtifact, functional, required) | Primary source file | The file containing the stating element | Direct (metadata) | The artifact itself (+`evidenceLine`) |
| hasSourceArtifact (→SourceArtifact, multi) | Supporting evidence | e.g. component XML resource entry; entity file behind an expansion | Direct (metadata) | Each artifact |

## URI minting (stable, deterministic)

- Application: `…/application/apache-ofbiz-24.09.07`
- Component: `…/component/{name}` · Service: `…/service/{name}` (qualify by component on collision)
- Entity: `…/entity/{entity-name}` · Attribute: `…/entity/{E}/field/{F}` or `…/service/{S}/param/{P}`
- Method: `…/method/{dotted-class}#{method}` (file-based for groovy/simple-method)
- ECA/Condition/Relation: `…/eca|condition|relation/{file-hash12}/{index}` (file + document order = stable)

## Statement-level provenance (implementation note)

Individual-level provenance (`definedIn`, `extractionType`, `evidenceLine`) covers *nodes*.
For *edges*, the extractor emits a fact envelope in `facts.jsonl`, and the RDF
builder (`docs/rdf-graph.md`) materializes it as reified `rdf:Statement`
individuals carrying `definedIn`, `extractionType`, `evidenceLine`.

## Validation rules (to enforce in code)

1. Every individual except `SourceArtifact` has exactly one `definedIn` and one `extractionType`.
2. No `implementedBy` where `engine ∈ {entity-auto, group, interface}`.
3. No `operatesOn` without a stated `default-entity-name`.
4. `relationType ∈ {one, many}`; `paramMode ∈ {IN, OUT, INOUT}` or absent (absent ≠ default).
5. `containsEntity` only for entities defined in the component's own model files.
6. Dangling references (unknown service/entity names) are reported, never minted as triples.

## Deferred (evidence exists, schema reserved for v0.2)

- **Endpoint/Screen/Form/Menu** (`controller.xml` request-maps, widget files) — no classes yet; extraction evidence is in `docs/ofbiz-context-extraction.md`.
- Seed/demo data, Java call graphs beyond string literals, transaction/security semantics.
- Anything probabilistic (confidence scores, embeddings, LLM labels) — explicitly out of Part 1.
