# Part 1 Deterministic Evaluation — Methodology

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

## 1. Research question

Given an unfamiliar enterprise artifact (here: the Apache OFBiz `order`
component), can we automatically construct a machine-readable Context Graph
that represents what exists, how components relate, what the artifacts mean
(structurally), and where each piece of knowledge came from?

This document evaluates the **deterministic baseline only** (Part 1 Context
Identification). It does NOT evaluate business-meaning understanding — that
requires the future probabilistic/LLM layer.

## 2. Dataset

- Apache OFBiz **24.09.07**, read-only under `dataset/apache-ofbiz-24.09.07`.
- Component: `applications/order` (+ `applications/datamodel` dependency files).
- Dataset is never modified; hashes pin every source file.

## 3. Extraction scope

- Default: `applications/order` only.
- Evaluated scope (`--include-dependencies`): plus explicit, reviewable map
  `scanner.COMPONENT_DEPENDENCIES["order"]`:
  - `applications/datamodel/ofbiz-component.xml` (component node)
  - `applications/datamodel/entitydef/order-entitymodel.xml` (112 base entities)
- Dependency files keep their owning component (`datamodel`) for attribution.
- Current measured baseline (outputs-deps): 468 service facts / 467 Service
  nodes (one duplicate definition merges), 112 base + 55 view entities,
  567 relations (301 resolved `relationTo`), 111 ECAs, 386 unresolved,
  10,204 facts, 117,788 triples, 0 SHACL violations.

## 4. Gold-set construction

- `evaluation/questions.yaml`: 15 questions, each grounded by reading the
  actual XML (file + line + XPath recorded). No answers invented from general
  knowledge. Categories: component (2), service (4: description,
  implementation, 56 inputs, 3 outputs for `storeOrder`), data (4: OrderHeader
  base existence, PK `[orderId]`, OrderItem base existence, OrderHeader
  relations), ECA (3: behavior, rule identity, action reference),
  provenance/scope (2).
- `evaluation/structural-gold.yaml`: sampled existence set — 10 services,
  10 base entities, 10 relations, 5 ECAs — each with source file/line.
- Semantic facts: DIRECT = directly observed; INFERRED = deterministic join
  with all evidence cited; UNRESOLVED = reference known but target outside
  scope (never minted). INFERRED does NOT mean uncertain/LLM.

## 5. Question-based evaluation

For each question: read definition → execute SPARQL over Oxigraph
(`stores/order-deps`) + facts/manifest/unresolved → retrieve graph answer +
provenance → structured comparison → CORRECT / PARTIAL / INCORRECT /
UNRESOLVED + fact type. No LLM, no string-only matching where structure
exists: entity URI/type, normalized PK/param sets, S/P/O triples, ECA
(entity, operation, event, conditions, action), provenance artifact+location.

## 6. Answer comparison

- Entity existence: URI `…/entity/<Name>` + `rdf:type` (`Entity` vs
  `ViewEntity`, exact triples — no reasoning).
- PKs / inputs / outputs: normalized sets (order/whitespace/URI-insensitive);
  aggressive normalization forbidden.
- Relations: `Relation` nodes + `relationFrom`/`relationTo` triples.
- ECA: trigger literals + `hasCondition` set + `triggersService` edge or
  dangling report.
- Provenance: `definedIn` file + `evidenceLine` + `sourceXPath` +
  `extractionType` + artifact `sha256`.

## 7. Provenance evaluation

Every answer exposes ANSWER / EVIDENCE / FACT TYPE. Evidence: source file,
line/XPath, extractor name/version, method, extraction type. Example:
`storeOrder → org.apache.ofbiz.order.order.OrderServices#createOrder` with
`applications/order/servicedef/services.xml:108 /services/service[10]`,
`direct`. Inferred facts additionally require `hasEvidence` spans.

## 8. Unresolved knowledge handling

If `eecas.xml` action `issueImmediatelyFulfilledOrder` points outside
`order`+`datamodel` (it lives in `applications/product/...`), the correct
result is UNRESOLVED: "source establishes the reference but the definition
is outside scope" — with file:line evidence — never a hallucinated Service
node. Same for cross-component entities (Party/Product/Content/Inventory…).
Q-ECA-001 and Q-ECA-003 are UNRESOLVED by design; Q-SCOPE-001 verifies the
dangling report lists them without minting.

## 9. Structural evaluation

Sampled gold-set existence checks (35 items). Precision = found/total,
recall = found/total on this sample. Labeled explicitly
**"sampled structural gold-set evaluation"** — never claimed as
repository-wide precision/recall.

## 10. Negative controls

`tests/test_part1_evaluation.py`: (1) arbitrary string (`ORDER_COMPLETED`)
creates no `BaseEntity`; (2) external service becomes UNRESOLVED;
(3) view vs base not confused (`OrderHeader` Entity-only,
`OrderHeaderAndItems` ViewEntity-only); (4) wrong provenance file detected;
(5) wrong expected description yields INCORRECT. These prove the harness is
meaningful (it can fail).

## 11. Metrics

- Total / Correct / Partial / Incorrect / Unresolved counts.
- Answer coverage = (CORRECT+PARTIAL)/total.
- Resolved correctness = CORRECT/(CORRECT+PARTIAL+INCORRECT).
- Provenance coverage = with-evidence/total.
- Direct / inferred / unresolved-fact shares (separate, never blended into
  one "accuracy").
- Structural precision/recall (sampled only).
- Current: 15 total; 13 correct, 0 partial, 0 incorrect, 2 unresolved;
  coverage 0.8667; resolved correctness 1.0; provenance 1.0;
  structural 1.0/1.0 (35/35).

## 12. Limitations

- Focused on OFBiz Order + explicit datamodel dependency; no
  full-repository coverage claim.
- Java/Groovy method bodies not parsed; `implementedBy` is source-stated,
  not code-verified.
- Cross-component references (Party/Product/Content/Inventory/…) remain
  unresolved by design.
- Business meaning is outside this baseline evaluation. The newer probabilistic layer exists, but live quality targets remain unproven.
- This demonstrates deterministic structural/context baseline, not complete
  enterprise semantic understanding.

## 13. Reproducibility

- Deterministic: sorted queries/outputs, no clock/random/network/LLM in
  results; `evaluation_hash` = sha256 of normalized results+metrics+structural.
- Run twice → identical hash (verified; see final report).
