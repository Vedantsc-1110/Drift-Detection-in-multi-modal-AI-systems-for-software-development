# OFBiz portion (referenced, not redistributed)

> **Frozen v1.0 dataset description.** Counts and baseline limitations describe
> the original extraction. OFBiz source and development tools are not included
> in this package; full source validation requires the external pinned checkout.
> Later contract/AST/dashboard implementation does not change these baseline
> measurements. The current project review is in `BRUTAL_REVIEW.md` in the development repository.

The full Apache OFBiz repository (~180MB+) is NOT copied into this package.
Use your local checkout at the exact version below.

- Exact version: Apache OFBiz 24.09.07
- Expected location: `dataset/apache-ofbiz-24.09.07` relative to the project
  root (read-only; never modified by the extractor or dataset scripts).
- Extraction scope (deterministic baseline, Part 1):
  - `applications/order/` (services, views, ECAs, component descriptor)
  - `applications/datamodel/entitydef/order-entitymodel.xml` (112 base entities)
  - `applications/datamodel/ofbiz-component.xml` (component node)
- Relevant source paths:
  - `applications/order/servicedef/services*.xml` (468 service facts)
  - `applications/order/servicedef/secas.xml` (108 service ECAs)
  - `applications/order/entitydef/eecas.xml` (3 entity ECAs)
  - `applications/order/entitydef/entitymodel_view.xml` (55 view entities)
  - `applications/datamodel/entitydef/order-entitymodel.xml` (112 entities, 567 relations)
- Processed baseline: 467 Service nodes, 112 base + 55 view entities,
  567 relations (301 resolved), 111 ECAs, 386 unresolved, 10,204 facts,
  117,788 RDF triples, SHACL 0 violations.

## How to reproduce the extraction

From the project root (with the OFBiz tree in place):

```powershell
python extract.py --root dataset/apache-ofbiz-24.09.07 --component order --out outputs-deps --include-dependencies
python build_graph.py --facts outputs-deps/order-facts.jsonl --manifest outputs-deps/order-manifest.json --out outputs-deps/order-graph.ttl
python store_graph.py load --graph outputs-deps/order-graph.ttl --store stores/order-deps
python evaluate.py --store stores/order-deps --evaluation evaluation/questions.yaml --out outputs/evaluation
```

## Licensing

Apache OFBiz is licensed under the Apache License 2.0. See
`LICENSES_AND_SOURCES.md` and the `LICENSE`/`NOTICE` files inside the OFBiz
tree. The synthetic corpus in this package is original fictional content for
research evaluation (no OFBiz code copied into it).
