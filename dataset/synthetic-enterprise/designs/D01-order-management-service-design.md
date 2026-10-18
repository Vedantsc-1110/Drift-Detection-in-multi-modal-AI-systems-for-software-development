---
document_id: D01
title: Order Management Service Design
type: design
version: 1.0
date: 2025-12-08
author: Enterprise Architecture Team
department: Architecture
related_documents: [R01, P01, P03, S05, S01]
related_ofbiz_components: [order, datamodel]
purpose: Service design for order creation, adjustment and status management.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order Management Service Design (D01)

# 1. Purpose and scope
Service design for order management, refining R01 under constraints P01 (approvals)
and P03 (cancellation). Architecture rationale in S05; operations in S01.

# 2. Service inventory (all [OFBiz-existing] in scope)
Order creation: storeOrder (java, OrderServices#createOrder) is the primary entry
point; createOrderHeader (entity-auto) covers header persistence; createOrderFromShoppingCart
covers cart conversion. Adjustment: createOrderAdjustment and createOrderAdjustmentAttribute
(entity-auto) cover charges and discounts. Status: changeOrderStatus covers lifecycle
transitions. Cancellation: cancelOrderItem and cancelOrderItemNoActions cover item
cancellation. Lookup: findOrders covers search. Each service exists in
applications/order/servicedef with the stated engine and binding.

# 3. Dependencies
storeOrder is followed by sendOrderConfirmation (notification) and, for
quote-derived orders, by checkUpdateQuoteStatus. Totals are maintained by
resetGrandTotal. Drop-ship assessment delegates to checkCreateDropShipPurchaseOrders.
These are stated service-to-service references; dynamic dispatch beyond stated
references is out of scope for deterministic extraction.

# 4. Entity mapping
Services operate on OrderHeader (header), OrderItem (lines), OrderAdjustment
(charges), OrderItemGroup (line groups), OrderItemAssoc (line associations), and
OrderItemShipGroup (shipment grouping). The default-entity-name attribute on
entity-auto services is a stated-only operatesOn link; CRUD exclusivity beyond the
attribute is NOT claimed.

# 5. Approval and cancellation integration
Approvals per P01 gate the release of storeOrder outputs (orderId, statusId) to
fulfillment. Cancellation per P03 routes through cancelOrderItem with item-level
rules. Both integrations are SYNTHETIC workflow logic overlaid on real services.

# 6. Open decisions
Whether to add an [SYNTHETIC] OrderRiskScore entity for fraud screening is deferred
to S05 and does NOT exist in OFBiz; any extractor that reports it as an OFBiz entity
is hallucinating.

# 7. Traceability
D01 refines R01; P01 and P03 constrain D01; S01 and S02 operate D01 services.

# 8. Non-functional considerations
Service calls MUST be idempotent on retry with the same orderId (SYNTHETIC
reliability requirement). Lookup via findOrders MUST complete within the SYNTHETIC
4-second service target for customer-service usability. These targets are not
OFBiz properties.

# 9. Dependency map
storeOrder → sendOrderConfirmation (notification); storeOrder → resetGrandTotal
(totals); storeOrder → checkUpdateQuoteStatus (quote lineage, conditional);
changeOrderStatus → sendOrderCompleteNotification (completion). Each arrow is a
stated SYNTHETIC orchestration over real services.

# 10. Verification
Design verification checks each listed service against order-facts.jsonl presence
and each entity against order-entitymodel.xml. The SYNTHETIC OrderRiskScore entity
MUST be absent from verification — its presence would indicate hallucination.

# Appendix A — Glossary (doc-specific)

- **storeOrder**: Primary creation entry point, 56 inputs (OFBiz-existing).
- **cancelOrderItem**: Item cancellation service (OFBiz-existing).
- **findOrders**: Search service (OFBiz-existing).
- **OrderRiskScore**: Deferred SYNTHETIC entity, absent from OFBiz.
- **Orchestration**: SYNTHETIC service sequencing logic.

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

