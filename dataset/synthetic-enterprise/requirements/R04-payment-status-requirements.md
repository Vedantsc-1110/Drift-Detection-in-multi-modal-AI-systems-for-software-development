---
document_id: R04
title: Payment and Order Status Requirements
type: requirements
version: 1.0
date: 2025-11-24
author: Finance Systems Team
department: Finance
related_documents: [D04, P02, S03]
related_ofbiz_components: [order, datamodel]
purpose: Define payment preferences, authorization and order-status transitions.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Payment and Order Status Requirements (R04)

# 1. Purpose and scope
This document defines payment and order-status requirements. Design in D04, policy
in P02, operations in S03.

# 2. Payment preferences
Each order MUST carry at least one payment preference in the [OFBiz-existing]
OrderPaymentPreference base entity. Preference creation SHOULD use the
[OFBiz-existing] createPaymentFromPreference service. Preference status changes MUST
use the [OFBiz-existing] changeOrderPaymentStatus service. Quote-related payment
status propagation SHOULD use the [OFBiz-existing] checkUpdateQuoteStatus service.
All four anchors exist in the current extraction scope.

# 3. Status transitions
Order-level status MUST change through the [OFBiz-existing] changeOrderStatus
service. Payment completion SHOULD trigger [OFBiz-existing] sendOrderCompleteNotification.
These transitions are structural; the business meaning of a status value (e.g. what
"completed" promises to the customer) is SYNTHETIC and defined by Finance, not by OFBiz.

# 4. Authorization linkage
Payment authorization thresholds and dual-control rules come from P02 (SYNTHETIC
policy). The claim "storeOrder guarantees payment authorization" is explicitly
UNSUPPORTED: storeOrder creates order entities; authorization is a separate
SYNTHETIC control. Extractors that infer authorization from order creation alone
are hallucinating.

# 5. Requirements table
| ID | Requirement | OFBiz anchor | Priority |
| R04-01 | Record payment preference per order | OrderPaymentPreference, createPaymentFromPreference | Must |
| R04-02 | Change payment status explicitly | changeOrderPaymentStatus | Must |
| R04-03 | Change order status explicitly | changeOrderStatus | Must |
| R04-04 | Notify on completion | sendOrderCompleteNotification | Should |

# 6. Roles
Actors: Finance Reviewer (authorizes per P02), Customer (pays), Order Operations
(reconciles per S03).

# 7. Traceability
R04 → D04, P02 constrains R04, S03 operates R04.

# 8. Stakeholders and responsibilities
The Finance Reviewer owns authorization per P02; Order Operations owns daily
reconciliation per S03; Customer Service owns status inquiries via findOrders.

# 9. Constraints and dependencies
Payment handling depends on OrderPaymentPreference and OrderStatus entities and on
D04 integration. Authorization thresholds are SYNTHETIC and live only in P02.

# 10. Acceptance criteria
AC-01: every order has at least one payment preference. AC-02: status changes flow
through changeOrderStatus. AC-03: no output claims storeOrder authorizes payment.
AC-04: completion notifications reference sendOrderCompleteNotification.

# Appendix A — Glossary (doc-specific)

- **OrderPaymentPreference**: Per-order payment record (OFBiz-existing).
- **createPaymentFromPreference**: Preference creation service (OFBiz-existing).
- **changeOrderPaymentStatus**: Preference state service (OFBiz-existing).
- **changeOrderStatus**: Order lifecycle service (OFBiz-existing).
- **Dual control**: Two-approver rule above 25,000 (SYNTHETIC).
- **Reconciliation**: Daily S03 matching process (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

