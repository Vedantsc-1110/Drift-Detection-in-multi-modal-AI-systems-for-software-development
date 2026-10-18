# Probabilistic Layer (Ollama, isolated)

> **Historical baseline / experiment scope.** This document describes the
> earlier `ofbiz` default-graph path, not the complete merged project. For the
> current `ctx` contract pipeline and dashboard, see
> [implementation status](implementation-status.md) and [the run guide](../HowToRun.md).

The deterministic pipeline in `src/contextgraph/` is the untouched baseline.
This layer lives in `src/contextgraph/prob/` + `prob.py` and may only READ
deterministic outputs. It writes exclusively to `outputs/prob/`.

```
Deterministic facts (facts.jsonl) ──read──> prob.py propose ──> proposals.jsonl (status=proposed)
                                                      │                    │
                                                      │              human review
                                                      │                    ↓
                                    deterministic triples ──guard──> accepted / rejected
                                    (facts.jsonl, read-only)         (never merged back)
```

## ProbabilisticFact schema

`subject, predicate, object, evidence[], confidence, model, promptVersion,
extractionType, status` (+ `extractedAt`, optional `reviewReason`).

- `extractionType` is always `"probabilistic"`.
- `confidence` ∈ [0, 1], required — deterministic facts never carry confidence.
- `evidence`: 1+ strings quoted verbatim from the input given to the model.
- `status`: `proposed` → `accepted` | `rejected`. Only `proposed` facts leave `propose`.
- `model`: e.g. `ollama:qwen2.5:1.5b`; `promptVersion`: e.g. `prob-v1`.
- Controlled predicate vocabulary (`prob-v1`): `suggestsDomain`,
  `managesEntity`, `relatesToService`, `requiresEntity`. Anything else is dropped.

## Never-overwrite guard

`review --auto-reject` (and `--accept`) compares each proposal's
`(subject, predicate, object)` against resolved deterministic edge triples.
Collisions are marked `rejected` with `reviewReason=duplicates-deterministic`
and the command refuses to accept them. Accepted proposals remain in the
proposals file; `facts.jsonl` and the RDF graph are never modified.

## Controlled example

Scope is one small file: `applications/order/servicedef/services_reservations.xml`
(3 services). Live run (requires `ollama serve` + a pulled model):

```
python prob.py propose --facts outputs/order-facts.jsonl \
  --source applications/order/servicedef/services_reservations.xml \
  --out outputs/prob/reservations-proposals.jsonl --model qwen2.5:1.5b
python prob.py list --proposals outputs/prob/reservations-proposals.jsonl
python prob.py review --proposals outputs/prob/reservations-proposals.jsonl \
  --facts outputs/order-facts.jsonl --auto-reject
```

`--stub` runs the same pipeline with a clearly labeled stub client for
offline tests/demos (model name `stub-test-client`, never an LLM claim).
