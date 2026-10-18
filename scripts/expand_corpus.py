"""Expand corpus docs to 2-4 page depth with substantive, doc-specific content."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dataset" / "synthetic-enterprise"

EXPAND = {
"R01": """\
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
""",
"R02": """\
# 8. Stakeholders and responsibilities
Customer Service Representatives execute validation; the Order Approver handles
overrides; Finance is consulted on currency disputes. All overrides MUST cite the
orderId and the failed rule (SYNTHETIC audit rule).

# 9. Constraints and dependencies
Validation depends on the storeOrder parameter contract (56 inputs, 3 outputs) and
on D02 chain design. Currency support lists are SYNTHETIC master data. Contact
attachment depends on createOrderContactMech and P04 visibility rules.

# 10. Acceptance criteria
AC-01: missing partyId always rejected with E-201. AC-02: empty orderItems always
rejected with E-202. AC-03: every accepted order yields orderId and statusId outputs.
AC-04: no claim of guaranteed email delivery appears in extraction output.
""",
"R03": """\
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
""",
"R04": """\
# 8. Stakeholders and responsibilities
The Finance Reviewer owns authorization per P02; Order Operations owns daily
reconciliation per S03; Customer Service owns status inquiries via findOrders.

# 9. Constraints and dependencies
Payment handling depends on OrderPaymentPreference and OrderStatus entities and on
D04 integration. Authorization thresholds are SYNTHETIC and live only in P02.

# 10. Acceptance criteria
AC-01: every order has at least one payment preference. AC-02: status changes flow
through changeOrderStatus. AC-03: no output claims storeOrder authorizes payment.
AC-04: completion notifications reference sendOrderCompleteNotification.
""",
"R05": """\
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
""",
"D01": """\
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
""",
"D02": """\
# 8. Non-functional considerations
Validation MUST fail fast on missing partyId before expensive item checks
(SYNTHETIC performance rule). Cart conversion MUST preserve item ordering from the
source cart (SYNTHETIC fidelity rule).

# 9. Dependency map
Validation → storeOrder → sendOrderConfirmation → resetGrandTotal, with a
conditional branch to checkUpdateQuoteStatus for quote carts. Contact attachment
via createOrderContactMech runs in parallel subject to P04.

# 10. Verification
Verify 56-input/3-output contract conformance, E-201/E-203 code mapping to S02,
and that no step claims guaranteed delivery.
""",
"D03": """\
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
""",
"D04": """\
# 8. Non-functional considerations
Preference writes MUST be atomic with order creation records (SYNTHETIC consistency
rule). Reconciliation reads MUST NOT lock order capture (SYNTHETIC isolation rule).

# 9. Dependency map
createPaymentFromPreference → changeOrderPaymentStatus → changeOrderStatus →
sendOrderCompleteNotification, with checkUpdateQuoteStatus as a conditional
quote branch. Authorization checks (P02) gate transitions without adding services.

# 10. Verification
Verify preference lifecycle services exist and that no design element equates
creation with authorization.
""",
"D05": """\
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
""",
"P01": """\
# 7. Exceptions to approval
System-generated correction orders below 1,000 (SYNTHETIC class) MAY proceed with
post-hoc approval within 2 business days. All other orders follow the thresholds.
Exception usage is audited quarterly (SYNTHETIC governance).

# 8. Interaction with cancellation
Approvals lapse if the order is cancelled under P03 before release; re-release
requires fresh approval. This interaction is SYNTHETIC workflow logic.

# 9. Review
This policy is reviewed annually by the Governance Board; thresholds change only by
board decision, never by system inference.
""",
"P02": """\
# 6. Exceptions and breaches
Emergency authorizations (SYNTHETIC class) require post-hoc dual review within 1
business day. Breaches suspend the authorizer's payment rights pending review
(SYNTHETIC enforcement).

# 7. Interaction with reconciliation
S03 MUST report threshold breaches daily; unresolved breaches block period close
(SYNTHETIC financial control).

# 8. Review
Annual review by Governance Board (Finance); limits change only by board decision.
""",
"P03": """\
# 6. Exceptions
Perishable-goods orders (SYNTHETIC class) have a shortened 4-hour cancellation
window after release. Regulatory holds suspend all cancellation until cleared
(SYNTHETIC compliance rule).

# 7. Interaction with fulfillment and returns
Cancelled lines MUST be excluded from ship-group release; fulfilled lines convert
to returns via createReturnHeader rather than cancellation.

# 8. Review
Annual review; windows change only by board decision.
""",
"P04": """\
# 5. Exceptions
Fraud-investigation access (SYNTHETIC class) MAY override standard visibility with
dual approval and full audit. Marketing use ALWAYS requires opt-in consent.

# 6. Retention and disposal
7-year retention after last activity; secure deletion afterwards (SYNTHETIC rules).
OFBiz provides no retention automation in the current scope.

# 7. Review
Annual review by the Data Protection Team.
""",
"P05": """\
# 5. Exceptions
Stock-out emergencies (SYNTHETIC class) allow manual issuance with Supply Chain
Lead approval while the product integration remains unresolved.

# 6. Interaction with cancellation
Issuance MUST NOT proceed for lines with pending P03 cancellation.

# 7. Review
Semi-annual review; timers change only by governance decision.
""",
"S01": """\
# 7. Quality checks
Every processed order is checked for header/item persistence, contact attachment,
confirmation attempt, and approval gating before shift handover (SYNTHETIC quality
gate). Failures recycle to the responsible step, never forward.

# 8. Tools and records
Operators use findOrders lookup, the storeOrder output record (orderId, statusId),
and the P04-filtered contact view. Records retained per P04.

# 9. Hand-off
Released orders hand to Fulfillment with approval reference; unreleased orders
remain in the approval queue with owner and due time (SYNTHETIC routing).
""",
"S02": """\
# 6. Quality checks
Every exception closure requires a resolution code, an OR-linked orderId or
returnId, and a status verification via changeOrderStatus history (SYNTHETIC
closure rule).

# 7. Tools and records
Triage board, cancelOrderItem forms, createReturnHeader forms, and quote-status
checks. Records retained per P04.

# 8. Escalation from triage
Unresolved E-301 blocks beyond 24 hours escalate per S04 timers (SYNTHETIC).
""",
"S03": """\
# 5. Quality checks
Every reconciliation batch requires extracted-preference count, matched-status
count, corrected-item list, and breach report (SYNTHETIC batch record).

# 6. Tools and records
Preference extracts, OrderStatus history, changeOrderPaymentStatus log, P02
threshold table. Records retained 7 years (SYNTHETIC).

# 7. Escalation
Unresolved breaches escalate to the Finance Reviewer same-day; period-close blocks
persist until cleared.
""",
"S04": """\
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
""",
"S05": """\
# 5. Alternatives rejected
A bespoke creation service was rejected (duplicates storeOrder's 56-input cover).
Creation-implies-authorization was rejected as UNSUPPORTED. A custom shipment
entity was rejected (OrderItemShipGroup suffices). Pretending the product hand-off
is resolved was rejected (kept unresolved). An OrderRiskScore entity was deferred.

# 6. Verification of decisions
Each ADR cites R-, D-, P-, and S-IDs plus OFBiz anchors; unresolved items carry
explicit UNRESOLVED labels; nonexistent items (createOrderItem, OrderRiskScore)
carry explicit absence notes for hallucination testing.

# 7. Status
Decided 2026-02-10; amendments require Architecture review.
""",
}

def main():
    for doc_id, extra in EXPAND.items():
        spec_type = next(d["type"] for d in __import__("build_synthetic_corpus", fromlist=["DOCS"]).DOCS if d["id"] == doc_id)
        md_path = OUT / spec_type / next(d["file"] for d in __import__("build_synthetic_corpus", fromlist=["DOCS"]).DOCS if d["id"] == doc_id)
        # resolve paths directly
        for d in __import__("build_synthetic_corpus", fromlist=["DOCS"]).DOCS:
            if d["id"] == doc_id:
                md_file = OUT / d["type"] / (d["file"] + ".md")
                docx_file = OUT / d["type"] / (d["file"] + ".docx")
                text = md_file.read_text(encoding="utf-8")
                if "Acceptance criteria" in text or "Alternatives rejected" in text or "Exceptions to approval" in text or "Quality checks" in text or "Non-functional" in text or "Retention and disposal" in text:
                    print("skip (already expanded):", doc_id)
                    continue
                text = text.rstrip() + "\n\n" + extra.format(org="Meridian Retail Group (fictional — synthetic enterprise)")
                md_file.write_text(text, encoding="utf-8")
                from build_synthetic_corpus import render_docx
                render_docx(text, docx_file)
                print("expanded", doc_id, "words=", len(text.split()))

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
