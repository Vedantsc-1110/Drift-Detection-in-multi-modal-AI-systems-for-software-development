# Part 2 integration run report (§11.1)

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.

- LLM layer: RECORDED (mocked) responses — no live Groq key / Ollama in this run.
- Stage-1 input: tests/fixtures/llm/stage1_fixture.ttl (hand-made, fixture tree).
- Wall-clock: 2.05s

## Triples per graph (metric: ~500+ on real data)
- ofbiz_semantic.ttl: 27
- document_semantic.ttl: 84
- cuad.ttl: 105
- edgar.ttl: 93
- Total: 309 — FAIL (fixture scale; see deviation)

## Corroboration (metric: > 60% supported)
- DIRECT rate: 0/20 = 0.0000
- DIRECT+INDIRECT rate: 10/20 = 0.5000 — FAIL (recorded claims are novel by design; see deviation)

## Accuracy sample (metric: > 80%% of 50 human-rated facts)
- Verdict: N/A — requires human rating. Sample table for raters:
| # | subject | predicate | object | confidence | support | rating |
|---|---------|-----------|--------|------------|---------|--------|
| 1 | createOrder | belongsToConcept | OrderCapture | 0.80 | INDIRECT | _ |
| 2 | OrderModule | businessPurpose | Capture and fulfil customer orders end t | 0.78 | SYNTHETIC | _ |
| 3 | OrderModule | dependsOn | PartyModule | 0.74 | SYNTHETIC | _ |
| 4 | createOrder | managesEntity | OrderHeader | 0.82 | INDIRECT | _ |
| 5 | Governing Law | mentionsEntity | OrderHeader | 0.72 | INDIRECT | _ |
| 6 | Governing Law | mentionsEntity | OrderHeader | 0.72 | INDIRECT | _ |
| 7 | P01 | mentionsEntity | OrderHeader | 0.75 | INDIRECT | _ |
| 8 | P01 | mentionsEntity | OrderHeader | 0.75 | INDIRECT | _ |
| 9 | P01 | mentionsEntity | OrderHeader | 0.75 | INDIRECT | _ |
| 10 | Payment Terms | mentionsEntity | Invoice | 0.80 | INDIRECT | _ |
| 11 | Payment Terms | mentionsEntity | Invoice | 0.80 | INDIRECT | _ |
| 12 | Business | mentionsProcess | createOrder | 0.74 | INDIRECT | _ |
| 13 | ACME-2025-10K | referencesModule | Accounting | 0.77 | SYNTHETIC | _ |
| 14 | ACME-2025-10K | referencesModule | Order | 0.80 | SYNTHETIC | _ |
| 15 | P01 | requiresApproval | Manager, Procurement Officer, and Financ | 0.82 | SYNTHETIC | _ |
| 16 | P01 | requiresApproval | Manager, Procurement Officer, and Financ | 0.82 | SYNTHETIC | _ |
| 17 | P01 | requiresApproval | Manager, Procurement Officer, and Financ | 0.82 | SYNTHETIC | _ |
| 18 | P01 | threshold | Purchases above $50,000 require three ap | 0.80 | SYNTHETIC | _ |
| 19 | P01 | threshold | Purchases above $50,000 require three ap | 0.80 | SYNTHETIC | _ |
| 20 | P01 | threshold | Purchases above $50,000 require three ap | 0.80 | SYNTHETIC | _ |

## Machine spec
- system: Windows
- release: 11
- version: 10.0.26200
- machine: AMD64
- processor: Intel64 Family 6 Model 154 Stepping 4, GenuineIntel
- cpu_count: 12
- ram: 16068 MiB total

## Deviation notes
- No live LLM: recorded fixtures stand in; the corroborated path (>=0.95)
  is proven by Task 2.3 unit tests with matched claims.
- Fixture scale (2 contracts, 1 filing, 3 docs) cannot hit ~500 triples;
  per-graph outputs validate clean under Task 2.8 rules.
