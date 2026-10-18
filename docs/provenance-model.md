# Provenance Model (Part 1, deterministic)

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

Schema: `ontology/context-ontology.ttl` v0.3 (additive over v0.1/v0.2; term IRIs stable).
PROV-O alignment: `SourceArtifact`, `Repository`, `Evidence` ⊂ `prov:Entity`;
`Extractor` ⊂ `prov:SoftwareAgent`; `Extraction` ⊂ `prov:Activity`;
`definedIn`, `hasSourceArtifact`, `hasEvidence`, `quotedFrom` ⊂ `prov:wasDerivedFrom`;
`generatedBy` ⊂ `prov:wasGeneratedBy`. Standard `prov:used` / `prov:wasAssociatedWith`
link runs to artifacts and extractors.

## Answering the six questions

| Question | Answered by |
|---|---|
| Which repository? | `SourceArtifact → fromRepository → Repository` (`repositoryId`, e.g. `apache-ofbiz-24.09.07`; `repositoryPath` records where it was read) |
| Which file? | `definedIn → SourceArtifact` (`filePath` repo-relative + `artifactType`) |
| Which location in the file? | `evidenceLine` (single element) and/or `sourceXPath` (e.g. `/services/service[12]/attribute[1]`); inferred facts additionally carry `hasEvidence → Evidence` spans (`lineStart`/`lineEnd`/`snippet`) |
| Which extractor generated this fact? | `generatedBy → Extraction → (prov:wasAssociatedWith) → Extractor` (`extractorName` + `extractorVersion`, `extractedAt`, `extractionMethod`) |
| Direct or inferred? | `extractionType = "direct"` or `"inferred"`. No third value |
| What evidence supports it? | Primary: `definedIn` artifact (+line/XPath). Supporting: `hasSourceArtifact` artifacts. Inferred: one or more `hasEvidence` spans quoting every source used |

## Minimum preserved fields → ontology terms

| Required item | Term(s) |
|---|---|
| repository identifier | `Repository` + `repositoryId` |
| repository path | `repositoryPath` (audit only, never identity) |
| source file | `SourceArtifact` + `filePath` (repo-relative) |
| source artifact/type | `artifactType` (vocabulary below) + `sha256` pin |
| source location | `evidenceLine`, `sourceXPath`; spans via `Evidence` |
| extractor name/version | `Extractor`: `extractorName`, `extractorVersion` |
| extraction timestamp | `Extraction`: `extractedAt` (UTC `xsd:dateTime`) |
| extraction method | `Extraction`: `extractionMethod` (vocabulary below) |
| confidence (inference only) | **Forbidden in Part 1.** The name `ofbiz:confidence` is reserved for the future probabilistic layer and MUST NOT appear in v0.2 output — not even as 1.0 |
| direct vs inferred | `extractionType`; inferred facts MUST also carry `hasEvidence` |

## Controlled vocabularies (v0.2)

`artifactType`: `component-descriptor | component-loader | entity-model | entity-eca | service-def | service-eca | java-source | groovy-source | minilang | widget-screen | widget-form | widget-menu | controller | properties | labels`.
Assigned mechanically from filename + XML root element.

`extractionMethod` (one primary verb per run): `xml-attribute-read` (element/attribute values) |
`xml-literal-reference` (stated name refs: implements, actions, targets) |
`auto-attributes-expansion` (field-list join service×entity) |
`implements-chain-resolution` (inherited params) |
`code-literal-scan` (quoted string literals in java/groovy) |
`join-validate` (location+invoke ↔ method existence checks).

## Direct facts

A direct fact restates source content verbatim (names, attributes, literal references).
It carries: `definedIn` (functional), `extractionType = "direct"`, `generatedBy`,
`evidenceLine`/`sourceXPath` where available, and NO confidence value.
Example (abbreviated):

```turtle
ofbiz:service/cancelOrderItemNoActions a ofbiz:Service ;
    ofbiz:name "cancelOrderItemNoActions" ; ofbiz:engine "java" ;
    ofbiz:implLocation "org.apache.ofbiz.order.order.OrderServices" ;
    ofbiz:implInvoke "cancelOrderItem" ;
    ofbiz:definedIn ofbiz:source/applications/order/servicedef/services.xml ;
    ofbiz:extractionType "direct" ;
    ofbiz:evidenceLine 42 ;
    ofbiz:generatedBy ofbiz:extraction/2026-09-22T003000Z/service-parser .

ofbiz:source/applications/order/servicedef/services.xml a ofbiz:SourceArtifact ;
    ofbiz:filePath "applications/order/servicedef/services.xml" ;
    ofbiz:artifactType "service-def" ; ofbiz:sha256 "…" ;
    ofbiz:fromRepository ofbiz:repo/apache-ofbiz-24.09.07 .
```

## Inferred facts

An inferred fact is produced ONLY by a deterministic join/expansion whose inputs are all cited.
It carries everything a direct fact has, plus `extractionType = "inferred"` and
**one `hasEvidence` span per source used** (e.g. the `<auto-attributes>` element AND each
entity `<field>` consumed; the `<implements>` element AND the interface's `<attribute>`s).
Counter-example: a service↔entity link with no `default-entity-name`, no ECA, no literal —
that is NOT a licensed inference and must not be minted (report as candidate, or drop).

```turtle
ofbiz:service/createOrderAdjustmentAttribute/param/orderAdjustmentId a ofbiz:Attribute ;
    ofbiz:role "service-parameter" ; ofbiz:paramMode "IN" ;
    ofbiz:extractionType "inferred" ;
    ofbiz:definedIn ofbiz:source/applications/order/servicedef/services_order.xml ;
    ofbiz:hasSourceArtifact ofbiz:source/applications/datamodel/entitydef/order-entitymodel.xml ;
    ofbiz:hasEvidence [ a ofbiz:Evidence ;                      # the auto-attributes directive
        ofbiz:quotedFrom ofbiz:source/applications/order/servicedef/services_order.xml ;
        ofbiz:lineStart 25 ; ofbiz:lineEnd 28 ;
        ofbiz:snippet "<auto-attributes include=\"pk\" mode=\"IN\"/>" ] ,
      [ a ofbiz:Evidence ;                                      # the entity field consumed
        ofbiz:quotedFrom ofbiz:source/applications/datamodel/entitydef/order-entitymodel.xml ;
        ofbiz:lineStart 52 ; ofbiz:lineEnd 52 ;
        ofbiz:snippet "<field name=\"orderAdjustmentId\" type=\"id\"/>" ] ;
    ofbiz:generatedBy ofbiz:extraction/2026-09-22T003000Z/service-parser .
```

## Statement (edge) provenance

Node provenance lives in the graph. Edge provenance lives in the `facts.jsonl` envelope
the extractor emits next to the triples (RDF reification deferred to v0.2+):

```json
{"s": "…/service/storeOrder", "p": "ofbiz:referencesService", "o": "…/service/resetGrandTotal",
 "extractionType": "direct", "method": "xml-literal-reference",
 "sources": [{"file": "applications/order/servicedef/secas.xml", "line": 24, "xpath": "/service-eca/eca[1]/action[1]"}]}
```

Every envelope MUST list ≥1 source; `inferred` envelopes MUST list ≥2 (all inputs).

## Validation rules (provenance)

1. Every individual except the five provenance classes' members has exactly one `definedIn` and one `generatedBy`.
2. `extractionType ∈ {direct, inferred}`; `inferred` ⇒ ≥1 `hasEvidence` (envelope: ≥2 sources).
3. No `ofbiz:confidence` triples anywhere in Part 1 output.
4. Every `SourceArtifact` has `filePath`, `artifactType`, `sha256`, `fromRepository`.
5. Every `Extraction` has `extractedAt`, `extractionMethod`, `prov:wasAssociatedWith` an `Extractor`, and `prov:used` ≥1 artifact.
6. Re-running the same extractor version over byte-identical sources yields identical triples (timestamps live only on `Extraction`, never on domain facts).
