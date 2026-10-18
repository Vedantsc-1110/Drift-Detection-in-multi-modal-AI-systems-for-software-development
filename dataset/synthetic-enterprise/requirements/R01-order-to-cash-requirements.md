---
document_id: R01
title: Order-to-Cash Process Requirements
type: requirements
version: 1.0
date: 2025-11-03
author: Business Analysis Team
department: Order Management Office
related_documents: [D01, P01, P03, S01, S05]
related_ofbiz_components: [order, datamodel]
purpose: Define the end-to-end order-to-cash scope supported by OFBiz order management.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Order-to-Cash Process Requirements (R01)

# 1. Purpose and scope
This document defines the order-to-cash (O2C) process requirements for Meridian Retail Group (fictional — synthetic enterprise).
The O2C scope covers order capture, validation, confirmation, fulfillment hand-off,
payment preference handling, and status visibility. The design companion for this
document is D01; operationalization is described in S01; approval and cancellation
constraints come from P01 and P03; architecture rationale is recorded in S05.

# 2. Business process overview
The O2C process begins when a customer request becomes a commercial order and ends
when the order is confirmed, fulfilled, and financially settled. The process owner is
the Order Management Office. Actors include the Customer Service Representative,
the Order Approver, the Fulfillment Coordinator, and the Finance Reviewer.
Each hand-off between these actors must leave an auditable order state.

# 3. System support (OFBiz)
Order capture is supported by the [OFBiz-existing] storeOrder service, which creates
and stores order entities (description: "Creates order entities" in
applications/order/servicedef/services.xml). Order confirmation messaging is supported
by the [OFBiz-existing] sendOrderConfirmation service. Order lookup for customer
service is supported by the [OFBiz-existing] findOrders service. These three services
are the minimum structural footprint of O2C in the current extraction scope
(applications/order plus applications/datamodel/entitydef/order-entitymodel.xml).

# 4. Entity requirements
Every order MUST persist a header record in the [OFBiz-existing] OrderHeader base
entity (primary key orderId) and one or more lines in the [OFBiz-existing] OrderItem
base entity (primary keys orderId plus orderItemSeqId). Price adjustments MUST use
the [OFBiz-existing] OrderAdjustment entity. Grouping of lines for shipment planning
MUST use the [OFBiz-existing] OrderItemShipGroup entity. These four entities are
defined in applications/datamodel/entitydef/order-entitymodel.xml and are directly
supported by the deterministic extraction (112 base entities in scope).

# 5. Requirements table
| ID | Requirement | OFBiz anchor | Priority |
| R01-01 | Capture an order with customer, items, and currency | storeOrder inputs partyId, orderItems, currencyUom | Must |
| R01-02 | Persist header, items, adjustments, ship groups | OrderHeader, OrderItem, OrderAdjustment, OrderItemShipGroup | Must |
| R01-03 | Send confirmation after order creation | sendOrderConfirmation | Must |
| R01-04 | Support cancellation per P03 | cancelOrderItem | Must |
| R01-05 | Support status transitions per R04 | changeOrderStatus | Should |

# 6. Business rules and ambiguity
Rule R01-BR1: an order SHALL NOT be released to fulfillment before required approvals
under P01 are recorded. This approval workflow is a SYNTHETIC business rule; OFBiz
provides the services but does not itself prove that the approval happened.
Deliberate ambiguity (for later semantic evaluation): the phrase "confirmed order" is
used in two senses in this corpus — (a) a notification was sent via
sendOrderConfirmation, and (b) a SYNTHETIC business state meaning the customer
acknowledged receipt. Extractors must not conflate the two without evidence.

# 7. Traceability
R01 is refined by D01, constrained by P01 and P03, operated by S01, and justified
in S05. Cross-document references use explicit IDs throughout.

# 8. Stakeholders and responsibilities
The Customer Service Representative owns intake quality; the Order Approver owns
release decisions under P01; the Fulfillment Coordinator owns ship-group readiness;
the Finance Reviewer owns settlement exceptions. Each role has a named deputy for
absence coverage (SYNTHETIC staffing rule). Hand-off records MUST reference the
orderId output of storeOrder so downstream steps can always re-locate the order via
findOrders.

# 9. Constraints and dependencies
R01 depends on the OFBiz order component plus order-entitymodel.xml being extracted;
without OrderHeader and OrderItem definitions the requirements cannot be verified.
External dependencies deliberately out of scope include product inventory masters and
party masters (INTENTIONALLY UNRESOLVED). Cancellation interactions follow P03 and
use cancelOrderItem; returns use createReturnHeader.

# 10. Acceptance criteria
AC-01: every captured order has a persisted OrderHeader and at least one OrderItem.
AC-02: every released order shows an approval record per P01. AC-03: every confirmed
order has a sendOrderConfirmation attempt logged. AC-04: ambiguous "confirmed" usages
are disambiguated in extraction output. These criteria are SYNTHETIC test conditions.

# Appendix A — Glossary (doc-specific)

- **Order-to-cash**: End-to-end flow from order capture to settlement (SYNTHETIC process scope).
- **storeOrder**: OFBiz service creating order entities (OFBiz-existing).
- **OrderHeader**: Header base entity keyed by orderId (OFBiz-existing).
- **OrderItem**: Line base entity keyed by orderId plus orderItemSeqId (OFBiz-existing).
- **Confirmed order**: Ambiguous: notification sent vs customer acknowledgement (see section 6).
- **Ship group**: Shipment planning group over OrderItemShipGroup (OFBiz-existing).
- **Approval gate**: P01 release control (SYNTHETIC).
- **StatusId**: OUT output of storeOrder carrying order state (OFBiz-existing).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

