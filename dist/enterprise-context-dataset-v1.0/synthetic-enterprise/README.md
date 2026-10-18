# Synthetic Enterprise Corpus — Meridian Retail Group (fictional)

All 20 documents are SYNTHETIC. They are not real company documents and contain
no real personal data. Authors are team names, dates are fixed fictional dates
(2025-11 through 2026-02).

## Layout

- `requirements/` — R01..R05 (business requirements)
- `designs/` — D01..D05 (service designs)
- `policies/` — P01..P05 (governance policies)
- `sops/` — S01..S05 (procedures + architecture decision record)
- `ground_truth/fact-mappings.yaml` — 72 semantic facts with support types
- `ground_truth/negative_cases.yaml` — 18 hallucination probes

Each document ships as DOCX (primary, readable) plus MD (source). Every document
carries metadata: document_id, title, type, version, date, author,
department, related_documents, related_ofbiz_components, purpose.

## OFBiz linkage convention

- `[OFBiz-existing]` — identifier verified in outputs-deps/order-facts.jsonl
  (order + order-entitymodel.xml scope).
- `[OFBiz-reference-out-of-scope]` — real OFBiz identifier outside the current
  scope (e.g. issueImmediatelyFulfilledOrder in applications/product); the
  deterministic graph reports it as UNRESOLVED, never as a node.
- `[SYNTHETIC]` — fictional business concept with no OFBiz source.

## Cross-document links (explicit IDs)

R01→D01, R02→D02, R03→D03, R04→D04, R05→D05. Policies constrain
requirements/designs (P01→R01/R02/D01, P02→R04/D04, P03→R01/R03/D01/D03,
P04→R05/D05, P05→R03/D03). SOPs operationalize them (S01→R01/R02,
S02→R01/R03, S03→R04, S04→R03, S05→D01..D05).

## Semantic categories A–P

Covered across the corpus and ground truth: A business purpose (GT-063),
B business process (GT-003), C service purpose (GT-001), D entity meaning
(GT-004), E role/actor (GT-046/067), F business rule (GT-012/069),
G approval rule (GT-008/043), H policy constraint (GT-045/068),
I service dependency (GT-018/064), J entity dependency (GT-014/065/066),
K exception handling (GT-055/070), L operational procedure (GT-054/071),
M architecture decision (GT-061/072), N cross-document reference (GT-031/053),
O intentional ambiguity (GT-009/021/030), P unsupported/inferred statement
(GT-015/026/034).

## Difficulty mix

Obvious facts (service/entity existence), multi-document facts (approval gating),
OFBiz-anchored interpretations (process support), reasoning-heavy business rules,
cross-document links, deliberate ambiguities (confirmed/fulfilled/customer), and
unsupported claims (guaranteed authorization/delivery) for hallucination testing.
