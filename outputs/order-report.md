# Extraction report: component `order`

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.

- Extractor: ofbiz-context-extractor 0.1.0
- Repository: apache-ofbiz-24.09.07
- Extracted at: 2026-09-21T20:53:30.701325+00:00
- Files parsed: 17 (errors: 0)
- Facts: 4699; unresolved references: 1026

## Files
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
- component: 1
- condition: 86
- eca: 111
- eca_action: 150
- edge: 1403
- param_override: 50
- permission_check: 21
- relation: 139
- resource: 27
- resource_loader: 1
- service: 468
- service_param: 1087
- view_alias: 411
- view_entity: 53
- view_link: 103
- view_member: 156
- webapp: 1

## Unresolved (reported, never minted as graph edges)
- auto_attributes_unexpanded: 431
- dangling_reference: 595

### Examples (first 20)
- [auto_attributes_unexpanded] addOrderItemShipGroup --auto-attributes(include=pk,mode=IN)--> OrderItemShipGroup (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services.xml:1467)
- [auto_attributes_unexpanded] addOrderItemShipGroup --auto-attributes(include=nonpk,mode=IN)--> OrderItemShipGroup (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services.xml:1468)
- [auto_attributes_unexpanded] addOrderItemShipGroupAssoc --auto-attributes(include=pk,mode=IN)--> OrderItemShipGroupAssoc (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services.xml:1483)
- [auto_attributes_unexpanded] addOrderItemShipGroupAssoc --auto-attributes(include=nonpk,mode=IN)--> OrderItemShipGroupAssoc (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services.xml:1484)
- [auto_attributes_unexpanded] autoUpdateQuotePrice --auto-attributes(include=pk,mode=IN)--> QuoteItem (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_quote.xml:216)
- [auto_attributes_unexpanded] cancelReplacementOrderItems --auto-attributes(include=pk,mode=IN)--> ReturnItem (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_return.xml:117)
- [auto_attributes_unexpanded] checkCreateStockRequirementQoh --auto-attributes(include=pk,mode=IN)--> ItemIssuance (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_requirement.xml:135)
- [auto_attributes_unexpanded] checkCreateStockRequirementQoh --auto-attributes(include=nonpk,mode=IN)--> ItemIssuance (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_requirement.xml:136)
- [auto_attributes_unexpanded] checkStatusCustRequest --auto-attributes(include=pk,mode=IN)--> CustRequest (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_request.xml:133)
- [auto_attributes_unexpanded] checkUpdateQuoteStatus --auto-attributes(include=pk,mode=IN)--> Quote (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_quote.xml:69)
- [auto_attributes_unexpanded] copyCustRequestItem --auto-attributes(include=pk,mode=IN)--> CustRequestItem (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_request.xml:104)
- [auto_attributes_unexpanded] copyCustRequestItem --auto-attributes(include=nonpk,mode=IN)--> CustRequestItem (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_request.xml:105)
- [auto_attributes_unexpanded] copyQuote --auto-attributes(include=pk,mode=INOUT)--> Quote (via auto-attributes(include=pk,mode=INOUT), applications/order/servicedef/services_quote.xml:58)
- [auto_attributes_unexpanded] copyQuoteItem --auto-attributes(include=pk,mode=IN)--> QuoteItem (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services_quote.xml:127)
- [auto_attributes_unexpanded] copyQuoteItem --auto-attributes(include=nonpk,mode=IN)--> QuoteItem (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_quote.xml:128)
- [auto_attributes_unexpanded] createAccommodationSpot --auto-attributes(include=pk,mode=INOUT)--> AccommodationSpot (via auto-attributes(include=pk,mode=INOUT), applications/order/servicedef/services_reservations.xml:29)
- [auto_attributes_unexpanded] createAccommodationSpot --auto-attributes(include=nonpk,mode=IN)--> AccommodationSpot (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services_reservations.xml:30)
- [auto_attributes_unexpanded] createAllocationPlanHeader --auto-attributes(include=pk,mode=IN)--> AllocationPlanHeader (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services.xml:1623)
- [auto_attributes_unexpanded] createAllocationPlanHeader --auto-attributes(include=nonpk,mode=IN)--> AllocationPlanHeader (via auto-attributes(include=nonpk,mode=IN), applications/order/servicedef/services.xml:1624)
- [auto_attributes_unexpanded] createAllocationPlanItem --auto-attributes(include=pk,mode=IN)--> AllocationPlanItem (via auto-attributes(include=pk,mode=IN), applications/order/servicedef/services.xml:1639)

Note: base entities referenced here (e.g. OrderHeader) are defined in
`applications/datamodel/entitydef/order-entitymodel.xml`, outside this
prototype's scope; their references are reported above, not invented.
