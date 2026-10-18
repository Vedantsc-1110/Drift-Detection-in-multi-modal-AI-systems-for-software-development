---
document_id: P03
title: Order Cancellation Policy
type: policy
version: 1.0
date: 2026-01-12
author: Governance Board
department: Order Management Office
related_documents: [R01, R03, D01, D03, S02]
related_ofbiz_components: [order, datamodel]
purpose: Cancellation windows, roles and item-level rules.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Cancellation Policy (P03)

# 1. Purpose and authority
Cancellation policy. Authority: Governance Board. Effective 2026-01-12.
Constrains R01, R03, D01, D03; operated by S02.

# 2. Windows and item rules (SYNTHETIC)
Unfulfilled lines MAY be cancelled by the Customer Service Representative at any
time before ship-group release. After release, cancellation requires Order Approver
consent. Partial (item-level) cancellation is the default; whole-order cancellation
is recorded as multiple item cancellations. These windows are business policy.

# 3. OFBiz relationship
Cancellation executes through [OFBiz-existing] cancelOrderItem (and
cancelOrderItemNoActions variant) with status propagation via [OFBiz-existing]
changeOrderStatus. Returns use [OFBiz-existing] createReturnHeader. OFBiz proves the
operations exist; P03 proves when they may be used.

# 4. Fulfillment interaction
Fulfillment MUST NOT release a ship group containing lines with pending
cancellation requests. This check is SYNTHETIC orchestration between P03 and P05.

# 5. Traceability
P03 → R01, R03, D01, D03, S02.

# 6. Exceptions
Perishable-goods orders (SYNTHETIC class) have a shortened 4-hour cancellation
window after release. Regulatory holds suspend all cancellation until cleared
(SYNTHETIC compliance rule).

# 7. Interaction with fulfillment and returns
Cancelled lines MUST be excluded from ship-group release; fulfilled lines convert
to returns via createReturnHeader rather than cancellation.

# 8. Review
Annual review; windows change only by board decision.

# Worked example
Order O-7784 has two lines; line 1 ships while line 2 is unreleased. Line 2 cancels immediately via cancelOrderItem; line 1, already released, needs approver consent, else converts to a return via createReturnHeader. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **Release**: Ship-group handover point (SYNTHETIC).
- **Item-level default**: Partial cancellation norm (SYNTHETIC).
- **Perishable class**: 4-hour window class (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

