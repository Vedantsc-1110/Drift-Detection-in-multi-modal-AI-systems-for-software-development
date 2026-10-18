---
document_id: S05
title: Order Management Architecture Decision Record
type: sop
version: 1.0
date: 2026-02-10
author: Enterprise Architecture Team
department: Architecture
related_documents: [R01, D01, D02, D03, D04, D05]
related_ofbiz_components: [order, datamodel]
purpose: Architecture decisions for OFBiz-based order management.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Management Architecture Decision Record (S05)

# 1. Purpose and status
Architecture Decision Record for OFBiz-based order management. Decided 2026-02-10
by the Enterprise Architecture Team. Context: R01; alternatives considered below.

# 2. Decisions
ADR-01: Use [OFBiz-existing] storeOrder as the single order-creation entry point
(because its 56-input definition already covers parties, items, adjustments, and
currency) rather than a SYNTHETIC bespoke creation service. ADR-02: Keep payment
authorization (P02) separate from order creation; rejected the alternative "creation
implies authorization" as UNSUPPORTED by OFBiz. ADR-03: Model shipment with
[OFBiz-existing] OrderItemShipGroup and associations via [OFBiz-existing]
OrderItemAssoc (rejected a SYNTHETIC custom shipment entity). ADR-04: Treat the
[OFBiz-reference-out-of-scope] issueImmediatelyFulfilledOrder ECA action as an
unresolved integration point (documented in R03, D03, P05, S04) rather than
pretending it is resolved. ADR-05: No [SYNTHETIC] OrderRiskScore entity in this
release; deferred. There is no OFBiz createOrderItem service (verified absent);
designs use appendOrderItem and createOrderItemGroup instead.

# 3. Consequences
Deterministic extraction covers the structural footprint (services, entities,
relations, ECAs, provenance, unresolved). Business meaning (approvals, thresholds,
timers, "confirmed" and "fulfilled" senses) remains SYNTHETIC and is the target of
the future probabilistic layer.

# 4. Traceability
S05 justifies D01–D05 against R01 and records the above five decisions.

# 5. Alternatives rejected
A bespoke creation service was rejected (duplicates storeOrder's 56-input cover).
Creation-implies-authorization was rejected as UNSUPPORTED. A custom shipment
entity was rejected (OrderItemShipGroup suffices). Pretending the product hand-off
is resolved was rejected (kept unresolved). An OrderRiskScore entity was deferred.

# 6. Verification of decisions
Each ADR cites R-, D-, P-, and S-IDs plus OFBiz anchors; unresolved items carry
explicit UNRESOLVED labels; nonexistent items (createOrderItem, OrderRiskScore)
carry explicit absence notes for hallucination testing.

# 7. Status
Decided 2026-02-10; amendments require Architecture review.

# Appendix A — Glossary (doc-specific)

- **ADR**: Architecture Decision Record entry (SYNTHETIC).
- **Status Decided**: 2026-02-10 decision state (SYNTHETIC).
- **Hallucination probe**: createOrderItem and OrderRiskScore absence notes (UNRESOLVED/SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

