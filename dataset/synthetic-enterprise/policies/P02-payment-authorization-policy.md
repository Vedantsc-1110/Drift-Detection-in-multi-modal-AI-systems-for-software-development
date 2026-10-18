---
document_id: P02
title: Payment Authorization Policy
type: policy
version: 1.0
date: 2026-01-09
author: Governance Board
department: Finance
related_documents: [R04, D04, S03]
related_ofbiz_components: [order, datamodel]
purpose: Payment authorization limits and reconciliation duties.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Payment Authorization Policy (P02)

# 1. Purpose and authority
Payment authorization policy. Authority: Governance Board (Finance). Effective
2026-01-09. Constrains R04, D04; operated by S03.

# 2. Limits (SYNTHETIC)
Single payment preference authorizations above 5,000 require Finance Reviewer
approval; above 25,000 require dual control. Daily reconciliation per S03 is
mandatory. These limits are business policy with no OFBiz source.

# 3. OFBiz relationship
Preferences live in [OFBiz-existing] OrderPaymentPreference; state changes use
[OFBiz-existing] changeOrderPaymentStatus; orders use [OFBiz-existing]
changeOrderStatus; completion uses [OFBiz-existing] sendOrderCompleteNotification.
OFBiz proves the lifecycle exists; P02 proves who may authorize and when.

# 4. Separation of duties
Order creation (storeOrder) and payment authorization are separate duties performed
by different roles. The claim that one implies the other is UNSUPPORTED.

# 5. Traceability
P02 → R04, D04, S03.

# 6. Exceptions and breaches
Emergency authorizations (SYNTHETIC class) require post-hoc dual review within 1
business day. Breaches suspend the authorizer's payment rights pending review
(SYNTHETIC enforcement).

# 7. Interaction with reconciliation
S03 MUST report threshold breaches daily; unresolved breaches block period close
(SYNTHETIC financial control).

# 8. Review
Annual review by Governance Board (Finance); limits change only by board decision.

# Worked example
Preference PAY-991 of 6,200 needs Finance Reviewer approval; preference PAY-992 of 31,000 needs dual control. S03 flags PAY-992 when only one approver is recorded. Limits and preferences are SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **5,000 limit**: Single-approval trigger (SYNTHETIC).
- **25,000 limit**: Dual-control trigger (SYNTHETIC).
- **Period close**: Blocked by unresolved breaches (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

