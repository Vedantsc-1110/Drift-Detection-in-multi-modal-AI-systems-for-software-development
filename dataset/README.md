# Enterprise Context Identification Dataset (v1.0)

## 1. What this dataset contains

Two parts are referenced: (a) Apache OFBiz 24.09.07 (external, read-only source;
**not bundled in this checkout**), and (b) 20 synthetic enterprise documents about a
fictional company, Meridian Retail Group, plus controlled ground truth.

## 2. Why Apache OFBiz is used

OFBiz is a large, real enterprise system with services, entities, relations,
and business rules in machine-readable XML. It gives us honest, verifiable
structure: what exists, how components relate, and where each fact came from.

## 3. Why synthetic documents are included

OFBiz structure alone does not state business meaning (why a service matters,
who approves, what policy constrains it). The synthetic documents provide
controlled business semantics plus ground truth, so we can later test whether
a probabilistic/LLM extractor recovers meaning without hallucinating.

## 4. What the 20 documents represent

5 Requirements (R01–R05: order-to-cash, creation/validation, fulfillment,
payment/status, customer/party), 5 Designs (D01–D05, one per requirement
area), 5 Policies (P01–P05: approval, payment authorization, cancellation,
data access, inventory control), 5 SOPs/Decisions (S01–S04 procedures plus
S05 architecture decision record). Each is DOCX (primary) plus MD (source).

## 5. How documents relate to OFBiz

Documents cite real OFBiz identifiers marked [OFBiz-existing] (verified in the
extraction: storeOrder, sendOrderConfirmation, changeOrderStatus,
createPaymentFromPreference, OrderHeader, OrderItem, …). Concepts outside the
current order plus order-entitymodel.xml scope (e.g.
issueImmediatelyFulfilledOrder in applications/product) are marked
[OFBiz-reference-out-of-scope] and treated as UNRESOLVED. Pure business
inventions (thresholds, timers, roles) are marked [SYNTHETIC].

## 6. What ground truth means

`synthetic-enterprise/ground_truth/fact-mappings.yaml` lists 72 semantic facts.
Each fact states its support: DIRECT (OFBiz proves it), INDIRECT (business
reading anchored on real artifacts), SYNTHETIC (fictional, no OFBiz source),
or UNRESOLVED (references outside scope). Business interpretations are never
presented as DIRECT.

## 7. What negative cases mean

`ground_truth/negative_cases.yaml` lists 18 claims that are false or
unsupported (nonexistent services/entities, wrong keys, fabricated rules).
Each states why it is unsupported and the expected verdict (UNSUPPORTED,
NOT_FOUND, or PARTIALLY_SUPPORTED). They measure hallucination resistance.

## 8. How the dataset will be used

Stage 1 (done): deterministic extraction and evaluation of OFBiz structure.
Stage 2 (planned dataset evaluation; fixture processors now exist): probabilistic extraction over the 20 documents, scored against
ground truth (supported vs hallucinated), without modifying OFBiz or the
deterministic baseline.

## 9. What is real vs synthetic

Real: Apache OFBiz 24.09.07 source and everything deterministically extracted
from it. Synthetic: Meridian Retail Group, all 20 documents, all thresholds,
roles, timers, codes, and business interpretations. Labels in every document
keep the two apart.

## 10. Current limitations

Order plus order-entitymodel.xml scope only (467 services, 112 base entities,
55 views, 567 relations, 111 ECAs); product/party masters unresolved by
design; Java/Groovy bodies unparsed in the historical baseline (a separate contract AST path now exists); live business meaning not yet evaluated;
synthetic docs are controlled, not a substitute for real enterprise text.

## Validation status on 2026-10-17

Corpus structure is present: 20 documents, 72 mapped facts, 18 negatives, and
78 cross-document links. The 20 Markdown distribution copies match their sources.
The validator fails 40 source-path checks without the unbundled OFBiz checkout;
this is not a successful full source validation. Archived counts describe a
previous extraction, not a rerun performed during the UI repair.
