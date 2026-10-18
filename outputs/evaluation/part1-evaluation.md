# Part 1 Deterministic Evaluation: Order Context Graph

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.

_Scope: component `order` + explicit dependency `applications/datamodel/entitydef/order-entitymodel.xml`._
_Method: SOURCE/GOLD (dataset XML) -> EXPECTED CONTEXT -> CONTEXT GRAPH ANSWER (Oxigraph SPARQL). No LLM._

## Metrics
- Total questions: 15
- Correct: 13
- Partial: 0
- Incorrect: 0
- Unresolved (honest, outside scope): 2
- Answer coverage (CORRECT+PARTIAL)/total: 0.8667
- Resolved-question correctness CORRECT/(CORRECT+PARTIAL+INCORRECT): 1.0
- Provenance coverage: 1.0 (15/15)
- Direct: 12 (0.8); Inferred: 0 (0.0); Unresolved facts: 3 (0.2)

## Structural gold set (sampled, NOT repository-wide)
- Label: sampled structural gold-set evaluation
- Precision: 1.0 (35/35)
- Recall: 1.0 (35/35)
- base_entity: precision 1.0 recall 1.0 (10/10)
- eca: precision 1.0 recall 1.0 (5/5)
- relation: precision 1.0 recall 1.0 (10/10)
- service: precision 1.0 recall 1.0 (10/10)

## Store / pipeline
- store: stores/order-deps
- facts: outputs-deps/order-facts.jsonl
- manifest: outputs-deps/order-manifest.json
- unresolved: outputs-deps/order-unresolved.json
- graph: outputs-deps/order-graph.ttl
- triples: 117788
- facts_count: 10204
- unresolved_count: 386
- evaluation_hash: b553dd42942264785fb5aa0e76d6a17f4989280f0a9389c7c3c4a3d3804bfc9f

| ID | Category | Question | Expected | Graph Answer | Status | Fact Type | Evidence |
|----|----------|----------|----------|--------------|--------|-----------|----------|
| Q-COMP-001 | component | What component is being analyzed? | {"component": "order"} | {"components": ["datamodel", "order"]} | CORRECT | DIRECT | applications/order/ofbiz-component.xml; line 23; /ofbiz-component; direct |
| Q-COMP-002 | component | Which source/datamodel components are included in the current extraction scope? | {"components": ["datamodel", "order"], "dependency_files": ["applications/datamodel/entitydef/order-entitymodel.xml", "applications/datamodel/ofbiz-component.xml"], "include_dependencies": true} | {"components": ["datamodel", "order"], "dependency_files": ["applications/datamodel/entitydef/order-entitymodel.xml", "applications/datamodel/ofbiz-component.xml"], "include_dependencies": true} | CORRECT | DIRECT | manifest:scope; direct |
| Q-DATA-001 | entity | Does OrderHeader exist as a BASE entity? | {"entity": "OrderHeader", "is_base": true, "kind": "Entity"} | {"classes": ["Entity"], "entity": "OrderHeader", "exists": true} | CORRECT | DIRECT | applications/datamodel/entitydef/order-entitymodel.xml; line 418; /entitymodel/entity[16]; direct |
| Q-DATA-002 | entity | What are the primary key fields of OrderHeader? | {"entity": "OrderHeader", "primary_keys": ["orderId"]} | {"entity": "OrderHeader", "primary_keys": ["orderId"]} | CORRECT | DIRECT | applications/datamodel/entitydef/order-entitymodel.xml; line 419; /entitymodel/entity[16]/field[1]; direct |
| Q-DATA-003 | entity | Does OrderItem exist as a BASE entity? | {"entity": "OrderItem", "is_base": true, "kind": "Entity"} | {"classes": ["Entity"], "entity": "OrderItem", "exists": true} | CORRECT | DIRECT | applications/datamodel/entitydef/order-entitymodel.xml; line 523; /entitymodel/entity[19]; direct |
| Q-DATA-004 | relation | What relationships connect relevant Order entities (OrderHeader subject)? | {"resolved_relations": [{"fk_name": "ORDER_HDR_TYPE", "target": "OrderType", "type": "one"}, {"target": "OrderTypeAttr", "type": "many"}, {"fk_name": "ORDER_HDR_AOSHLST", "target": "ShoppingList", "type": "one"}], "subject": "OrderHeader", "unresolved_targets": ["Enumeration", "Facility", "BillingAccount", "ProductStore", "UserLogin", "StatusItem", "Uom", "WebSite"]} | {"relation_nodes": 12, "resolved_targets": ["OrderType", "OrderTypeAttr", "ShoppingList"], "subject": "OrderHeader", "unresolved_targets": ["BillingAccount", "Enumeration", "Facility", "NoteData", "ProductStore", "ShipmentReceipt", "StatusItem", "Uom", "UserLogin", "WebSite", "WorkEffort"]} | CORRECT | DIRECT | applications/datamodel/entitydef/order-entitymodel.xml; line 450; /entitymodel/entity[16]/relation[1]; direct |
| Q-ECA-001 | eca | What happens when OrderHeader is created (create-store, return) with statusId=ORDER_COMPLETED and needsInventoryIssuance=Y? | {"action_mode": "sync", "action_service": "issueImmediatelyFulfilledOrder", "conditions": [{"field": "statusId", "operator": "equals", "value": "ORDER_COMPLETED"}, {"field": "needsInventoryIssuance", "operator": "equals", "value": "Y"}], "event": "return", "operation": "create-store", "trigger_entity": "OrderHeader"} | {"action_service": "issueImmediatelyFulfilledOrder", "conditions": [{"field": "needsInventoryIssuance", "operator": "equals", "value": "Y"}, {"field": "statusId", "operator": "equals", "value": "ORDER_COMPLETED"}], "eca": "1", "eca_uri": "http://example.org/ofbiz/0.1/eca/0b23d547aab3/1", "event": "return", "operation": "create-store", "triggers_edge_present": false, "unresolved_reported": true} | UNRESOLVED | UNRESOLVED | applications/order/entitydef/eecas.xml; line 24; /entity-eca/eca[1]; direct |
| Q-ECA-002 | eca | Which ECA rule represents the OrderHeader create-store behavior? | {"eca_class": "EntityECA", "event": "return", "operation": "create-store", "trigger_entity": "OrderHeader"} | {"matches": [{"class": "EntityECA", "eca": "1", "event": "return", "operation": "create-store"}]} | CORRECT | DIRECT | applications/order/entitydef/eecas.xml; line 24; /entity-eca/eca[1]; direct |
| Q-ECA-003 | eca | Which service does the OrderHeader ECA action reference? | {"action_service": "issueImmediatelyFulfilledOrder", "defined_in": "applications/product/servicedef/services_facility.xml", "in_scope": false} | {"action_service": "issueImmediatelyFulfilledOrder", "node_classes": [], "node_exists": false, "unresolved_reported": true, "unresolved_via": ["eca-action"]} | UNRESOLVED | UNRESOLVED | applications/order/entitydef/eecas.xml; line 27; /entity-eca/eca[1]/action; unresolved |
| Q-PROV-001 | provenance | Can the graph provide source evidence for the storeOrder service fact? | {"extraction_type": "direct", "file": "applications/order/servicedef/services.xml", "line": 108, "service": "storeOrder", "xpath": "/services/service[10]"} | {"artifact_type": "service-def", "extraction_type": "direct", "file": "applications/order/servicedef/services.xml", "line": "108", "service": "storeOrder", "sha256_present": true, "xpath": "/services/service[10]"} | CORRECT | DIRECT | applications/order/servicedef/services.xml; line 108; /services/service[10]; direct |
| Q-SCOPE-001 | scope | Which known dependencies remain unresolved because they are outside the current scope? | {"unresolved_targets": [{"kind": "service", "name": "issueImmediatelyFulfilledOrder", "via": "eca-action"}, {"kind": "entity", "name": "AccommodationSpot"}, {"kind": "entity", "name": "ItemIssuance"}, {"kind": "entity", "name": "CommunicationEvent"}, {"kind": "entity", "name": "StatusItem"}]} | {"targets": [{"kind": "service", "minted": false, "name": "issueImmediatelyFulfilledOrder", "ok": true, "references": 1, "unresolved_reported": true}, {"kind": "entity", "minted": false, "name": "AccommodationSpot", "ok": true, "references": 8, "unresolved_reported": true}, {"kind": "entity", "minted": false, "name": "ItemIssuance", "ok": true, "references": 6, "unresolved_reported": true}, {"k... | CORRECT | UNRESOLVED | unresolved-report; unresolved |
| Q-SVC-001 | service | What is the purpose/description of storeOrder? | {"description": "Creates order entities", "service": "storeOrder"} | {"description": "Creates order entities", "service": "storeOrder"} | CORRECT | DIRECT | applications/order/servicedef/services.xml; line 108; /services/service[10]; direct |
| Q-SVC-002 | service | What implements storeOrder according to the service definition? | {"engine": "java", "implementation_class": "org.apache.ofbiz.order.order.OrderServices", "method": "createOrder", "service": "storeOrder"} | {"engine": "java", "implementation_class": "org.apache.ofbiz.order.order.OrderServices", "method": "createOrder", "method_uri": "http://example.org/ofbiz/0.1/method/org.apache.ofbiz.order.order.OrderServices#createOrder", "service": "storeOrder"} | CORRECT | DIRECT | applications/order/servicedef/services.xml; line 108; /services/service[10]; direct |
| Q-SVC-003 | service | What are the inputs of storeOrder? | {"count": 56, "inputs": ["affiliateId", "agreementId", "autoOrderShoppingListId", "billFromVendorPartyId", "billToCustomerPartyId", "billingAccountId", "currencyUom", "distributorId", "endUserCustomerPartyId", "externalId", "firstAttemptOrderId", "grandTotal", "internalCode", "isRushOrder", "orderAdditionalPartyRoleMap", "orderAdjustments", "orderAttributes", "orderContactMechs", "orderDate", "... | {"count": 56, "inputs": ["affiliateId", "agreementId", "autoOrderShoppingListId", "billFromVendorPartyId", "billToCustomerPartyId", "billingAccountId", "currencyUom", "distributorId", "endUserCustomerPartyId", "externalId", "firstAttemptOrderId", "grandTotal", "internalCode", "isRushOrder", "orderAdditionalPartyRoleMap", "orderAdjustments", "orderAttributes", "orderContactMechs", "orderDate", "... | CORRECT | DIRECT | applications/order/servicedef/services.xml; line 108; /services/service[10]; direct |
| Q-SVC-004 | service | What are the outputs of storeOrder? | {"count": 3, "outputs": ["orderId", "orderTypeId", "statusId"], "service": "storeOrder"} | {"count": 3, "outputs": ["orderId", "orderTypeId", "statusId"], "service": "storeOrder"} | CORRECT | DIRECT | applications/order/servicedef/services.xml; line 108; /services/service[10]; direct |

### Q-COMP-001 — What component is being analyzed?
- Category: component; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"component": "order"}`
- Graph answer: `{"components": ["datamodel", "order"]}`
- Evidence: applications/order/ofbiz-component.xml; line 23; /ofbiz-component; direct
- Note: Component node present.
- Sources: applications/order/ofbiz-component.xml

### Q-COMP-002 — Which source/datamodel components are included in the current extraction scope?
- Category: component; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"components": ["datamodel", "order"], "dependency_files": ["applications/datamodel/entitydef/order-entitymodel.xml", "applications/datamodel/ofbiz-component.xml"], "include_dependencies": true}`
- Graph answer: `{"components": ["datamodel", "order"], "dependency_files": ["applications/datamodel/entitydef/order-entitymodel.xml", "applications/datamodel/ofbiz-component.xml"], "include_dependencies": true}`
- Evidence: manifest:scope; direct
- Note: Scope matches manifest + graph.
- Sources: applications/order/ofbiz-component.xml, applications/datamodel/ofbiz-component.xml, applications/datamodel/entitydef/order-entitymodel.xml

### Q-DATA-001 — Does OrderHeader exist as a BASE entity?
- Category: entity; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"entity": "OrderHeader", "is_base": true, "kind": "Entity"}`
- Graph answer: `{"classes": ["Entity"], "entity": "OrderHeader", "exists": true}`
- Evidence: applications/datamodel/entitydef/order-entitymodel.xml; line 418; /entitymodel/entity[16]; direct
- Note: Base Entity node present (not a view).
- Sources: applications/datamodel/entitydef/order-entitymodel.xml

### Q-DATA-002 — What are the primary key fields of OrderHeader?
- Category: entity; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"entity": "OrderHeader", "primary_keys": ["orderId"]}`
- Graph answer: `{"entity": "OrderHeader", "primary_keys": ["orderId"]}`
- Evidence: applications/datamodel/entitydef/order-entitymodel.xml; line 419; /entitymodel/entity[16]/field[1]; direct
- Note: PK sets identical.
- Sources: applications/datamodel/entitydef/order-entitymodel.xml

### Q-DATA-003 — Does OrderItem exist as a BASE entity?
- Category: entity; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"entity": "OrderItem", "is_base": true, "kind": "Entity"}`
- Graph answer: `{"classes": ["Entity"], "entity": "OrderItem", "exists": true}`
- Evidence: applications/datamodel/entitydef/order-entitymodel.xml; line 523; /entitymodel/entity[19]; direct
- Note: Base Entity node present (not a view).
- Sources: applications/datamodel/entitydef/order-entitymodel.xml

### Q-DATA-004 — What relationships connect relevant Order entities (OrderHeader subject)?
- Category: relation; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"resolved_relations": [{"fk_name": "ORDER_HDR_TYPE", "target": "OrderType", "type": "one"}, {"target": "OrderTypeAttr", "type": "many"}, {"fk_name": "ORDER_HDR_AOSHLST", "target": "ShoppingList", "type": "one"}], "subject": "OrderHeader", "unresolved_targets": ["Enumeration", "Facility", "BillingAccount", "ProductStore", "UserLogin", "StatusItem", "Uom", "WebSite"]}`
- Graph answer: `{"relation_nodes": 12, "resolved_targets": ["OrderType", "OrderTypeAttr", "ShoppingList"], "subject": "OrderHeader", "unresolved_targets": ["BillingAccount", "Enumeration", "Facility", "NoteData", "ProductStore", "ShipmentReceipt", "StatusItem", "Uom", "UserLogin", "WebSite", "WorkEffort"]}`
- Evidence: applications/datamodel/entitydef/order-entitymodel.xml; line 450; /entitymodel/entity[16]/relation[1]; direct
- Note: Resolved + unresolved subsets verified.
- Sources: applications/datamodel/entitydef/order-entitymodel.xml

### Q-ECA-001 — What happens when OrderHeader is created (create-store, return) with statusId=ORDER_COMPLETED and needsInventoryIssuance=Y?
- Category: eca; Status: **UNRESOLVED**; Fact type: UNRESOLVED
- Expected: `{"action_mode": "sync", "action_service": "issueImmediatelyFulfilledOrder", "conditions": [{"field": "statusId", "operator": "equals", "value": "ORDER_COMPLETED"}, {"field": "needsInventoryIssuance", "operator": "equals", "value": "Y"}], "event": "return", "operation": "create-store", "trigger_entity": "OrderHeader"}`
- Graph answer: `{"action_service": "issueImmediatelyFulfilledOrder", "conditions": [{"field": "needsInventoryIssuance", "operator": "equals", "value": "Y"}, {"field": "statusId", "operator": "equals", "value": "ORDER_COMPLETED"}], "eca": "1", "eca_uri": "http://example.org/ofbiz/0.1/eca/0b23d547aab3/1", "event": "return", "operation": "create-store", "triggers_edge_present": false, "unresolved_reported": true}`
- Evidence: applications/order/entitydef/eecas.xml; line 24; /entity-eca/eca[1]; direct
- Note: ECA+conditions resolved; action 'issueImmediatelyFulfilledOrder' outside scope (reported, not minted).
- Sources: applications/order/entitydef/eecas.xml

### Q-ECA-002 — Which ECA rule represents the OrderHeader create-store behavior?
- Category: eca; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"eca_class": "EntityECA", "event": "return", "operation": "create-store", "trigger_entity": "OrderHeader"}`
- Graph answer: `{"matches": [{"class": "EntityECA", "eca": "1", "event": "return", "operation": "create-store"}]}`
- Evidence: applications/order/entitydef/eecas.xml; line 24; /entity-eca/eca[1]; direct
- Note: ECA rule identified.
- Sources: applications/order/entitydef/eecas.xml

### Q-ECA-003 — Which service does the OrderHeader ECA action reference?
- Category: eca; Status: **UNRESOLVED**; Fact type: UNRESOLVED
- Expected: `{"action_service": "issueImmediatelyFulfilledOrder", "defined_in": "applications/product/servicedef/services_facility.xml", "in_scope": false}`
- Graph answer: `{"action_service": "issueImmediatelyFulfilledOrder", "node_classes": [], "node_exists": false, "unresolved_reported": true, "unresolved_via": ["eca-action"]}`
- Evidence: applications/order/entitydef/eecas.xml; line 27; /entity-eca/eca[1]/action; unresolved
- Note: Reference stated in eecas.xml; target outside scope (correctly not minted).
- Sources: applications/order/entitydef/eecas.xml, applications/product/servicedef/services_facility.xml

### Q-PROV-001 — Can the graph provide source evidence for the storeOrder service fact?
- Category: provenance; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"extraction_type": "direct", "file": "applications/order/servicedef/services.xml", "line": 108, "service": "storeOrder", "xpath": "/services/service[10]"}`
- Graph answer: `{"artifact_type": "service-def", "extraction_type": "direct", "file": "applications/order/servicedef/services.xml", "line": "108", "service": "storeOrder", "sha256_present": true, "xpath": "/services/service[10]"}`
- Evidence: applications/order/servicedef/services.xml; line 108; /services/service[10]; direct
- Note: Full source evidence present.
- Sources: applications/order/servicedef/services.xml

### Q-SCOPE-001 — Which known dependencies remain unresolved because they are outside the current scope?
- Category: scope; Status: **CORRECT**; Fact type: UNRESOLVED
- Expected: `{"unresolved_targets": [{"kind": "service", "name": "issueImmediatelyFulfilledOrder", "via": "eca-action"}, {"kind": "entity", "name": "AccommodationSpot"}, {"kind": "entity", "name": "ItemIssuance"}, {"kind": "entity", "name": "CommunicationEvent"}, {"kind": "entity", "name": "StatusItem"}]}`
- Graph answer: `{"targets": [{"kind": "service", "minted": false, "name": "issueImmediatelyFulfilledOrder", "ok": true, "references": 1, "unresolved_reported": true}, {"kind": "entity", "minted": false, "name": "AccommodationSpot", "ok": true, "references": 8, "unresolved_reported": true}, {"kind": "entity", "minted": false, "name": "ItemIssuance", "ok": true, "references": 6, "unresolved_reported": true}, {"k...`
- Evidence: unresolved-report; unresolved
- Note: All expected out-of-scope refs reported, none minted.
- Sources: applications/order/entitydef/eecas.xml, applications/order/servicedef/services_requirement.xml, applications/order/servicedef/services_reservations.xml

### Q-SVC-001 — What is the purpose/description of storeOrder?
- Category: service; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"description": "Creates order entities", "service": "storeOrder"}`
- Graph answer: `{"description": "Creates order entities", "service": "storeOrder"}`
- Evidence: applications/order/servicedef/services.xml; line 108; /services/service[10]; direct
- Note: Verbatim description matches.
- Sources: applications/order/servicedef/services.xml

### Q-SVC-002 — What implements storeOrder according to the service definition?
- Category: service; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"engine": "java", "implementation_class": "org.apache.ofbiz.order.order.OrderServices", "method": "createOrder", "service": "storeOrder"}`
- Graph answer: `{"engine": "java", "implementation_class": "org.apache.ofbiz.order.order.OrderServices", "method": "createOrder", "method_uri": "http://example.org/ofbiz/0.1/method/org.apache.ofbiz.order.order.OrderServices#createOrder", "service": "storeOrder"}`
- Evidence: applications/order/servicedef/services.xml; line 108; /services/service[10]; direct
- Note: Source-stated binding matches (not code-verified).
- Sources: applications/order/servicedef/services.xml

### Q-SVC-003 — What are the inputs of storeOrder?
- Category: service; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"count": 56, "inputs": ["affiliateId", "agreementId", "autoOrderShoppingListId", "billFromVendorPartyId", "billToCustomerPartyId", "billingAccountId", "currencyUom", "distributorId", "endUserCustomerPartyId", "externalId", "firstAttemptOrderId", "grandTotal", "internalCode", "isRushOrder", "orderAdditionalPartyRoleMap", "orderAdjustments", "orderAttributes", "orderContactMechs", "orderDate", "...`
- Graph answer: `{"count": 56, "inputs": ["affiliateId", "agreementId", "autoOrderShoppingListId", "billFromVendorPartyId", "billToCustomerPartyId", "billingAccountId", "currencyUom", "distributorId", "endUserCustomerPartyId", "externalId", "firstAttemptOrderId", "grandTotal", "internalCode", "isRushOrder", "orderAdditionalPartyRoleMap", "orderAdjustments", "orderAttributes", "orderContactMechs", "orderDate", "...`
- Evidence: applications/order/servicedef/services.xml; line 108; /services/service[10]; direct
- Note: Input sets identical (56).
- Sources: applications/order/servicedef/services.xml

### Q-SVC-004 — What are the outputs of storeOrder?
- Category: service; Status: **CORRECT**; Fact type: DIRECT
- Expected: `{"count": 3, "outputs": ["orderId", "orderTypeId", "statusId"], "service": "storeOrder"}`
- Graph answer: `{"count": 3, "outputs": ["orderId", "orderTypeId", "statusId"], "service": "storeOrder"}`
- Evidence: applications/order/servicedef/services.xml; line 108; /services/service[10]; direct
- Note: Output sets identical.
- Sources: applications/order/servicedef/services.xml

## Structural details
- [base_entity] CustRequest: FOUND
- [base_entity] OrderAdjustment: FOUND
- [base_entity] OrderContactMech: FOUND
- [base_entity] OrderHeader: FOUND
- [base_entity] OrderItem: FOUND
- [base_entity] OrderItemShipGroup: FOUND
- [base_entity] OrderPaymentPreference: FOUND
- [base_entity] OrderRole: FOUND
- [base_entity] OrderStatus: FOUND
- [base_entity] OrderType: FOUND
- [eca] ECA:OrderHeader:return: FOUND
- [eca] ECA:OrderItem:return: FOUND
- [eca] ECA:OrderPaymentPreference:return: FOUND
- [eca] ECA:storeOrder:return: FOUND
- [eca] ECA:storeOrder:return: FOUND
- [relation] OrderAdjustment->OrderHeader: FOUND
- [relation] OrderAdjustment->OrderItem: FOUND
- [relation] OrderHeader->Facility: FOUND
- [relation] OrderHeader->OrderType: FOUND
- [relation] OrderHeader->OrderTypeAttr: FOUND
- [relation] OrderHeader->ShoppingList: FOUND
- [relation] OrderHeader->StatusItem: FOUND
- [relation] OrderItem->OrderHeader: FOUND
- [relation] OrderItem->Product: FOUND
- [relation] OrderItem->StatusItem: FOUND
- [service] addOrderRole: FOUND
- [service] appendOrderItem: FOUND
- [service] cancelOrderItem: FOUND
- [service] createCustRequest: FOUND
- [service] createOrderAdjustment: FOUND
- [service] createOrderHeader: FOUND
- [service] createQuote: FOUND
- [service] createReturnHeader: FOUND
- [service] findOrders: FOUND
- [service] storeOrder: FOUND
