---
document_id: R05
title: Customer and Party Management Requirements
type: requirements
version: 1.0
date: 2025-12-01
author: Customer Domain Team
department: Customer Operations
related_documents: [D05, P04, S01]
related_ofbiz_components: [order, datamodel]
purpose: Define customer roles, contact mechanisms and request handling.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Customer and Party Management Requirements (R05)

# 1. Purpose and scope
This document defines customer and party management requirements. Design in D05,
policy in P04, operations touch S01.

# 2. Party and role model
Customers are represented as parties with roles. Order participation MUST be recorded
in the [OFBiz-existing] OrderRole entity; order status history MUST use the
[OFBiz-existing] OrderStatus entity. Both are base entities in
order-entitymodel.xml. Human workflow requests SHOULD use the [OFBiz-existing]
CustRequest and [OFBiz-existing] createCustRequest / [OFBiz-existing]
createCustRequestItem services. Saved customer assortments MAY use the
[OFBiz-existing] ShoppingList entity.

# 3. Contact mechanisms
Order contact details MUST use the [OFBiz-existing] OrderContactMech entity and the
[OFBiz-existing] createOrderContactMech service. Communication-event linkage MAY use
the [OFBiz-existing] CommunicationEventOrder entity. Contact data handling and
visibility are governed by P04 (SYNTHETIC access rules); OFBiz proves the structures
exist, not who is allowed to see them.

# 4. Quote linkage
Customer quotes SHOULD use the [OFBiz-existing] createQuote service, with status
propagation via [OFBiz-existing] checkUpdateQuoteStatus. The business claim "a quote
automatically becomes an order" is UNSUPPORTED without an explicit conversion
service such as createOrderFromShoppingCart or a documented SYNTHETIC procedure.

# 5. Requirements table
| ID | Requirement | OFBiz anchor | Priority |
| R05-01 | Record order roles | OrderRole | Must |
| R05-02 | Track order status history | OrderStatus | Must |
| R05-03 | Capture customer requests | CustRequest, createCustRequest | Should |
| R05-04 | Manage contact mechanisms | OrderContactMech, createOrderContactMech | Must |

# 6. Ambiguity
"Customer" means (a) the partyId input of storeOrder and (b) a SYNTHETIC commercial
relationship managed by Customer Operations. Extractors must keep the two senses apart.

# 7. Traceability
R05 → D05, P04 constrains R05, S01 uses R05 contact data.

# 8. Stakeholders and responsibilities
Customer Operations owns party data quality; the Data Protection Team owns P04
enforcement; Customer Service owns request intake via CustRequest flows.

# 9. Constraints and dependencies
Party handling depends on OrderRole, OrderStatus, OrderContactMech, and CustRequest
structures. Visibility depends on P04 SYNTHETIC rules. Quote conversion depends on
explicit conversion services, never on assumption.

# 10. Acceptance criteria
AC-01: every order has recorded roles and status history. AC-02: contacts use
OrderContactMech. AC-03: "customer" senses kept distinct. AC-04: no automatic
quote-to-order claim without a conversion anchor.

# Appendix A — Glossary (doc-specific)

- **OrderRole**: Participation record (OFBiz-existing).
- **OrderStatus**: Status history record (OFBiz-existing).
- **CustRequest**: Human request record (OFBiz-existing).
- **OrderContactMech**: Contact record (OFBiz-existing).
- **ShoppingList**: Saved assortment (OFBiz-existing).
- **Customer**: Ambiguous: partyId input vs commercial relationship (see section 6).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

