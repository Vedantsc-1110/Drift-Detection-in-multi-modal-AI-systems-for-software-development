---
document_id: R03
title: Order Fulfillment and Inventory Requirements
type: requirements
version: 1.0
date: 2025-11-17
author: Supply Chain Analysis Team
department: Fulfillment Operations
related_documents: [D03, P05, P03, S04, S02]
related_ofbiz_components: [order, datamodel]
purpose: Define fulfillment, shipment grouping and inventory issuance expectations.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Fulfillment and Inventory Requirements (R03)

# 1. Purpose and scope
This document defines fulfillment and inventory requirements. Design in D03, policy
in P05, cancellation interaction in P03, operations in S04, exceptions in S02.

# 2. Fulfillment model
Orders are fulfilled through shipment groups. The [OFBiz-existing] OrderItemShipGroup
entity carries the grouping; item-to-group links use [OFBiz-existing] OrderItemAssoc
where appropriate. Ship-group creation SHOULD use the [OFBiz-existing]
createOrderItemShipGroup service. Drop-ship purchase orders SHOULD use the
[OFBiz-existing] checkCreateDropShipPurchaseOrders service. Order totals affected by
fulfillment changes MUST be recomputed via the [OFBiz-existing] resetGrandTotal
service.

# 3. Inventory hand-off and unresolved scope
When an OrderHeader record is created with statusId ORDER_COMPLETED and
needsInventoryIssuance Y, the entity-ECA in applications/order/entitydef/eecas.xml
references an [OFBiz-reference-out-of-scope] issueImmediatelyFulfilledOrder action
(mode sync). That service is defined in applications/product, outside the current
order plus order-entitymodel.xml extraction scope, so its definition is
INTENTIONALLY UNRESOLVED in the deterministic graph (dangling triggersService
report, never a minted node). This document therefore requires that any claim about
the behavior of issueImmediatelyFulfilledOrder be labeled as unresolved until the
product component is extracted.

# 4. Inventory policy linkage
Inventory issuance controls follow P05. Suggested retail replenishment lists MAY use
the [OFBiz-existing] addSuggestionsToShoppingList service. Unit-price maintenance MAY
use the [OFBiz-existing] setUnitPriceAsLastPrice service. Both exist in scope; their
business effect (stock levels, pricing) is SYNTHETIC interpretation.

# 5. Requirements table
| ID | Requirement | OFBiz anchor | Priority |
| R03-01 | Group items for shipment | OrderItemShipGroup, createOrderItemShipGroup | Must |
| R03-02 | Recompute totals after fulfillment change | resetGrandTotal | Must |
| R03-03 | Drop-ship assessment | checkCreateDropShipPurchaseOrders | Should |
| R03-04 | Immediate issuance hand-off | issueImmediatelyFulfilledOrder (UNRESOLVED) | Should |

# 6. Ambiguity
"Fulfilled" is used both for (a) shipment-group completion events and (b) a
SYNTHETIC business milestone "customer considers the order fulfilled". The two
senses must be distinguished by extractors.

# 7. Traceability
R03 → D03, P05 constrains R03, S04 operates R03, P03 interacts on cancellation.

# 8. Stakeholders and responsibilities
The Fulfillment Coordinator owns ship-group planning; the Supply Chain Lead owns
drop-ship decisions; the Inventory Steward (SYNTHETIC role) owns issuance follow-up
for the unresolved issueImmediatelyFulfilledOrder hand-off.

# 9. Constraints and dependencies
Fulfillment depends on OrderItemShipGroup definitions, resetGrandTotal availability,
and P05 controls. The immediate-issuance path is blocked on product-component
extraction and MUST be treated as unresolved until then.

# 10. Acceptance criteria
AC-01: every released group references an existing OrderItemShipGroup record.
AC-02: totals recomputed after fulfillment changes. AC-03: unresolved hand-off
claims labeled as such. AC-04: "fulfilled" senses distinguished.

# Appendix A — Glossary (doc-specific)

- **Ship group**: OrderItemShipGroup grouping (OFBiz-existing).
- **resetGrandTotal**: Totals recomputation service (OFBiz-existing).
- **Drop-ship**: Supplier-direct fulfillment assessed by checkCreateDropShipPurchaseOrders (OFBiz-existing).
- **Immediate issuance**: Unresolved product hand-off via issueImmediatelyFulfilledOrder (OUT-OF-SCOPE).
- **Fulfilled**: Ambiguous: group completion vs business milestone (see section 6).
- **Supply Chain Lead**: Drop-ship decision role (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

