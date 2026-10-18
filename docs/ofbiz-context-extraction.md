# OFBiz Context Extraction — `applications/order/` (Prototype Scope)

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

Research project: *Identifying Context for Enterprises using Deterministic as well as Probabilistic Methods* — **Part 1 only** (deterministic-first Context Graph). This document predates the current PART 2 semantic and PART 4 drift modules. No LLM extraction — every fact below is traceable to a source artifact.

> **Scope note (verified):** the `order` component's *core entities do NOT live in `applications/order/entitydef/`*.
> That directory contains only `entitymodel_view.xml` (53 `<view-entity>`, 0 `<entity>`) and `eecas.xml`.
> The 112 base entities (+ 2 view-entities, 428 relations) live in
> `applications/datamodel/entitydef/order-entitymodel.xml`. The prototype MUST read both.

Dataset version: Apache OFBiz **24.09.07** (`dataset/apache-ofbiz-24.09.07`). All paths below are relative to that root. The `dataset/` tree is **read-only evidence**.

## Module layout (verified)

```
applications/order/
  ofbiz-component.xml     # component registry (69 lines)
  entitydef/              # entitymodel_view.xml (53 views), eecas.xml (3 ECAs)
  servicedef/             # 14 files, 468 <service> total (services.xml: 155)
  src/main/java/          # 42 .java files (e.g. order/OrderServices.java)
  src/main/groovy/        # 90 .groovy files
  minilang/               # simple-method XML (e.g. minilang/order/OrderServices.xml)
  widget/ordermgr/        # ~35 Screens/Forms/Menus files
  config/                 # order.properties + OrderEntityLabels/OrderUiLabels/ErrorUiLabels XML
  webapp/ordermgr/WEB-INF/controller.xml  # request-maps (event type=service -> findOrders, ...)
  data/ testdef/ template/                # OUT OF SCOPE for this prototype
```

Service count per file (measured): services.xml 155, services_return.xml 73, services_order.xml 61,
services_quote.xml 48, services_request.xml 43, services_requirement.xml 42, services_shoppinglist.xml 23,
services_cart.xml 15, services_reservations.xml 3, services_checkout.xml 3, services_upgrade.xml 1,
services_perm.xml 1. Engine mix in services.xml: java 81, entity-auto 37, simple 25, groovy 7, group 2, interface 3.
`secas.xml` holds **108** service ECAs.

## Required table

| Artifact Type | Source Location | Extractable Facts | Extraction Method | Direct / Inference |
|---|---|---|---|---|
| Component / module info | `applications/order/ofbiz-component.xml` — `<ofbiz-component name>`, `<resource-loader>`, `<classpath location="config">`, `<entity-resource>`, `<service-resource>`, `<test-suite>`, `<webapp name/title/mount-point/location/base-permission/app-shortcut-screen>` | Component name (`order`); resource inventory (which entity/service/test files belong to it); webapp mount (`/ordermgr`), permissions (`OFBTOOLS,ORDERMGR`) | XML parse (lxml/ElementTree), attribute read | **Direct** |
| Entities | `applications/datamodel/entitydef/order-entitymodel.xml` — `<entity entity-name package-name never-cache title>` + `<field name type>` + `<prim-key field>` | 112 entities (e.g. `OrderHeader`, `OrderAdjustment`); field names+types (e.g. `orderId:id`, `grandTotal:currency-amount`); primary keys | XML parse, attribute read | **Direct** |
| View entities | `applications/order/entitydef/entitymodel_view.xml` — `<view-entity entity-name>` + `<member-entity entity-alias entity-name>` + `<alias entity-alias name field>` + `<view-link entity-alias rel-entity-alias>` + `<key-map field-name>` | 53 views (e.g. `OrderHeaderAndItems` joins `OH:OrderHeader`↔`OI:OrderItem` on `orderId`) | XML parse | **Direct** (join edges stated by `view-link`) |
| Entity relationships | `*-entitymodel.xml` — `<relation type fk-name title rel-entity-name>` + `<key-map field-name rel-field-name>` | 428 relations in order model (e.g. `OrderHeader --ORDER_HDR_TYPE--> OrderType` via `orderTypeId`; `type="one"` vs `"many"`) | XML parse, attribute read | **Direct** (only what `type`/`key-map` state) |
| Services | `applications/order/servicedef/services*.xml` — `<service name engine location invoke default-entity-name auth require-new-transaction transaction-timeout>` | 468 services; impl binding (e.g. `cancelOrderItemNoActions` → java `org.apache.ofbiz.order.order.OrderServices#cancelOrderItem`); `default-entity-name` link | XML parse, attribute read | **Direct** |
| Service inputs | Same files — `<attribute name type mode="IN"/"INOUT" optional entity-name>` + `<auto-attributes include="pk"/"nonpk" mode optional>` + `<override name mode …>` | Explicit attrs (e.g. `orderNotificationInterface`: `orderId IN required`; mode mix in services.xml: IN 390, OUT 51, INOUT 14); `auto-attributes` patterns (81 in services.xml) | XML parse | **Direct** for `<attribute>`; **Inference (deterministic join)** for `auto-attributes` expansion — must cite the entity definition as second evidence and flag as expanded |
| Service outputs | Same files — `<attribute mode="OUT"/"INOUT">` + `<override>` + `<implements service>` inherited contract (e.g. `sendOrderConfirmation` implements `orderNotificationInterface` → OUT: `emailType, body, messageWrapper, subject`) | OUT params per service, incl. inherited via `implements` (21 in services.xml) | XML parse + `implements` chain resolution | **Direct** (attribute); **Inference** (inherited outputs — cite the chain) |
| Java impl classes/methods | `src/main/java/**.java` — `package`, `class`, `public static Map<String,Object> name(DispatchContext, Map)` (e.g. `OrderServices.createOrder/resetGrandTotal/cancelOrderItem`) | Method inventory; **confirmation** that a `location`+`invoke` from services XML resolves to a real method | Regex/AST-lite parse + join on `location`+`invoke` | **Direct** (method exists; binding stated by service XML). Method *behaviour* = do NOT infer |
| Entity ECA rules | `applications/order/entitydef/eecas.xml` — `<eca entity operation event>` + `<condition field-name operator value>` + `<action service mode>` (only 3 ECAs, e.g. `OrderHeader create-store → issueImmediatelyFulfilledOrder` when `statusId=ORDER_COMPLETED, needsInventoryIssuance=Y`) | Entity-triggered service calls with exact trigger + guard | XML parse | **Direct** |
| Conditions | `servicedef/secas.xml` (108 ECAs: `<eca service event>` + `<condition field-name operator value>` + `<action service mode persist run-as-user>`, e.g. `changeOrderItemStatus` + `statusId=ITEM_CANCELLED` → 6 sync actions) and minilang `<if-empty>/<if-not-empty>/<compare>` | Guard expressions (`operator`: `equals`, `is-not-empty`, …) on both service-ECA and simple-method paths | XML parse | **Direct** as syntax; semantic *meaning* of the guard = do NOT infer |
| Service-to-service refs | (a) `<implements service>` + `<permission-service service-name main-action>` (4 in services.xml) + `<group><invoke name result-to-context>` (e.g. `completePurchaseOrder` → 3 invokes) — stated; (b) `secas.xml` actions — stated; (c) Java `dispatcher.runSync/runAsync("name")` and `delegator.makeValue/findOne/findByAnd("Entity")` string literals (verified in `OrderServices.java`); (d) minilang `make-value entity-name` (e.g. `createOrderHeader` → `OrderHeader`) + `check-permission permission action` | Call/reference edges with call-site evidence | (a)(b) XML parse; (c) literal string extraction; (d) XML parse | **Direct** where a literal/name is stated. Dynamic service/entity names (variables, concatenation) = do NOT infer |
| Widget / UI bindings | `widget/ordermgr/*.xml` (Screen namespace `Widget-Screen`: `<screen name>`, `<decorator-screen location name>`, `<include-menu>`, `<property-map resource>`; Form namespace `Widget-Form`: `<form name target>`, `<alt-target target use-when>`, e.g. form target `createOrderHeader`) | Screen/form inventory; screen→service *target* names; label-bundle deps (`OrderUiLabels`…) | XML parse (namespace-aware) | **Direct** (target stated). "Form invokes service with these params" beyond `target` = **Inference**, do NOT assert |
| Config / labels | `config/order.properties`, `taxware.properties` (`key=value`); `config/OrderEntityLabels.xml`, `OrderUiLabels.xml` (`<resource><property key><value xml:lang>`) | Property keys; i18n label keys per entity/field | Properties + XML parse | **Direct**. Concept mapping from label *text* = do NOT infer |
| Web endpoints | `webapp/ordermgr/WEB-INF/controller.xml` — `<include location>` + `<request-map uri>` + `<security>` + `<event type="service" invoke="findOrders">` + `<response type view>` | URI→service/view edges (e.g. `searchorders` → service `findOrders` → view `findorders`) | XML parse | **Direct** |
| Source-file provenance | Every fact above | `sourceFile` (repo-relative path), `sha256`, XML line number, `extractor name+version`, `direct|inferred`, evidence snippet | Recorder at extraction time | **Direct** (metadata, always required) |

## What can be extracted deterministically (allow-list)

1. All XML element/attribute values listed above via namespace-aware parsing (`Site-Conf`, `Widget-Screen`, `Widget-Form`, `Simple-Method` namespaces observed).
2. Literal cross-references: `implements`, `permission-service`, `group/invoke`, ECA `action service`, controller `event invoke`, form `target`, `delegator.makeValue("X")` / `dispatcher.runSync("Y")` string literals, minilang `entity-name`.
3. `auto-attributes` expansion **only** as a flagged deterministic join (service file + entity definition both cited).
4. Counts/reconciliation: files scanned vs facts emitted; unresolvable names go to a dangling-reference report, never silently dropped or invented.

## What requires inference (allowed only if flagged + evidenced)

- `auto-attributes` → concrete field lists (needs entity lookup).
- Inherited inputs/outputs via `implements` chains.
- `default-entity-name` on java/groovy services → "operates on entity" (the attribute is stated; exclusivity/intent is not).
- Java/Groovy call graph beyond string literals; overload resolution; dynamic dispatch.
- Screen/form `target` → actual runtime invocation signature.

## What must NOT be inferred (deny-list)

- Business semantics from names (`cancelOrderItem` "cancels an order" — not a fact).
- Entity ownership: the component declaring an `<entity-resource>` is not necessarily where the entity is defined (order entities live in `datamodel/`).
- Cardinality/optionality beyond what `relation type` and `attribute optional` state.
- Transactional, security, or caching behaviour beyond the stated attributes (`require-new-transaction`, `auth`, `never-cache`).
- Calls via dynamically computed service/entity names.
- Any relationship not present as a literal in a source file. No LLM-guessed edges in Part 1.
