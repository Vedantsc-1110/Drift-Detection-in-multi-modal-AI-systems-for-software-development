---
document_id: P01
title: Order Approval Policy
type: policy
version: 1.0
date: 2026-01-06
author: Governance Board
department: Governance
related_documents: [R01, R02, D01, S01]
related_ofbiz_components: [order, datamodel]
purpose: Approval thresholds and roles for order release.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Approval Policy (P01)

# 1. Purpose and authority
Order approval policy. Authority: Governance Board. Effective 2026-01-06.
Constrains R01, R02, D01; operated by S01.

# 2. Thresholds (SYNTHETIC — no OFBiz source)
Orders at or above 10,000 (order currency) require Order Approver release before
fulfillment hand-off. Orders at or above 50,000 require dual approval (Order
Approver plus Finance Reviewer). Below 10,000, the Customer Service Representative
may release directly. These thresholds are business policy; OFBiz services do not
encode them.

# 3. Roles (SYNTHETIC)
Customer Service Representative (capture, correct), Order Approver (release),
Finance Reviewer (dual approval), Fulfillment Coordinator (receives released
orders). Role names are fictional and carry no personal data.

# 4. OFBiz relationship
Approvals gate the outputs of [OFBiz-existing] storeOrder (orderId, statusId)
before [OFBiz-existing] changeOrderStatus advances the order. The gating workflow
is SYNTHETIC; the services are real. Extractors must classify "P01 approval
required before fulfillment" as SYNTHETIC BUSINESS INFORMATION with INDIRECT
service anchors, not as DIRECTLY SUPPORTED by OFBiz.

# 5. Enforcement and audit
S01 records the approver identity and timestamp per order (SYNTHETIC audit
requirement). OFBiz OrderStatus history MAY store the resulting state; the policy
does not claim OFBiz enforces the threshold automatically.

# 6. Traceability
P01 → R01, R02, D01, S01.

# 7. Exceptions to approval
System-generated correction orders below 1,000 (SYNTHETIC class) MAY proceed with
post-hoc approval within 2 business days. All other orders follow the thresholds.
Exception usage is audited quarterly (SYNTHETIC governance).

# 8. Interaction with cancellation
Approvals lapse if the order is cancelled under P03 before release; re-release
requires fresh approval. This interaction is SYNTHETIC workflow logic.

# 9. Review
This policy is reviewed annually by the Governance Board; thresholds change only by
board decision, never by system inference.

# Worked example
Order O-7782 totals 12,400 and requires Order Approver release; order O-7783 totals 61,000 and requires dual approval. Both gates apply to storeOrder outputs before changeOrderStatus. A 640 correction order proceeds with post-hoc approval. Thresholds and orders are SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **10,000 threshold**: Single-approval trigger (SYNTHETIC).
- **50,000 threshold**: Dual-approval trigger (SYNTHETIC).
- **Order Approver**: Release role (SYNTHETIC).
- **Post-hoc approval**: Sub-1,000 correction class (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

