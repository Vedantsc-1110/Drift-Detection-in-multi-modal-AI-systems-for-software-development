# Extraction report: component `order`

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.

- Extractor: ofbiz-context-extractor 0.1.0
- Repository: apache-ofbiz-24.09.07
- Extracted at: 2026-09-22T06:39:24.496925+00:00
- Files parsed: 19 (errors: 0)
- Facts: 10204; unresolved references: 386

## Files
- `applications/datamodel/entitydef/order-entitymodel.xml` (entity-model)
- `applications/datamodel/ofbiz-component.xml` (component-descriptor)
- `applications/order/entitydef/eecas.xml` (entity-eca)
- `applications/order/entitydef/entitymodel_view.xml` (entity-model)
- `applications/order/ofbiz-component.xml` (component-descriptor)
- `applications/order/servicedef/orderProcessXPDL.xml` (service-def)
- `applications/order/servicedef/secas.xml` (service-eca)
- `applications/order/servicedef/services.xml` (service-def)
- `applications/order/servicedef/services_cart.xml` (service-def)
- `applications/order/servicedef/services_checkout.xml` (service-def)
- `applications/order/servicedef/services_order.xml` (service-def)
- `applications/order/servicedef/services_perm.xml` (service-def)
- `applications/order/servicedef/services_quote.xml` (service-def)
- `applications/order/servicedef/services_request.xml` (service-def)
- `applications/order/servicedef/services_requirement.xml` (service-def)
- `applications/order/servicedef/services_reservations.xml` (service-def)
- `applications/order/servicedef/services_return.xml` (service-def)
- `applications/order/servicedef/services_shoppinglist.xml` (service-def)
- `applications/order/servicedef/services_upgrade.xml` (service-def)

## Fact counts by kind
- auto_attributes: 431
- component: 2
- condition: 86
- eca: 111
- eca_action: 150
- edge: 3808
- entity: 112
- entity_field: 793
- param_override: 50
- permission_check: 21
- relation: 567
- resource: 62
- resource_loader: 2
- service: 468
- service_param: 2797
- view_alias: 423
- view_entity: 55
- view_link: 105
- view_member: 160
- webapp: 1

## Unresolved (reported, never minted as graph edges)
- auto_attributes_unexpanded: 13
- dangling_reference: 373

### Examples (first 20)
- [auto_attributes_unexpanded] checkCreateStockRequirementQoh --auto-attributes(include=pk,mode=IN)--> ItemIssuance (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_requirement.xml:135)
- [auto_attributes_unexpanded] checkCreateStockRequirementQoh --auto-attributes(include=nonpk,mode=IN)--> ItemIssuance (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_requirement.xml:136)
- [auto_attributes_unexpanded] createAccommodationSpot --auto-attributes(include=pk,mode=INOUT)--> AccommodationSpot (via auto-attributes(include=pk,mode=INOUT), applications/order/servicedef/services_reservations.xml:29)
- [auto_attributes_unexpanded] createAccommodationSpot --auto-attributes(include=nonpk,mode=IN)--> AccommodationSpot (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_reservations.xml:30)
- [auto_attributes_unexpanded] createCustRequestFromCommEvent --auto-attributes(include=pk,mode=IN)--> CommunicationEvent (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_request.xml:202)
- [auto_attributes_unexpanded] createCustRequestFromCommEvent --auto-attributes(include=nonpk,mode=IN)--> CommunicationEvent (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_request.xml:203)
- [auto_attributes_unexpanded] deleteAccommodationSpot --auto-attributes(include=pk,mode=IN)--> AccommodationSpot (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_reservations.xml:39)
- [auto_attributes_unexpanded] ensureWorkEffortAndCreateQuoteWorkEffort --auto-attributes(include=pk,mode=IN)--> WorkEffort (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_quote.xml:277)
- [auto_attributes_unexpanded] ensureWorkEffortAndCreateQuoteWorkEffort --auto-attributes(include=pk,mode=OUT)--> WorkEffort (via auto-attributes(include=pk,mode=OUT), applications/order/servicedef/services_quote.xml:278)
- [auto_attributes_unexpanded] ensureWorkEffortAndCreateQuoteWorkEffort --auto-attributes(include=nonpk,mode=IN)--> WorkEffort (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_quote.xml:279)
- [auto_attributes_unexpanded] itemFulfillmentInterface --auto-attributes(include=pk,mode=IN)--> ProductContent (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services.xml:652)
- [auto_attributes_unexpanded] updateAccommodationSpot --auto-attributes(include=pk,mode=IN)--> AccommodationSpot (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_reservations.xml:34)
- [auto_attributes_unexpanded] updateAccommodationSpot --auto-attributes(include=nonpk,mode=IN)--> AccommodationSpot (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_reservations.xml:35)
- [dangling_reference] http://example.org/ofbiz/0.1/service/checkCreateStockRequirementQoh --operatesOn--> ItemIssuance (via default-entity-name, applications/order/servicedef/services_requirement.xml:133)
- [dangling_reference] http://example.org/ofbiz/0.1/service/createAccommodationSpot --operatesOn--> AccommodationSpot (via default-entity-name, applications/order/servicedef/services_reservations.xml:27)
- [dangling_reference] http://example.org/ofbiz/0.1/service/createCustRequestFromCommEvent --operatesOn--> CommunicationEvent (via default-entity-name, applications/order/servicedef/services_request.xml:200)
- [dangling_reference] http://example.org/ofbiz/0.1/service/createUpdateCreditCard --operatesOn--> CreditCard (via default-entity-name, applications/order/servicedef/services.xml:1283)
- [dangling_reference] http://example.org/ofbiz/0.1/service/deleteAccommodationSpot --operatesOn--> AccommodationSpot (via default-entity-name, applications/order/servicedef/services_reservations.xml:37)
- [dangling_reference] http://example.org/ofbiz/0.1/service/ensureWorkEffortAndCreateQuoteWorkEffort --operatesOn--> WorkEffort (via default-entity-name, applications/order/servicedef/services_quote.xml:272)
- [dangling_reference] http://example.org/ofbiz/0.1/service/updateAccommodationSpot --operatesOn--> AccommodationSpot (via default-entity-name, applications/order/servicedef/services_reservations.xml:32)

Note: base entities referenced here (e.g. OrderHeader) are defined in
`applications/datamodel/entitydef/order-entitymodel.xml`, outside this
prototype's scope; their references are reported above, not invented.
