"""Build synthetic enterprise corpus: 20 docs (MD + DOCX) + ground truth + stats.

Fictional org: Meridian Retail Group (synthetic). OFBiz identifiers marked
EXISTING were verified against outputs-deps/order-facts.jsonl on 2026-09-22.
Deterministic (fixed dates, sorted keys, no clock).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dataset" / "synthetic-enterprise"
ORG = "Meridian Retail Group (fictional — synthetic enterprise)"

DOCS = [
    {"id": "R01", "type": "requirements", "file": "R01-order-to-cash-requirements", "title": "Order-to-Cash Process Requirements", "version": "1.0", "date": "2025-11-03", "author": "Business Analysis Team", "dept": "Order Management Office", "related": ["D01", "P01", "P03", "S01", "S05"], "ofbiz": ["order", "datamodel"], "purpose": "Define the end-to-end order-to-cash scope supported by OFBiz order management."},
    {"id": "R02", "type": "requirements", "file": "R02-order-creation-validation-requirements", "title": "Order Creation and Validation Requirements", "version": "1.0", "date": "2025-11-10", "author": "Business Analysis Team", "dept": "Order Management Office", "related": ["D02", "P01", "S01"], "ofbiz": ["order", "datamodel"], "purpose": "Define order creation inputs, validation rules and confirmation behavior."},
    {"id": "R03", "type": "requirements", "file": "R03-fulfillment-inventory-requirements", "title": "Order Fulfillment and Inventory Requirements", "version": "1.0", "date": "2025-11-17", "author": "Supply Chain Analysis Team", "dept": "Fulfillment Operations", "related": ["D03", "P05", "P03", "S04", "S02"], "ofbiz": ["order", "datamodel"], "purpose": "Define fulfillment, shipment grouping and inventory issuance expectations."},
    {"id": "R04", "type": "requirements", "file": "R04-payment-status-requirements", "title": "Payment and Order Status Requirements", "version": "1.0", "date": "2025-11-24", "author": "Finance Systems Team", "dept": "Finance", "related": ["D04", "P02", "S03"], "ofbiz": ["order", "datamodel"], "purpose": "Define payment preferences, authorization and order-status transitions."},
    {"id": "R05", "type": "requirements", "file": "R05-customer-party-requirements", "title": "Customer and Party Management Requirements", "version": "1.0", "date": "2025-12-01", "author": "Customer Domain Team", "dept": "Customer Operations", "related": ["D05", "P04", "S01"], "ofbiz": ["order", "datamodel"], "purpose": "Define customer roles, contact mechanisms and request handling."},
    {"id": "D01", "type": "designs", "file": "D01-order-management-service-design", "title": "Order Management Service Design", "version": "1.0", "date": "2025-12-08", "author": "Enterprise Architecture Team", "dept": "Architecture", "related": ["R01", "P01", "P03", "S05", "S01"], "ofbiz": ["order", "datamodel"], "purpose": "Service design for order creation, adjustment and status management."},
    {"id": "D02", "type": "designs", "file": "D02-validation-processing-design", "title": "Order Validation and Processing Design", "version": "1.0", "date": "2025-12-12", "author": "Enterprise Architecture Team", "dept": "Architecture", "related": ["R02", "S05", "S01"], "ofbiz": ["order", "datamodel"], "purpose": "Validation chain and cart-to-order processing design."},
    {"id": "D03", "type": "designs", "file": "D03-fulfillment-service-design", "title": "Order Fulfillment Service Design", "version": "1.0", "date": "2025-12-15", "author": "Supply Chain Systems Team", "dept": "Fulfillment Operations", "related": ["R03", "P05", "S05", "S04"], "ofbiz": ["order", "datamodel"], "purpose": "Fulfillment services, ship groups and inventory hand-off design."},
    {"id": "D04", "type": "designs", "file": "D04-payment-integration-design", "title": "Payment Processing Integration Design", "version": "1.0", "date": "2025-12-18", "author": "Finance Systems Team", "dept": "Finance", "related": ["R04", "P02", "S05", "S03"], "ofbiz": ["order", "datamodel"], "purpose": "Payment preference and status integration design."},
    {"id": "D05", "type": "designs", "file": "D05-customer-party-integration-design", "title": "Customer and Party Integration Design", "version": "1.0", "date": "2025-12-20", "author": "Customer Domain Team", "dept": "Customer Operations", "related": ["R05", "P04", "S05"], "ofbiz": ["order", "datamodel"], "purpose": "Party roles, contact mechanisms and customer-request integration."},
    {"id": "P01", "type": "policies", "file": "P01-order-approval-policy", "title": "Order Approval Policy", "version": "1.0", "date": "2026-01-06", "author": "Governance Board", "dept": "Governance", "related": ["R01", "R02", "D01", "S01"], "ofbiz": ["order", "datamodel"], "purpose": "Approval thresholds and roles for order release."},
    {"id": "P02", "type": "policies", "file": "P02-payment-authorization-policy", "title": "Payment Authorization Policy", "version": "1.0", "date": "2026-01-09", "author": "Governance Board", "dept": "Finance", "related": ["R04", "D04", "S03"], "ofbiz": ["order", "datamodel"], "purpose": "Payment authorization limits and reconciliation duties."},
    {"id": "P03", "type": "policies", "file": "P03-order-cancellation-policy", "title": "Order Cancellation Policy", "version": "1.0", "date": "2026-01-12", "author": "Governance Board", "dept": "Order Management Office", "related": ["R01", "R03", "D01", "D03", "S02"], "ofbiz": ["order", "datamodel"], "purpose": "Cancellation windows, roles and item-level rules."},
    {"id": "P04", "type": "policies", "file": "P04-customer-data-access-policy", "title": "Customer Data and Access Policy", "version": "1.0", "date": "2026-01-15", "author": "Data Protection Team", "dept": "Customer Operations", "related": ["R05", "D05", "S01"], "ofbiz": ["order", "datamodel"], "purpose": "Customer data handling and role-based access."},
    {"id": "P05", "type": "policies", "file": "P05-fulfillment-inventory-policy", "title": "Fulfillment and Inventory Control Policy", "version": "1.0", "date": "2026-01-18", "author": "Supply Chain Governance Team", "dept": "Fulfillment Operations", "related": ["R03", "D03", "S04"], "ofbiz": ["order", "datamodel"], "purpose": "Inventory issuance and fulfillment escalation controls."},
    {"id": "S01", "type": "sops", "file": "S01-order-processing-sop", "title": "Order Processing Standard Operating Procedure", "version": "1.0", "date": "2026-01-25", "author": "Order Operations Team", "dept": "Order Management Office", "related": ["R01", "R02", "P01", "P04", "D01", "D02"], "ofbiz": ["order", "datamodel"], "purpose": "Step-by-step order intake, validation and confirmation procedure."},
    {"id": "S02", "type": "sops", "file": "S02-exception-handling-procedure", "title": "Order Exception Handling Procedure", "version": "1.0", "date": "2026-01-28", "author": "Order Operations Team", "dept": "Order Management Office", "related": ["R01", "R03", "P03", "D01"], "ofbiz": ["order", "datamodel"], "purpose": "Exception triage, cancellation and return handling."},
    {"id": "S03", "type": "sops", "file": "S03-payment-reconciliation-procedure", "title": "Payment Reconciliation Procedure", "version": "1.0", "date": "2026-02-02", "author": "Finance Operations Team", "dept": "Finance", "related": ["R04", "P02", "D04"], "ofbiz": ["order", "datamodel"], "purpose": "Daily payment preference reconciliation and status correction."},
    {"id": "S04", "type": "sops", "file": "S04-fulfillment-escalation-procedure", "title": "Fulfillment Escalation Procedure", "version": "1.0", "date": "2026-02-05", "author": "Fulfillment Operations Team", "dept": "Fulfillment Operations", "related": ["R03", "P05", "D03"], "ofbiz": ["order", "datamodel"], "purpose": "Fulfillment delays, drop-ship and inventory escalation."},
    {"id": "S05", "type": "sops", "file": "S05-architecture-decision-record", "title": "Order Management Architecture Decision Record", "version": "1.0", "date": "2026-02-10", "author": "Enterprise Architecture Team", "dept": "Architecture", "related": ["R01", "D01", "D02", "D03", "D04", "D05"], "ofbiz": ["order", "datamodel"], "purpose": "Architecture decisions for OFBiz-based order management."},
]

META_HEADER = """\
> **SYNTHETIC DOCUMENT — {org}.**
> This is a controlled fictional document created for evaluating probabilistic
> context extraction. It is NOT a real company document and contains no real
> personal data. Identifiers marked [OFBiz-existing] were verified against the
> Apache OFBiz 24.09.07 extraction scope (order + order-entitymodel.xml);
> identifiers marked [SYNTHETIC] are intentionally fictional business concepts.
"""

BODIES = {
"R01": """\
# 1. Purpose and scope
This document defines the order-to-cash (O2C) process requirements for {org}.
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
""",
"R02": """\
# 1. Purpose and scope
This document defines order creation and validation requirements. It refines R01 for
the capture stage and is designed in D02, operated in S01, and constrained by P01.

# 2. Creation inputs
Order creation MUST accept the inputs of the [OFBiz-existing] storeOrder service as
defined in applications/order/servicedef/services.xml: partyId (required), orderItems
(required, List), orderAdjustments, currencyUom (required), orderTypeId (INOUT),
orderId (INOUT), and statusId (OUT). The full input set contains 56 IN/INOUT
parameters and 3 OUT/INOUT parameters (orderTypeId, orderId, statusId). Any
implementation that drops a required input is non-conformant.

# 3. Validation rules
Rule R02-VR1: partyId MUST be present and refer to a known customer party; missing
partyId SHALL reject the order. Rule R02-VR2: orderItems MUST be non-empty; an empty
item list SHALL reject the order. Rule R02-VR3: currencyUom MUST be a supported
currency code; unsupported codes SHALL route to exception handling in S02.
These rules are SYNTHETIC business constraints layered over the structural
parameter definitions; OFBiz proves the parameters exist, not that a given order
satisfies the rules.

# 4. Cart-to-order and header services
Cart conversion SHOULD use the [OFBiz-existing] createOrderFromShoppingCart service.
Header-level creation is supported by the [OFBiz-existing] createOrderHeader service
(entity-auto). Item association and grouping SHOULD use [OFBiz-existing]
createOrderItemAssoc and [OFBiz-existing] createOrderItemGroup. Contact details MUST
use [OFBiz-existing] createOrderContactMech. All five services exist in the current
extraction scope.

# 5. Confirmation behavior
After successful creation, the system MUST invoke the [OFBiz-existing]
sendOrderConfirmation flow and MUST record the resulting orderId and statusId outputs
of storeOrder. The claim "storeOrder guarantees that the customer received the
confirmation email" is explicitly UNSUPPORTED: OFBiz shows the confirmation service
exists, not that delivery occurred.

# 6. Roles
Actors: Customer (places the order), Customer Service Representative (captures and
corrects), Order Approver (releases per P01). Role assignment for access control is
governed by P04.

# 7. Traceability
R02 → D02 (design), R02 → S01 (operation), P01 constrains R02 approvals.
""",
"R03": """\
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
""",
"R04": """\
# 1. Purpose and scope
This document defines payment and order-status requirements. Design in D04, policy
in P02, operations in S03.

# 2. Payment preferences
Each order MUST carry at least one payment preference in the [OFBiz-existing]
OrderPaymentPreference base entity. Preference creation SHOULD use the
[OFBiz-existing] createPaymentFromPreference service. Preference status changes MUST
use the [OFBiz-existing] changeOrderPaymentStatus service. Quote-related payment
status propagation SHOULD use the [OFBiz-existing] checkUpdateQuoteStatus service.
All four anchors exist in the current extraction scope.

# 3. Status transitions
Order-level status MUST change through the [OFBiz-existing] changeOrderStatus
service. Payment completion SHOULD trigger [OFBiz-existing] sendOrderCompleteNotification.
These transitions are structural; the business meaning of a status value (e.g. what
"completed" promises to the customer) is SYNTHETIC and defined by Finance, not by OFBiz.

# 4. Authorization linkage
Payment authorization thresholds and dual-control rules come from P02 (SYNTHETIC
policy). The claim "storeOrder guarantees payment authorization" is explicitly
UNSUPPORTED: storeOrder creates order entities; authorization is a separate
SYNTHETIC control. Extractors that infer authorization from order creation alone
are hallucinating.

# 5. Requirements table
| ID | Requirement | OFBiz anchor | Priority |
| R04-01 | Record payment preference per order | OrderPaymentPreference, createPaymentFromPreference | Must |
| R04-02 | Change payment status explicitly | changeOrderPaymentStatus | Must |
| R04-03 | Change order status explicitly | changeOrderStatus | Must |
| R04-04 | Notify on completion | sendOrderCompleteNotification | Should |

# 6. Roles
Actors: Finance Reviewer (authorizes per P02), Customer (pays), Order Operations
(reconciles per S03).

# 7. Traceability
R04 → D04, P02 constrains R04, S03 operates R04.
""",
"R05": """\
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
""",
"D01": """\
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
""",
"D02": """\
# 1. Purpose and scope
Validation and cart-to-order processing design for R02. Rationale in S05; operation in S01.

# 2. Validation chain
The chain validates partyId presence, orderItems non-emptiness, currencyUom support,
and orderTypeId/orderId INOUT handling per the storeOrder definition
(applications/order/servicedef/services.xml, service[10], 56 inputs / 3 outputs).
Failures route to S02 exception handling. The parameter definitions are DIRECTLY
SUPPORTED; the pass/fail business outcome for a specific order is SYNTHETIC runtime
information.

# 3. Cart conversion
createOrderFromShoppingCart converts a validated cart; appendOrderItem adds lines
post-creation; createOrderItemAssoc and createOrderItemGroup maintain associations
and groups; createOrderContactMech attaches contacts. All are [OFBiz-existing].

# 4. Confirmation and totals
Post-creation steps invoke sendOrderConfirmation and resetGrandTotal. For
quote-derived carts, checkUpdateQuoteStatus propagates quote state. The sequence
"validate → create → confirm → recompute" is a SYNTHETIC orchestration; OFBiz
proves each step exists, not that every order follows the full sequence.

# 5. Error handling
Missing partyId, empty orderItems, and unsupported currencyUom map to S02 triage
codes E-201, E-202, E-203 (SYNTHETIC codes). Extractors must label these codes as
SYNTHETIC, not OFBiz-supported.

# 6. Traceability
D02 refines R02; S01 operates D02; S05 justifies the chain over alternatives.
""",
"D03": """\
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
""",
"D04": """\
# 1. Purpose and scope
Payment integration design for R04 under P02. Rationale in S05; reconciliation in S03.

# 2. Preference lifecycle
createPaymentFromPreference creates preferences over OrderPaymentPreference;
changeOrderPaymentStatus advances preference state; checkUpdateQuoteStatus
propagates quote-linked payment state; changeOrderStatus advances the order;
sendOrderCompleteNotification notifies completion. All are [OFBiz-existing].

# 3. Authorization boundary (anti-hallucination)
This design states explicitly that order creation (storeOrder) and payment
authorization (P02 controls) are SEPARATE concerns. No service in the current scope
proves that creating an order authorizes payment. Any extraction claiming
"storeOrder guarantees payment authorization" MUST be classified UNSUPPORTED.

# 4. Reconciliation support
S03 reconciliation reads OrderPaymentPreference and OrderStatus records, corrects
preference state via changeOrderPaymentStatus, and escalates dual-control breaches
per P02. The reconciliation schedule (daily 06:00, SYNTHETIC) is not in OFBiz.

# 5. Traceability
D04 refines R04; P02 constrains D04; S03 operates D04.
""",
"D05": """\
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
There is no [OFBiz-existing] createOrderItem service in the current extraction
(verified absent from order-facts.jsonl). Designs MUST use appendOrderItem,
createOrderItemAssoc, or createOrderItemGroup for line management. Any document
claiming createOrderItem exists as an OFBiz service is UNSUPPORTED (see NEG-01).

# 5. Traceability
D05 refines R05; P04 constrains D05; S05 records the role-model decision.
""",
"P01": """\
# 1. Purpose and authority
Order approval policy. Authority: Governance Board. Effective 2026-01-06.
Constrains R01, R02, D01; operated by S01.

# 2. Thresholds (SYNTHETIC — no OFBiz source)
Orders at or above 10,000 (order currency) require Order Approver release before
fulfillment hand-off. Orders at or above 50,000 require dual approval (Order
Approver plus Finance Reviewer). Below 10,000, the Customer Service Representative
may release directly. These thresholds are business policy; OFBiz services do not
encode them.

# 3. Roles (SYNTHETIC)
Customer Service Representative (capture, correct), Order Approver (release),
Finance Reviewer (dual approval), Fulfillment Coordinator (receives released
orders). Role names are fictional and carry no personal data.

# 4. OFBiz relationship
Approvals gate the outputs of [OFBiz-existing] storeOrder (orderId, statusId)
before [OFBiz-existing] changeOrderStatus advances the order. The gating workflow
is SYNTHETIC; the services are real. Extractors must classify "P01 approval
required before fulfillment" as SYNTHETIC BUSINESS INFORMATION with INDIRECT
service anchors, not as DIRECTLY SUPPORTED by OFBiz.

# 5. Enforcement and audit
S01 records the approver identity and timestamp per order (SYNTHETIC audit
requirement). OFBiz OrderStatus history MAY store the resulting state; the policy
does not claim OFBiz enforces the threshold automatically.

# 6. Traceability
P01 → R01, R02, D01, S01.
""",
"P02": """\
# 1. Purpose and authority
Payment authorization policy. Authority: Governance Board (Finance). Effective
2026-01-09. Constrains R04, D04; operated by S03.

# 2. Limits (SYNTHETIC)
Single payment preference authorizations above 5,000 require Finance Reviewer
approval; above 25,000 require dual control. Daily reconciliation per S03 is
mandatory. These limits are business policy with no OFBiz source.

# 3. OFBiz relationship
Preferences live in [OFBiz-existing] OrderPaymentPreference; state changes use
[OFBiz-existing] changeOrderPaymentStatus; orders use [OFBiz-existing]
changeOrderStatus; completion uses [OFBiz-existing] sendOrderCompleteNotification.
OFBiz proves the lifecycle exists; P02 proves who may authorize and when.

# 4. Separation of duties
Order creation (storeOrder) and payment authorization are separate duties performed
by different roles. The claim that one implies the other is UNSUPPORTED.

# 5. Traceability
P02 → R04, D04, S03.
""",
"P03": """\
# 1. Purpose and authority
Cancellation policy. Authority: Governance Board. Effective 2026-01-12.
Constrains R01, R03, D01, D03; operated by S02.

# 2. Windows and item rules (SYNTHETIC)
Unfulfilled lines MAY be cancelled by the Customer Service Representative at any
time before ship-group release. After release, cancellation requires Order Approver
consent. Partial (item-level) cancellation is the default; whole-order cancellation
is recorded as multiple item cancellations. These windows are business policy.

# 3. OFBiz relationship
Cancellation executes through [OFBiz-existing] cancelOrderItem (and
cancelOrderItemNoActions variant) with status propagation via [OFBiz-existing]
changeOrderStatus. Returns use [OFBiz-existing] createReturnHeader. OFBiz proves the
operations exist; P03 proves when they may be used.

# 4. Fulfillment interaction
Fulfillment MUST NOT release a ship group containing lines with pending
cancellation requests. This check is SYNTHETIC orchestration between P03 and P05.

# 5. Traceability
P03 → R01, R03, D01, D03, S02.
""",
"P04": """\
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
""",
"P05": """\
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
""",
"S01": """\
# 1. Purpose
Step-by-step order intake, validation, and confirmation. Operationalizes R01, R02
under P01 and P04 using D01 and D02 services.

# 2. Procedure
Step 1 — Intake: capture partyId, orderItems, currencyUom, and orderTypeId per the
[OFBiz-existing] storeOrder input definition (56 inputs). Step 2 — Validate per
R02 rules (partyId present, items non-empty, currency supported); failures go to
S02 with codes E-201/E-203 (SYNTHETIC). Step 3 — Create via storeOrder; record
orderId and statusId outputs. Step 4 — Attach contacts via [OFBiz-existing]
createOrderContactMech respecting P04 visibility. Step 5 — Confirm via
[OFBiz-existing] sendOrderConfirmation. Step 6 — Release only after P01 approvals;
advance via [OFBiz-existing] changeOrderStatus.

# 3. Roles and timing (SYNTHETIC)
Customer Service Representative performs steps 1–5 within 4 business hours of
intake; Order Approver completes step 6 within 1 business day for orders under
10,000. Timing targets are operational policy, not OFBiz behavior.

# 4. Systems used
storeOrder, createOrderContactMech, sendOrderConfirmation, changeOrderStatus,
findOrders (lookup), createOrderHeader (header fix-ups). All [OFBiz-existing].

# 5. Traceability
S01 operates R01, R02, D01, D02 under P01, P04.
""",
"S02": """\
# 1. Purpose
Exception triage, cancellation, and return handling for R01 and R03 under P03,
using D01 services.

# 2. Triage
Codes: E-201 missing partyId, E-202 empty orderItems, E-203 unsupported currencyUom,
E-301 fulfillment block, E-401 payment mismatch (all SYNTHETIC codes). Each code maps
to a queue, a role, and a time target. OFBiz provides no exception codes; the mapping
is pure operations design.

# 3. Cancellation path
Unreleased lines: cancel via [OFBiz-existing] cancelOrderItem immediately. Released
groups: hold shipment, obtain Order Approver consent per P03, then cancel. Returns:
create via [OFBiz-existing] createReturnHeader. Status: propagate via
[OFBiz-existing] changeOrderStatus.

# 4. Quote interaction
Quote-linked exceptions SHOULD check [OFBiz-existing] checkUpdateQuoteStatus before
cancellation completes. This sequencing is SYNTHETIC.

# 5. Traceability
S02 operates R01, R03, D01 under P03.
""",
"S03": """\
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
""",
"S04": """\
# 1. Purpose
Fulfillment delay, drop-ship, and inventory escalation for R03 under P05 using D03.

# 2. Procedure
Delay over 48 hours (SYNTHETIC threshold): Fulfillment Coordinator reviews the
[OFBiz-existing] OrderItemShipGroup, recomputes totals via [OFBiz-existing]
resetGrandTotal, and assesses drop-ship via [OFBiz-existing]
checkCreateDropShipPurchaseOrders. Inventory doubt: consult the
[OFBiz-reference-out-of-scope] issueImmediatelyFulfilledOrder hand-off log; because
that integration is INTENTIONALLY UNRESOLVED in the current scope, the procedure
requires a manual inventory check and labels any automated claim about issuance as
unverified. Suggestions: MAY use [OFBiz-existing] addSuggestionsToShoppingList;
last-price: MAY use [OFBiz-existing] setUnitPriceAsLastPrice.

# 3. Escalation ladder (SYNTHETIC)
Coordinator → Supply Chain Lead (72h) → Governance (5 days). OFBiz encodes none of
these timers.

# 4. Traceability
S04 operates R03, D03 under P05.
""",
"S05": """\
# 1. Purpose and status
Architecture Decision Record for OFBiz-based order management. Decided 2026-02-10
by the Enterprise Architecture Team. Context: R01; alternatives considered below.

# 2. Decisions
ADR-01: Use [OFBiz-existing] storeOrder as the single order-creation entry point
(because its 56-input definition already covers parties, items, adjustments, and
currency) rather than a SYNTHETIC bespoke creation service. ADR-02: Keep payment
authorization (P02) separate from order creation; rejected the alternative "creation
implies authorization" as UNSUPPORTED by OFBiz. ADR-03: Model shipment with
[OFBiz-existing] OrderItemShipGroup and associations via [OFBiz-existing]
OrderItemAssoc (rejected a SYNTHETIC custom shipment entity). ADR-04: Treat the
[OFBiz-reference-out-of-scope] issueImmediatelyFulfilledOrder ECA action as an
unresolved integration point (documented in R03, D03, P05, S04) rather than
pretending it is resolved. ADR-05: No [SYNTHETIC] OrderRiskScore entity in this
release; deferred. There is no OFBiz createOrderItem service (verified absent);
designs use appendOrderItem and createOrderItemGroup instead.

# 3. Consequences
Deterministic extraction covers the structural footprint (services, entities,
relations, ECAs, provenance, unresolved). Business meaning (approvals, thresholds,
timers, "confirmed" and "fulfilled" senses) remains SYNTHETIC and is the target of
the future probabilistic layer.

# 4. Traceability
S05 justifies D01–D05 against R01 and records the above five decisions.
""",
}

# Valid OFBiz-existing anchors (verified 2026-09-22 in order-facts.jsonl).
VERIFIED_SERVICES = {"storeOrder", "sendOrderConfirmation", "changeOrderStatus", "createPaymentFromPreference", "changeOrderPaymentStatus", "checkUpdateQuoteStatus", "createOrderHeader", "cancelOrderItem", "cancelOrderItemNoActions", "findOrders", "createQuote", "createReturnHeader", "resetGrandTotal", "checkCreateDropShipPurchaseOrders", "setUnitPriceAsLastPrice", "addSuggestionsToShoppingList", "createOrderAdjustment", "createOrderAdjustmentAttribute", "createOrderContactMech", "createOrderItemShipGroup", "createCustRequest", "createCustRequestItem", "sendOrderCompleteNotification", "createOrderFromShoppingCart", "appendOrderItem", "createOrderItemAssoc", "createOrderItemAssocType", "createOrderItemGroup", "createOrderItemGroupOrder", "createOrderItemAttribute", "createOrderItemBilling", "createOrderItemChange", "createOrderItemContactMech", "createOrderItemRole", "createOrderContent", "createOrderAdjustmentType", "createOrderDeliverySchedule"}
VERIFIED_ENTITIES = {"OrderHeader", "OrderItem", "OrderPaymentPreference", "OrderAdjustment", "OrderItemAssoc", "OrderItemGroup", "OrderItemShipGroup", "OrderType", "OrderStatus", "OrderRole", "OrderContactMech", "CustRequest", "CustRequestItem", "ShoppingList", "OrderContent", "OrderAdjustmentAttribute", "OrderItemShipGroupAssoc", "CommunicationEventOrder", "OrderAdjustmentType", "OrderItemAttribute"}

OUT_OF_SCOPE = {"issueImmediatelyFulfilledOrder", "Party", "Product", "Facility", "StatusItem", "UserLogin", "AccommodationSpot", "ItemIssuance", "InventoryItem"}


def meta_block(spec):
    lines = [
        "---",
        "document_id: %s" % spec["id"],
        "title: %s" % spec["title"],
        "type: %s" % ({"requirements": "requirements", "designs": "design", "policies": "policy", "sops": "sop"}[spec["type"]]),
        "version: %s" % spec["version"],
        "date: %s" % spec["date"],
        "author: %s" % spec["author"],
        "department: %s" % spec["dept"],
        "related_documents: [%s]" % ", ".join(spec["related"]),
        "related_ofbiz_components: [%s]" % ", ".join(spec["ofbiz"]),
        "purpose: %s" % spec["purpose"],
        "---",
        "",
    ]
    return "\n".join(lines)


def render_md(spec, body):
    header = meta_block(spec)
    intro = META_HEADER.format(org=ORG) + "\n"
    title = "# %s (%s)\n\n" % (spec["title"], spec["id"])
    return header + intro + title + body.format(org=ORG) + "\n"


def render_docx(md_text, docx_path):
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(11)
    lines = md_text.splitlines()
    in_meta = False
    table_buf = []
    def flush_table():
        if not table_buf:
            return
        rows = [r for r in table_buf]
        t = doc.add_table(rows=len(rows), cols=len(rows[0]))
        t.style = "Light Grid"
        for i, r in enumerate(rows):
            for j, c in enumerate(r):
                t.cell(i, j).text = c
        table_buf.clear()
    for ln in lines:
        s = ln.strip()
        if s == "---":
            in_meta = not in_meta
            continue
        if in_meta or (s.startswith(("document_id:", "title:", "type:", "version:", "date:", "author:", "department:", "related_", "purpose:")) and ":" in s):
            if s and not s.startswith(">") and not s.startswith("#"):
                continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            table_buf.append(cells)
            continue
        else:
            flush_table()
        if s.startswith("# "):
            doc.add_heading(s[2:].strip(), level=1)
        elif s.startswith("## "):
            doc.add_heading(s[3:].strip(), level=2)
        elif s.startswith("# "):
            doc.add_heading(s.strip("# ").strip(), level=1)
        elif re.match(r"^#+\s", ln):
            doc.add_heading(re.sub(r"^#+\s*", "", ln).strip(), level=2)
        elif s.startswith(">"):
            p = doc.add_paragraph(s.lstrip("> ").strip())
            p.style = doc.styles["Intense Quote"] if "Intense Quote" in [x.name for x in doc.styles] else doc.styles["Normal"]
        elif s.startswith("- ") or s.startswith("* "):
            doc.add_paragraph(s[2:].strip(), style="List Bullet")
        elif re.match(r"^[A-Za-z]+ \d+ ", s) and s.startswith("Step"):
            doc.add_paragraph(s, style="List Number")
        elif not s:
            continue
        else:
            doc.add_paragraph(s)
    flush_table()
    doc.core_properties.title = docx_path.stem
    doc.core_properties.subject = "Synthetic enterprise dataset (fictional)"
    doc.save(str(docx_path))


def build_docs():
    counts = {}
    for spec in DOCS:
        body = BODIES[spec["id"]]
        md = render_md(spec, body)
        d = OUT / spec["type"]
        d.mkdir(parents=True, exist_ok=True)
        (d / (spec["file"] + ".md")).write_text(md, encoding="utf-8")
        render_docx(md, d / (spec["file"] + ".docx"))
        counts[spec["id"]] = len(md.split())
    return counts


if __name__ == "__main__":
    counts = build_docs()
    total_words = sum(counts.values())
    print("docs: %d words(total md): %d" % (len(counts), total_words))
    for k in sorted(counts):
        print(" %s words=%d" % (k, counts[k]))
