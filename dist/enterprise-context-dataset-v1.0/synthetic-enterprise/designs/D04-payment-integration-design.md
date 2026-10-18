---
document_id: D04
title: Payment Processing Integration Design
type: design
version: 1.0
date: 2025-12-18
author: Finance Systems Team
department: Finance
related_documents: [R04, P02, S05, S03]
related_ofbiz_components: [order, datamodel]
purpose: Payment preference and status integration design.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Payment Processing Integration Design (D04)

# 1. Purpose and scope
Payment integration design for R04 under P02. Rationale in S05; reconciliation in S03.

# 2. Preference lifecycle
createPaymentFromPreference creates preferences over OrderPaymentPreference;
changeOrderPaymentStatus advances preference state; checkUpdateQuoteStatus
propagates quote-linked payment state; changeOrderStatus advances the order;
sendOrderCompleteNotification notifies completion. All are [OFBiz-existing].

# 3. Authorization boundary (anti-hallucination)
This design states explicitly that order creation (storeOrder) and payment
authorization (P02 controls) are SEPARATE concerns. No service in the current scope
proves that creating an order authorizes payment. Any extraction claiming
"storeOrder guarantees payment authorization" MUST be classified UNSUPPORTED.

# 4. Reconciliation support
S03 reconciliation reads OrderPaymentPreference and OrderStatus records, corrects
preference state via changeOrderPaymentStatus, and escalates dual-control breaches
per P02. The reconciliation schedule (daily 06:00, SYNTHETIC) is not in OFBiz.

# 5. Traceability
D04 refines R04; P02 constrains D04; S03 operates D04.

# 8. Non-functional considerations
Preference writes MUST be atomic with order creation records (SYNTHETIC consistency
rule). Reconciliation reads MUST NOT lock order capture (SYNTHETIC isolation rule).

# 9. Dependency map
createPaymentFromPreference → changeOrderPaymentStatus → changeOrderStatus →
sendOrderCompleteNotification, with checkUpdateQuoteStatus as a conditional
quote branch. Authorization checks (P02) gate transitions without adding services.

# 10. Verification
Verify preference lifecycle services exist and that no design element equates
creation with authorization.

# Worked example
Order O-7781 carries one OrderPaymentPreference created via createPaymentFromPreference for 12,400, requiring Finance Reviewer approval per P02 (above 5,000, below 25,000). After authorization, changeOrderPaymentStatus advances the preference and changeOrderStatus advances the order; sendOrderCompleteNotification follows. Creation alone never authorized payment. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **Atomicity rule**: Preference plus order records written together (SYNTHETIC).
- **Isolation rule**: Reads never block capture (SYNTHETIC).
- **06:00 schedule**: Daily reconciliation time (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

