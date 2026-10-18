# Context Identification Report: `apache-ofbiz-24.09.07` / `order`

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.
> Scope wording was corrected on 2026-10-17 from the archived RDF/facts;
> original extraction timestamps and measured data counts were retained.

_Generated 2026-09-21T20:53:30.701325+00:00 by ofbiz-context-extractor 0.1.0. Every statement below cites graph evidence;
out-of-scope references are listed as unresolved, never presented as discoveries._

## 1. Repository overview
- Repository: apache-ofbiz-24.09.07; component: `order`
- Source files analyzed: 17; facts extracted: 4699; graph triples: 42722
- Services: 467; base entities: 0; view-entities: 53; ECA rules: 111

## 2. Components discovered
- Requested component: `order`. Totals cover every source file listed below, including explicit dependencies.

## 3. Entities discovered
- Base entities (defined in entity models): 0 (e.g. none in scope)
- View-entities (joins over base entities): 53 (e.g. CommunicationEventAndCustRequest, CommunicationEventAndOrder, CommunicationEventAndReturn, CustReqAndTypeAndPartyRel, CustRequestAndCommEvent, CustRequestAndContent, CustRequestAndNote, CustRequestAndRole)
- Note: 0 base entities and 53 view-entities are represented from this run's source files. 549 entity references remain unresolved; these references are not additional discovered entities.

## 4. Services discovered
- Total: 467
- By engine: entity-auto=218, groovy=68, group=2, interface=7, java=127, simple=45

## 5. Service implementations
- DIRECTLY EXTRACTED bindings (stated location+invoke): 240 services
- Services with no code entry point in source (entity-auto/group/interface): 227
- Sample: addDistinctShoppingListItem -> component://order/src/main/groovy/org/apache/ofbiz/order/shoppinglist/ShoppingListServicesScript.groovy#addDistinctShoppingListItem; addOrderItemShipGroup -> org.apache.ofbiz.order.order.OrderServices#addOrderItemShipGroup; addOrderItemShipGroupAssoc -> org.apache.ofbiz.order.order.OrderServices#addOrderItemShipGroupAssoc; addOrderRole -> org.apache.ofbiz.order.order.OrderServices#addRoleType; addPaymentMethodToOrder -> component://order/minilang/order/OrderServices.xml#addPaymentMethodToOrder; addProductsBackToCategory -> component://order/src/main/groovy/org/apache/ofbiz/order/order/OrderReturnServicesScript.groovy#addProductsBackToCategory; addSuggestionsToShoppingList -> component://order/src/main/groovy/org/apache/ofbiz/order/shoppinglist/ShoppingListServicesScript.groovy#addSuggestionsToShoppingList; appendOrderItem -> org.apache.ofbiz.order.order.OrderServices#addItemToApprovedOrder

## 6. Service inputs/outputs
- Parameter links (direct + inferred): 915 inputs, 202 outputs
- INFERRED parameter links (implements-chain inheritance, evidenced): included in totals above; see facts with extractionType=inferred
- Most inputs: orderSequence_enforced (59); getNextOrderId (58); storeOrder (56); findOrders (48); createUpdateBillingAddressAndPaymentMethod (38)

## 7. Entity relationships
- DIRECTLY EXTRACTED view composition: 103 view-links, 156 member references, 411 aliases
- Relation facts extracted: 139; resolved relationTo links: 5. Definitions and targets are limited to the source files in this run.

## 8. ECA rules
- Rules: 111 (EntityECA=3, ServiceECA=108)
- Conditions: 86; services triggered (in scope): 61

## 9. Service-to-entity relationships
- Statements: 99 (stated `default-entity-name` literals + resolved `operatesOn` links)
- Most referenced: AccommodationSpot (1); AllocationPlanHeader (1); AllocationPlanItem (1); CartAbandonedLine (1); CommunicationEvent (1); CommunicationEventOrder (1); CommunicationEventReturn (1); CreditCard (1)
- No exclusivity or CRUD intent is claimed beyond the stated attribute (see ontology).

## 10. Important dependencies
- Highest fan-in (stated referencesService): massOrderChangeInterface (10); returnPermissionCheck (10); orderNotificationInterface (5); orderAdjustmentPermissionCheck (4); checkShoppingListItemSecurity (3); checkShoppingListSecurity (3); createShoppingListRecurrence (3); shoppingListItemInterface (3)
- referencesService links total: 59
- Cross-component dependencies (top dangling targets, reported with evidence, never minted): OrderItem (27 via relationTo,triggeredOnEntity,viewMemberEntity); OrderHeader (26 via operatesOn,relationTo,triggeredOnEntity,viewMemberEntity); OrderRole (15 via relationTo,viewMemberEntity); CustRequest (13 via operatesOn,relationTo,viewMemberEntity); OrderItemShipGrpInvRes (13 via operatesOn,relationTo,viewMemberEntity); StatusItem (13 via relationTo,viewMemberEntity); Product (13 via relationTo,viewMemberEntity); OrderPaymentPreference (12 via operatesOn,relationTo,triggeredOnEntity,viewMemberEntity); WorkEffort (9 via operatesOn,relationTo,viewMemberEntity); OrderItemShipGroup (8 via operatesOn,viewMemberEntity)

## 11. Provenance
- Every fact carries repository, file, line/XPath, extractor name/version, method, and direct/inferred classification.
- Extraction methods: implements-chain-resolution=594, xml-attribute-read=3925, xml-literal-reference=180
- Unresolved references (reported, never minted): 1026 (auto_attributes_unexpanded=431, dangling_reference=595)
- Source files: applications/order/entitydef/eecas.xml, applications/order/entitydef/entitymodel_view.xml, applications/order/ofbiz-component.xml, applications/order/servicedef/orderProcessXPDL.xml, applications/order/servicedef/secas.xml, applications/order/servicedef/services.xml, applications/order/servicedef/services_cart.xml, applications/order/servicedef/services_checkout.xml, applications/order/servicedef/services_order.xml, applications/order/servicedef/services_perm.xml, applications/order/servicedef/services_quote.xml, applications/order/servicedef/services_request.xml, applications/order/servicedef/services_requirement.xml, applications/order/servicedef/services_reservations.xml, applications/order/servicedef/services_return.xml, applications/order/servicedef/services_shoppinglist.xml, applications/order/servicedef/services_upgrade.xml

## 12. Extraction statistics
- Facts extracted: 4699
- DIRECTLY EXTRACTED: 4105
- INFERRED (deterministic joins, all evidence cited): 594
- Graph triples: 42722
- Facts by kind: auto_attributes=431, component=1, condition=86, eca=111, eca_action=150, edge=1403, param_override=50, permission_check=21, relation=139, resource=27, resource_loader=1, service=468, service_param=1087, view_alias=411, view_entity=53, view_link=103, view_member=156, webapp=1
