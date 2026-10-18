---
document_id: S03
title: Payment Reconciliation Procedure
type: sop
version: 1.0
date: 2026-02-02
author: Finance Operations Team
department: Finance
related_documents: [R04, P02, D04]
related_ofbiz_components: [order, datamodel]
purpose: Daily payment preference reconciliation and status correction.
---
> **SYNTHETIC DOCUMENT — Meridian Retail Group (fictional — synthetic enterprise).**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.

# Payment Reconciliation Procedure (S03)

# 1. Purpose
Daily payment preference reconciliation for R04 under P02 using D04 integration.

# 2. Procedure (SYNTHETIC schedule: daily 06:00)
Step 1 — Extract all [OFBiz-existing] OrderPaymentPreference records modified in
the last 24 hours. Step 2 — Match each against [OFBiz-existing] OrderStatus
history and the [OFBiz-existing] changeOrderPaymentStatus log. Step 3 — Correct
mismatched preference states via changeOrderPaymentStatus. Step 4 — Escalate
dual-control breaches (over 25,000 without two approvers) to the Finance Reviewer.
Step 5 — Confirm order completion messaging via [OFBiz-existing]
sendOrderCompleteNotification where applicable.

# 3. OFBiz boundary
OFBiz proves preferences, statuses, and transitions exist (createPaymentFromPreference,
changeOrderPaymentStatus, changeOrderStatus). The 06:00 schedule, matching rules,
and escalation thresholds are SYNTHETIC.

# 4. Traceability
S03 operates R04, D04 under P02.

# 5. Quality checks
Every reconciliation batch requires extracted-preference count, matched-status
count, corrected-item list, and breach report (SYNTHETIC batch record).

# 6. Tools and records
Preference extracts, OrderStatus history, changeOrderPaymentStatus log, P02
threshold table. Records retained 7 years (SYNTHETIC).

# 7. Escalation
Unresolved breaches escalate to the Finance Reviewer same-day; period-close blocks
persist until cleared.

# Worked example
Batch B-0602 extracts 214 preferences, matches 211, corrects 2 via changeOrderPaymentStatus, and escalates 1 dual-control breach (31,000, single approver). Period close waits on the breach. Figures are SYNTHETIC.

# Appendix A — Glossary (doc-specific)

- **Batch record**: Extracted/matched/corrected/breach counts (SYNTHETIC).
- **Same-day escalation**: Breach routing rule (SYNTHETIC).

# Appendix B — Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | see metadata | Initial synthetic release for semantic evaluation. No real data. |

# Appendix C — Approval

Owner team sign-off recorded in the fictional governance log (SYNTHETIC). No real signatures.

