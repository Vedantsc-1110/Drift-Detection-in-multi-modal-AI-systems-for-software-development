# Oxigraph Store (local)

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

Module: `src/contextgraph/store.py` (`ContextStore`), queries in
`src/contextgraph/queries.py`, CLI in `store_graph.py`.

## Pipeline position

```
OFBiz repo -> extract.py -> facts.jsonl -> build_graph.py -> graph.ttl
  -> store_graph.py load -> Oxigraph (stores/<version>/) -> SPARQL -> reports
```

## CLI

- `python store_graph.py load --graph outputs/order-graph.ttl --store stores/order`
  (clears first; `--no-clear` to append)
- `python store_graph.py query --store stores/order --q inputs --arg storeOrder`
- `python store_graph.py export --store stores/order --out outputs/order-graph-export.ttl`
- `python store_graph.py clear --store stores/order`

Rebuild from scratch = `clear` + `load` (both deterministic; same Turtle in →
same triples out).

## Query library (`queries.py`, all `ORDER BY`-deterministic)

| Key | Question | Argument |
|---|---|---|
| `services` | 1. What services exist? | — |
| `implementations` | 2. Which class/method implements each service? (null when engine has no entry point) | — |
| `inputs` | 3. What inputs does a service require? | service name |
| `outputs` | 4. What outputs does it produce? | service name |
| `entities-referenced` | 5. Which entities are referenced? (`operatesOn` links + stated `defaultEntityName`s) | — |
| `eca-rules` | 6. Which ECA rules exist? | — |
| `eca-triggered-services` | 7. Which services are triggered by ECA rules? | — |
| `fact-provenance` | 8. Where was a fact extracted from? (file, sha, type, kind, line) | fact URI |
| `service-files` | 9. Which source files contribute to a service? (service + its params) | service name |
| `component-services` | 10. Which services belong to a component? | component name |

`store.sparql()` returns rows as `{var: python value}` dicts (literals →
values, IRIs → strings), in query order — run twice, get identical rows
(asserted in `tests/test_store.py`, with export round-trip and clear/rebuild).
