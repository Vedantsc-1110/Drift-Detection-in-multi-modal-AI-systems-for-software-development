---
document_id: P04
title: Customer Data and Access Policy
type: policy
version: 1.0
date: 2026-01-15
author: Data Protection Team
department: Customer Operations
related_documents: [R05, D05, S01]
related_ofbiz_components: [order, datamodel]
purpose: Customer data handling and role-based access.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Customer Data and Access Policy (P04)

# 1. Purpose and authority
Customer data and access policy. Authority: Data Protection Team. Effective
2026-01-15. Constrains R05, D05; operated by S01.

# 2. Rules (SYNTHETIC)
Contact records ([OFBiz-existing] OrderContactMech) are visible only to the owning
customer team and the assigned Customer Service Representative. Bulk export requires
Data Protection approval. Retention is 7 years after last order activity. Consent
for marketing use is opt-in and recorded per contact mechanism. None of these rules
have an OFBiz source; they are pure business policy.

# 3. OFBiz relationship
Structures (OrderRole, OrderStatus, OrderContactMech, CommunicationEventOrder,
CustRequest, ShoppingList) are [OFBiz-existing]; access constraints are SYNTHETIC.
Extractors must not claim OFBiz enforces P04 visibility.

# 4. Traceability
P04 → R05, D05, S01.

# 5. Exceptions
Fraud-investigation access (SYNTHETIC class) MAY override standard visibility with
dual approval and full audit. Marketing use ALWAYS requires opt-in consent.

# 6. Retention and disposal
7-year retention after last activity; secure deletion afterwards (SYNTHETIC rules).
OFBiz provides no retention automation in the current scope.

# 7. Review
Annual review by the Data Protection Team.

# Worked example
Representative R-21 views the contact for her assigned order; representative R-22 from another team is denied. Bulk export of 2,000 contacts needs Data Protection approval. Retention clock starts at last order activity plus 7 years. Scenario is SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **Visibility rule**: Team plus assignee only (SYNTHETIC).
- **7-year retention**: Post-activity retention (SYNTHETIC).
- **Opt-in consent**: Marketing precondition (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

