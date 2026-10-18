---
document_id: P05
title: Fulfillment and Inventory Control Policy
type: policy
version: 1.0
date: 2026-01-18
author: Supply Chain Governance Team
department: Fulfillment Operations
related_documents: [R03, D03, S04]
related_ofbiz_components: [order, datamodel]
purpose: Inventory issuance and fulfillment escalation controls.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Fulfillment and Inventory Control Policy (P05)

# 1. Purpose and authority
Fulfillment and inventory control policy. Authority: Supply Chain Governance.
Effective 2026-01-18. Constrains R03, D03; operated by S04.

# 2. Controls (SYNTHETIC with one unresolved anchor)
Immediate issuance for completed orders SHOULD route through the
[OFBiz-reference-out-of-scope] issueImmediatelyFulfilledOrder integration (mode
sync per eecas.xml eca[1] action). Because that service is outside the current
extraction scope, compliance CANNOT be verified from the deterministic graph alone;
the reference is INTENTIONALLY UNRESOLVED. All other controls (ship-group release
checks, drop-ship review, escalation timers) are SYNTHETIC policy.

# 3. OFBiz relationship
Ship groups ([OFBiz-existing] OrderItemShipGroup, createOrderItemShipGroup),
totals ([OFBiz-existing] resetGrandTotal), drop-ship assessment ([OFBiz-existing]
checkCreateDropShipPurchaseOrders) are real anchors. Inventory effects are
SYNTHETIC interpretation.

# 4. Traceability
P05 → R03, D03, S04.

# 5. Exceptions
Stock-out emergencies (SYNTHETIC class) allow manual issuance with Supply Chain
Lead approval while the product integration remains unresolved.

# 6. Interaction with cancellation
Issuance MUST NOT proceed for lines with pending P03 cancellation.

# 7. Review
Semi-annual review; timers change only by governance decision.

# Worked example
Order O-7785 completes with needsInventoryIssuance Y; the ECA action is unresolved in scope, so the coordinator runs the manual check, logs sign-off, and escalates at 72 hours when stock is unconfirmed. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **48-hour timer**: Delay escalation trigger (SYNTHETIC).
- **Manual check**: Required while product hand-off unresolved (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

