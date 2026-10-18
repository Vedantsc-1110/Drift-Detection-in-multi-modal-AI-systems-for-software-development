---
document_id: D05
title: Customer and Party Integration Design
type: design
version: 1.0
date: 2025-12-20
author: Customer Domain Team
department: Customer Operations
related_documents: [R05, P04, S05]
related_ofbiz_components: [order, datamodel]
purpose: Party roles, contact mechanisms and customer-request integration.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Customer and Party Integration Design (D05)

# 1. Purpose and scope
Customer and party integration design for R05 under P04. Rationale in S05.

# 2. Role and contact design
OrderRole records participation; OrderStatus records history; OrderContactMech plus
createOrderContactMech manage contacts; CommunicationEventOrder links
communications; CustRequest with createCustRequest and createCustRequestItem manages
human requests; ShoppingList holds saved assortments; createQuote plus
checkUpdateQuoteStatus manage quotes. All anchors are [OFBiz-existing] base
entities or services in scope.

# 3. Access boundary
P04 access rules (role-based visibility, retention, consent) are SYNTHETIC policy
overlaid on real structures. OFBiz proves OrderContactMech exists; it does not prove
who may read a given contact record.

# 4. Deliberate non-claim
There is no \createOrderItem\ service (verified absent — NOT an OFBiz service) in the current extraction
(verified absent from order-facts.jsonl). Designs MUST use appendOrderItem,
createOrderItemAssoc, or createOrderItemGroup for line management. Any document
claiming createOrderItem exists as an OFBiz service is UNSUPPORTED (see NEG-01).

# 5. Traceability
D05 refines R05; P04 constrains D05; S05 records the role-model decision.

# 8. Non-functional considerations
Contact writes MUST respect P04 visibility at read time (SYNTHETIC enforcement
point). Request queues MUST prioritize blocking order issues over general inquiries
(SYNTHETIC prioritization).

# 9. Dependency map
createCustRequest → createCustRequestItem (request decomposition); createQuote →
checkUpdateQuoteStatus (quote lineage); createOrderContactMech → CommunicationEventOrder
(communication linkage). Roles and status are recorded alongside each step.

# 10. Verification
Verify role/contact/request anchors exist and that createOrderItem is correctly
absent (use appendOrderItem instead).

# Worked example
Customer C-1042 places an order as partyId; participation recorded in OrderRole, history in OrderStatus, phone in OrderContactMech via createOrderContactMech, and a delivery question as CustRequest via createCustRequest. A quote converts only through an explicit conversion step, never automatically. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **Prioritization**: Blocking issues before general inquiries (SYNTHETIC).
- **createOrderItem**: Not an OFBiz service in scope (verified absent).
- **appendOrderItem**: Correct line service (OFBiz-existing).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

