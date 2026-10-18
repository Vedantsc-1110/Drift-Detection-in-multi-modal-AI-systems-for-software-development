---
document_id: S02
title: Order Exception Handling Procedure
type: sop
version: 1.0
date: 2026-01-28
author: Order Operations Team
department: Order Management Office
related_documents: [R01, R03, P03, D01]
related_ofbiz_components: [order, datamodel]
purpose: Exception triage, cancellation and return handling.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Exception Handling Procedure (S02)

# 1. Purpose
Exception triage, cancellation, and return handling for R01 and R03 under P03,
using D01 services.

# 2. Triage
Codes: E-201 missing partyId, E-202 empty orderItems, E-203 unsupported currencyUom,
E-301 fulfillment block, E-401 payment mismatch (all SYNTHETIC codes). Each code maps
to a queue, a role, and a time target. OFBiz provides no exception codes; the mapping
is pure operations design.

# 3. Cancellation path
Unreleased lines: cancel via [OFBiz-existing] cancelOrderItem immediately. Released
groups: hold shipment, obtain Order Approver consent per P03, then cancel. Returns:
create via [OFBiz-existing] createReturnHeader. Status: propagate via
[OFBiz-existing] changeOrderStatus.

# 4. Quote interaction
Quote-linked exceptions SHOULD check [OFBiz-existing] checkUpdateQuoteStatus before
cancellation completes. This sequencing is SYNTHETIC.

# 5. Traceability
S02 operates R01, R03, D01 under P03.

# 6. Quality checks
Every exception closure requires a resolution code, an OR-linked orderId or
returnId, and a status verification via changeOrderStatus history (SYNTHETIC
closure rule).

# 7. Tools and records
Triage board, cancelOrderItem forms, createReturnHeader forms, and quote-status
checks. Records retained per P04.

# 8. Escalation from triage
Unresolved E-301 blocks beyond 24 hours escalate per S04 timers (SYNTHETIC).

# Worked example
Exception E-202 on ticket T-502 (empty items) notifies the representative, who corrects and resubmits. Exception E-301 on order O-7787 (fulfillment block) holds the ship group, and after 24 hours escalates per S04. Cancellation of the unreleased line uses cancelOrderItem. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **Resolution code**: Closure identifier (SYNTHETIC).
- **E-301**: Fulfillment block code (SYNTHETIC).
- **E-401**: Payment mismatch code (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

