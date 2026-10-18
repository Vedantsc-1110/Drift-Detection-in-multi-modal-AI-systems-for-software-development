---
document_id: S04
title: Fulfillment Escalation Procedure
type: sop
version: 1.0
date: 2026-02-05
author: Fulfillment Operations Team
department: Fulfillment Operations
related_documents: [R03, P05, D03]
related_ofbiz_components: [order, datamodel]
purpose: Fulfillment delays, drop-ship and inventory escalation.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Fulfillment Escalation Procedure (S04)

# 1. Purpose
Fulfillment delay, drop-ship, and inventory escalation for R03 under P05 using D03.

# 2. Procedure
Delay over 48 hours (SYNTHETIC threshold): Fulfillment Coordinator reviews the
[OFBiz-existing] OrderItemShipGroup, recomputes totals via [OFBiz-existing]
resetGrandTotal, and assesses drop-ship via [OFBiz-existing]
checkCreateDropShipPurchaseOrders. Inventory doubt: consult the
[OFBiz-reference-out-of-scope] issueImmediatelyFulfilledOrder hand-off log; because
that integration is INTENTIONALLY UNRESOLVED in the current scope, the procedure
requires a manual inventory check and labels any automated claim about issuance as
unverified. Suggestions: MAY use [OFBiz-existing] addSuggestionsToShoppingList;
last-price: MAY use [OFBiz-existing] setUnitPriceAsLastPrice.

# 3. Escalation ladder (SYNTHETIC)
Coordinator → Supply Chain Lead (72h) → Governance (5 days). OFBiz encodes none of
these timers.

# 4. Traceability
S04 operates R03, D03 under P05.

# 5. Quality checks
Every escalation requires group identifier, delay cause, totals-recompute
confirmation, drop-ship assessment, and manual inventory-check sign-off while the
product hand-off is unresolved (SYNTHETIC record).

# 6. Tools and records
Ship-group view, resetGrandTotal log, drop-ship assessment, suggestion and
last-price references. Records retained per operations schedule.

# 7. Stand-down
Escalation stands down when the group ships or converts to drop-ship with owner
sign-off.

# Worked example
Group G-77 for order O-7788 delays 50 hours; coordinator recomputes via resetGrandTotal, assesses drop-ship, performs the manual inventory check (unresolved hand-off), and escalates to the Supply Chain Lead at 72 hours. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **72-hour rung**: Lead escalation point (SYNTHETIC).
- **5-day rung**: Governance escalation point (SYNTHETIC).
- **Sign-off**: Manual inventory check record (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

