# Context Identification Report: `apache-ofbiz-24.09.07` / `order`

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.
> Scope wording was corrected on 2026-10-17 from the archived RDF/facts;
> original extraction timestamps and measured data counts were retained.

_Generated 2026-09-22T06:39:24.496925+00:00 by ofbiz-context-extractor 0.1.0. Every statement below cites graph evidence;
out-of-scope references are listed as unresolved, never presented as discoveries._

## 1. Repository overview
- Repository: apache-ofbiz-24.09.07; component: `order`
- Source files analyzed: 19; facts extracted: 10204; graph triples: 117788
- Services: 467; base entities: 112; view-entities: 55; ECA rules: 111

## 2. Components discovered
- Requested component: `order`. Totals cover every source file listed below, including explicit dependencies.

## 3. Entities discovered
- Base entities (defined in entity models): 112 (e.g. AllocationPlanHeader, AllocationPlanItem, AllocationPlanType, CartAbandonedLine, CommunicationEventOrder, CommunicationEventReturn, CustRequest, CustRequestAttribute)
- View-entities (joins over base entities): 55 (e.g. AllocationPlanAndItem, CommunicationEventAndCustRequest, CommunicationEventAndOrder, CommunicationEventAndReturn, CustReqAndTypeAndPartyRel, CustRequestAndCommEvent, CustRequestAndContent, CustRequestAndNote)
- Note: 112 base entities and 55 view-entities are represented from this run's source files. 327 entity references remain unresolved; these references are not additional discovered entities.

## 4. Services discovered
- Total: 467
- By engine: entity-auto=218, groovy=68, group=2, interface=7, java=127, simple=45

## 5. Service implementations
- DIRECTLY EXTRACTED bindings (stated location+invoke): 240 services
- Services with no code entry point in source (entity-auto/group/interface): 227
- Sample: addDistinctShoppingListItem -> component://order/src/main/groovy/org/apache/ofbiz/order/shoppinglist/ShoppingListServicesScript.groovy#addDistinctShoppingListItem; addOrderItemShipGroup -> org.apache.ofbiz.order.order.OrderServices#addOrderItemShipGroup; addOrderItemShipGroupAssoc -> org.apache.ofbiz.order.order.OrderServices#addOrderItemShipGroupAssoc; addOrderRole -> org.apache.ofbiz.order.order.OrderServices#addRoleType; addPaymentMethodToOrder -> component://order/minilang/order/OrderServices.xml#addPaymentMethodToOrder; addProductsBackToCategory -> component://order/src/main/groovy/org/apache/ofbiz/order/order/OrderReturnServicesScript.groovy#addProductsBackToCategory; addSuggestionsToShoppingList -> component://order/src/main/groovy/org/apache/ofbiz/order/shoppinglist/ShoppingListServicesScript.groovy#addSuggestionsToShoppingList; appendOrderItem -> org.apache.ofbiz.order.order.OrderServices#addItemToApprovedOrder

## 6. Service inputs/outputs
- Parameter links (direct + inferred): 2587 inputs, 281 outputs
- INFERRED parameter links (implements-chain inheritance, evidenced): included in totals above; see facts with extractionType=inferred
- Most inputs: createReturnAndItemOrAdjustment (60); orderSequence_enforced (59); getNextOrderId (58); storeOrder (56); findOrders (48)

## 7. Entity relationships
- DIRECTLY EXTRACTED view composition: 105 view-links, 160 member references, 423 aliases
- Relation facts extracted: 567; resolved relationTo links: 301. Definitions and targets are limited to the source files in this run.

## 8. ECA rules
- Rules: 111 (EntityECA=3, ServiceECA=108)
- Conditions: 86; services triggered (in scope): 61

## 9. Service-to-entity relationships
- Statements: 193 (stated `default-entity-name` literals + resolved `operatesOn` links)
- Most referenced: AllocationPlanHeader (2); AllocationPlanItem (2); CartAbandonedLine (2); CommunicationEventOrder (2); CommunicationEventReturn (2); CustRequest (2); CustRequestAttribute (2); CustRequestCategory (2)
- No exclusivity or CRUD intent is claimed beyond the stated attribute (see ontology).

## 10. Important dependencies
- Highest fan-in (stated referencesService): massOrderChangeInterface (10); returnPermissionCheck (10); orderNotificationInterface (5); orderAdjustmentPermissionCheck (4); checkShoppingListItemSecurity (3); checkShoppingListSecurity (3); createShoppingListRecurrence (3); shoppingListItemInterface (3)
- referencesService links total: 59
- Cross-component dependencies (top dangling targets, reported with evidence, never minted): StatusItem (32 via relationTo,viewMemberEntity); Product (24 via relationTo,viewMemberEntity); UserLogin (21 via relationTo); WorkEffort (17 via operatesOn,relationTo,viewMemberEntity); Party (17 via relationTo); ContactMech (11 via relationTo,viewMemberEntity); Uom (10 via relationTo); NoteData (9 via relationTo,viewMemberEntity); Facility (9 via relationTo); CommunicationEvent (8 via operatesOn,relationTo,viewMemberEntity)

## 11. Provenance
- Every fact carries repository, file, line/XPath, extractor name/version, method, and direct/inferred classification.
- Extraction methods: auto-attributes-expansion=3461, implements-chain-resolution=594, xml-attribute-read=5969, xml-literal-reference=180
- Unresolved references (reported, never minted): 386 (auto_attributes_unexpanded=13, dangling_reference=373)
- Source files: applications/datamodel/entitydef/order-entitymodel.xml, applications/datamodel/ofbiz-component.xml, applications/order/entitydef/eecas.xml, applications/order/entitydef/entitymodel_view.xml, applications/order/ofbiz-component.xml, applications/order/servicedef/orderProcessXPDL.xml, applications/order/servicedef/secas.xml, applications/order/servicedef/services.xml, applications/order/servicedef/services_cart.xml, applications/order/servicedef/services_checkout.xml, applications/order/servicedef/services_order.xml, applications/order/servicedef/services_perm.xml, applications/order/servicedef/services_quote.xml, applications/order/servicedef/services_request.xml, applications/order/servicedef/services_requirement.xml, applications/order/servicedef/services_reservations.xml, applications/order/servicedef/services_return.xml, applications/order/servicedef/services_shoppinglist.xml, applications/order/servicedef/services_upgrade.xml

## 12. Extraction statistics
- Facts extracted: 10204
- DIRECTLY EXTRACTED: 6149
- INFERRED (deterministic joins, all evidence cited): 4055
- Graph triples: 117788
- Facts by kind: auto_attributes=431, component=2, condition=86, eca=111, eca_action=150, edge=3808, entity=112, entity_field=793, param_override=50, permission_check=21, relation=567, resource=62, resource_loader=2, service=468, service_param=2797, view_alias=423, view_entity=55, view_link=105, view_member=160, webapp=1
