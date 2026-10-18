# Scope Comparison: order-only (BEFORE) vs order + datamodel (AFTER)

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

Both runs from the same code; BEFORE = `extract.py --component order`,
AFTER = `... --component order --include-dependencies`.
Dependency scope is explicit (`scanner.COMPONENT_DEPENDENCIES`), attributed
per file (base entities belong to component `datamodel`), and entities are
minted only from `<entity>` definitions — never from mentions.

| Metric | BEFORE (order-only) | AFTER (+ datamodel) |
|---|---|---|
| Services | 467 nodes (468 elements; 1 duplicate def. merged) | 467 (unchanged) |
| Base entities | 0 | 112 (`OrderHeader`, `OrderItem`, …) |
| View-entities | 53 | 55 (+2 datamodel views) |
| Entity fields | 0 | 793 |
| Relations extracted | 139 (view `<relation>`s; previously dropped) | 567 (422 base + 145 view) |
| `relationTo` resolved | 5 | 301 |
| ECAs | 111 (unchanged) | 111 (unchanged) |
| `operatesOn` dangling | 258 | 7 |
| `triggeredOnEntity` dangling | 3 | 0 |
| `auto_attributes` unexpanded | 431 | 13 |
| `viewMemberEntity` dangling | 154 | 54 |
| Unresolved total | 1026 | 386 |
| Facts | 4699 (4105 direct / 594 inferred) | 10204 (6149 direct / 4055 inferred) |
| RDF triples | 42722 | 117788 |
| SHACL | conforms, 0 violations, 20 warnings | conforms, 0 violations, 20 warnings (no shape change needed) |
| Provenance | every fact: file+line/XPath/version/kind | same, + datamodel file evidence; inferred expansions carry 2 evidence spans |

Connected-path example (was: trigger name only): `OrderHeader`
—`triggeredOnEntity`→ ECA(`create-store`/`return`, 2 conditions)
—`triggersService`→ (still reported, not minted: `issueImmediatelyFulfilledOrder`
is defined outside both scopes, `eecas.xml:27`).

Remaining dangling (all evidenced, next-scope pointers): 266 `relationTo`
(ContactMech/Party/Product targets in other datamodel files), 54 view members
(`Product`, `InventoryItem`, `Party`…), 29 ECA actions + 9 ECA triggers owned by
other components, 8 service refs (`permissionInterface`, content services),
7 `operatesOn` (`AccommodationSpot` has no definition anywhere in scope;
`ItemIssuance`, `WorkEffort`, `CreditCard`, `CommunicationEvent` live in other
models), 13 unexpanded directives on those same undefined entities.
