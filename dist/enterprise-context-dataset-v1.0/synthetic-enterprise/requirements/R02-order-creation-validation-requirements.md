---
document_id: R02
title: Order Creation and Validation Requirements
type: requirements
version: 1.0
date: 2025-11-10
author: Business Analysis Team
department: Order Management Office
related_documents: [D02, P01, S01]
related_ofbiz_components: [order, datamodel]
purpose: Define order creation inputs, validation rules and confirmation behavior.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Creation and Validation Requirements (R02)

# 1. Purpose and scope
This document defines order creation and validation requirements. It refines R01 for
the capture stage and is designed in D02, operated in S01, and constrained by P01.

# 2. Creation inputs
Order creation MUST accept the inputs of the [OFBiz-existing] storeOrder service as
defined in applications/order/servicedef/services.xml: partyId (required), orderItems
(required, List), orderAdjustments, currencyUom (required), orderTypeId (INOUT),
orderId (INOUT), and statusId (OUT). The full input set contains 56 IN/INOUT
parameters and 3 OUT/INOUT parameters (orderTypeId, orderId, statusId). Any
implementation that drops a required input is non-conformant.

# 3. Validation rules
Rule R02-VR1: partyId MUST be present and refer to a known customer party; missing
partyId SHALL reject the order. Rule R02-VR2: orderItems MUST be non-empty; an empty
item list SHALL reject the order. Rule R02-VR3: currencyUom MUST be a supported
currency code; unsupported codes SHALL route to exception handling in S02.
These rules are SYNTHETIC business constraints layered over the structural
parameter definitions; OFBiz proves the parameters exist, not that a given order
satisfies the rules.

# 4. Cart-to-order and header services
Cart conversion SHOULD use the [OFBiz-existing] createOrderFromShoppingCart service.
Header-level creation is supported by the [OFBiz-existing] createOrderHeader service
(entity-auto). Item association and grouping SHOULD use [OFBiz-existing]
createOrderItemAssoc and [OFBiz-existing] createOrderItemGroup. Contact details MUST
use [OFBiz-existing] createOrderContactMech. All five services exist in the current
extraction scope.

# 5. Confirmation behavior
After successful creation, the system MUST invoke the [OFBiz-existing]
sendOrderConfirmation flow and MUST record the resulting orderId and statusId outputs
of storeOrder. The claim "storeOrder guarantees that the customer received the
confirmation email" is explicitly UNSUPPORTED: OFBiz shows the confirmation service
exists, not that delivery occurred.

# 6. Roles
Actors: Customer (places the order), Customer Service Representative (captures and
corrects), Order Approver (releases per P01). Role assignment for access control is
governed by P04.

# 7. Traceability
R02 → D02 (design), R02 → S01 (operation), P01 constrains R02 approvals.

# 8. Stakeholders and responsibilities
Customer Service Representatives execute validation; the Order Approver handles
overrides; Finance is consulted on currency disputes. All overrides MUST cite the
orderId and the failed rule (SYNTHETIC audit rule).

# 9. Constraints and dependencies
Validation depends on the storeOrder parameter contract (56 inputs, 3 outputs) and
on D02 chain design. Currency support lists are SYNTHETIC master data. Contact
attachment depends on createOrderContactMech and P04 visibility rules.

# 10. Acceptance criteria
AC-01: missing partyId always rejected with E-201. AC-02: empty orderItems always
rejected with E-202. AC-03: every accepted order yields orderId and statusId outputs.
AC-04: no claim of guaranteed email delivery appears in extraction output.

# Appendix A — Glossary (doc-specific)

- **partyId**: Required IN input identifying the customer party (OFBiz-existing).
- **orderItems**: Required List input of order lines (OFBiz-existing).
- **currencyUom**: Required currency input (OFBiz-existing).
- **orderId**: INOUT output recorded for downstream steps (OFBiz-existing).
- **E-201**: Missing-partyId triage code (SYNTHETIC).
- **E-202**: Empty-items triage code (SYNTHETIC).
- **E-203**: Unsupported-currency triage code (SYNTHETIC).
- **createOrderHeader**: Header persistence service (OFBiz-existing).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

