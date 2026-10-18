# Part 1 Deterministic Evaluation — fixed question set

> This is the historical baseline evaluation, not the merged contract/drift
> acceptance suite. The real OFBiz checkout and regenerated baseline store are
> prerequisites for source-backed reruns. See [the run guide](../HowToRun.md).

Scope: `order` component + explicit dependency
`applications/datamodel/entitydef/order-entitymodel.xml`.

## Files

- `questions.yaml` — 15 grounded questions (component, service, entity,
  relation, ECA, provenance, unresolved). Every expected answer was read from
  the actual dataset files; nothing is invented from general knowledge.
- `structural-gold.yaml` — sampled structural gold set (10 services, 10 base
  entities, 10 relations, 5 ECAs). Label: **sampled structural gold-set
  evaluation** (not repository-wide precision/recall).

## Run

```powershell
python evaluate.py --store stores/order-deps --evaluation evaluation/questions.yaml --out outputs/evaluation
python evaluate.py --help
```

Defaults (all overridable):

- `--facts outputs-deps/order-facts.jsonl`
- `--manifest outputs-deps/order-manifest.json`
- `--unresolved outputs-deps/order-unresolved.json`
- `--structural evaluation/structural-gold.yaml`
- `--graph outputs-deps/order-graph.ttl` (used for triple count + hash)

## Statuses

- `CORRECT` — graph answer matches expected (structured comparison).
- `PARTIAL` — subset/overlap but incomplete.
- `INCORRECT` — contradicts expected.
- `UNRESOLVED` — source establishes a reference but the target is outside the
  current extraction scope; the graph correctly reports it instead of minting
  a node. This is honest behavior, not failure.

## Fact types

- `DIRECT` — extractor directly observed a source-level fact.
- `INFERRED` — deterministic fact derived by combining explicit evidence.
- `UNRESOLVED` — reference known but target outside scope.

`INFERRED` does NOT mean uncertain or LLM-generated.
