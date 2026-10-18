---
document_id: D03
title: Order Fulfillment Service Design
type: design
version: 1.0
date: 2025-12-15
author: Supply Chain Systems Team
department: Fulfillment Operations
related_documents: [R03, P05, S05, S04]
related_ofbiz_components: [order, datamodel]
purpose: Fulfillment services, ship groups and inventory hand-off design.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Fulfillment Service Design (D03)

# 1. Purpose and scope
Fulfillment service design for R03 under P05, with cancellation interaction P03.
Rationale in S05; escalation in S04.

# 2. Ship-group design
createOrderItemShipGroup creates shipment groups over OrderItemShipGroup;
OrderItemAssoc links related lines; OrderItemGroup organizes planning groups.
Totals use resetGrandTotal; drop-ship uses checkCreateDropShipPurchaseOrders;
suggestions use addSuggestionsToShoppingList; last-price maintenance uses
setUnitPriceAsLastPrice. All services and entities are [OFBiz-existing] in scope.

# 3. Inventory hand-off (unresolved)
The OrderHeader create-store ECA (eecas.xml eca[1], conditions statusId
ORDER_COMPLETED and needsInventoryIssuance Y) references
[OFBiz-reference-out-of-scope] issueImmediatelyFulfilledOrder (sync). Because the
target is defined in applications/product (outside order + order-entitymodel.xml),
the deterministic graph reports a dangling triggersService reference and mints no
Service node. This design therefore treats immediate issuance as an
INTENTIONALLY UNRESOLVED integration point pending product-component extraction.

# 4. Cancellation interaction
Fulfillment MUST check P03 cancellation state via cancelOrderItem status before
releasing a ship group. This check is SYNTHETIC orchestration logic.

# 5. Traceability
D03 refines R03; P05 constrains D03; S04 operates D03; S05 records the ship-group
and unresolved hand-off decisions.

# 8. Non-functional considerations
Ship-group planning MUST handle 500-line orders within the SYNTHETIC overnight batch
window. Drop-ship assessment MUST NOT block standard fulfillment beyond the
SYNTHETIC 2-hour review SLA.

# 9. Dependency map
createOrderItemShipGroup → resetGrandTotal → checkCreateDropShipPurchaseOrders,
with an unresolved branch to issueImmediatelyFulfilledOrder (product scope).
Suggestions and last-price services are optional side branches.

# 10. Verification
Verify ship-group entities, totals recomputation, drop-ship availability, and that
the unresolved hand-off is reported dangling rather than edged.

# Worked example
Order O-7781 with three lines splits into two ship groups via createOrderItemShipGroup; totals recomputed via resetGrandTotal; one line flagged for drop-ship via checkCreateDropShipPurchaseOrders. Because the order completed with needsInventoryIssuance Y, the ECA references issueImmediatelyFulfilledOrder, which is unresolved in scope, so the coordinator performs the S04 manual inventory check. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **createOrderItemShipGroup**: Group creation service (OFBiz-existing).
- **Batch window**: Overnight 500-line target (SYNTHETIC).
- **Review SLA**: 2-hour drop-ship review target (SYNTHETIC).
- **Unresolved branch**: Product hand-off pending extraction (UNRESOLVED).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

