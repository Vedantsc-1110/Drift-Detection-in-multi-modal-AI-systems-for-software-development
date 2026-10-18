---
document_id: S01
title: Order Processing Standard Operating Procedure
type: sop
version: 1.0
date: 2026-01-25
author: Order Operations Team
department: Order Management Office
related_documents: [R01, R02, P01, P04, D01, D02]
related_ofbiz_components: [order, datamodel]
purpose: Step-by-step order intake, validation and confirmation procedure.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Processing Standard Operating Procedure (S01)

# 1. Purpose
Step-by-step order intake, validation, and confirmation. Operationalizes R01, R02
under P01 and P04 using D01 and D02 services.

# 2. Procedure
Step 1 — Intake: capture partyId, orderItems, currencyUom, and orderTypeId per the
[OFBiz-existing] storeOrder input definition (56 inputs). Step 2 — Validate per
R02 rules (partyId present, items non-empty, currency supported); failures go to
S02 with codes E-201/E-203 (SYNTHETIC). Step 3 — Create via storeOrder; record
orderId and statusId outputs. Step 4 — Attach contacts via [OFBiz-existing]
createOrderContactMech respecting P04 visibility. Step 5 — Confirm via
[OFBiz-existing] sendOrderConfirmation. Step 6 — Release only after P01 approvals;
advance via [OFBiz-existing] changeOrderStatus.

# 3. Roles and timing (SYNTHETIC)
Customer Service Representative performs steps 1–5 within 4 business hours of
intake; Order Approver completes step 6 within 1 business day for orders under
10,000. Timing targets are operational policy, not OFBiz behavior.

# 4. Systems used
storeOrder, createOrderContactMech, sendOrderConfirmation, changeOrderStatus,
findOrders (lookup), createOrderHeader (header fix-ups). All [OFBiz-existing].

# 5. Traceability
S01 operates R01, R02, D01, D02 under P01, P04.

# 7. Quality checks
Every processed order is checked for header/item persistence, contact attachment,
confirmation attempt, and approval gating before shift handover (SYNTHETIC quality
gate). Failures recycle to the responsible step, never forward.

# 8. Tools and records
Operators use findOrders lookup, the storeOrder output record (orderId, statusId),
and the P04-filtered contact view. Records retained per P04.

# 9. Hand-off
Released orders hand to Fulfillment with approval reference; unreleased orders
remain in the approval queue with owner and due time (SYNTHETIC routing).

# Worked example
Intake ticket T-501 (partyId C-1042, two lines, USD) validates clean, creates order O-7786 with statusId output, attaches contact, sends confirmation, and queues for approval (12,400, so approver required). Ticket T-502 missing partyId fails E-201 to S02. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **4-hour target**: Intake-to-create target (SYNTHETIC).
- **1-day target**: Approval target under 10,000 (SYNTHETIC).
- **Quality gate**: Handover completeness check (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

