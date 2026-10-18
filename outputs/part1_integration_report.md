# Part 1 integration run report (§11.1)

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.

- Dataset: C:/Users/vedan/OneDrive/Desktop/EDITY/enterprise-context-graph/tests/fixtures (22 files, fixture tree — real OFBiz 24.09 unavailable)
- Tool: ofbiz-context-extractor 0.1.0
- Wall-clock extraction time: 0.15s (metric: < 300s) — PASS
- Graph size: 1389 triples / 142 facts (metric: ~5000+ on real OFBiz core) — see deviation note

## Triples per file
- airflow.ttl: 107
- cicd.ttl: 199
- ofbiz_structural.ttl: 1083

## Coverage vs manual inventory (metric: > 0.95 per area)
- services: 4/4 = 1.0000 — PASS
- entities: 4/4 = 1.0000 — PASS
- methods: 4/4 = 1.0000 — PASS
- tasks: 6/6 = 1.0000 — PASS
- jobs: 4/4 = 1.0000 — PASS
- steps: 9/9 = 1.0000 — PASS
- Overall: PASS

## Machine spec (Q14)
- system: Windows
- release: 11
- version: 10.0.26200
- machine: AMD64
- processor: Intel64 Family 6 Model 154 Stepping 4, GenuineIntel
- cpu_count: 12
- ram: 16068 MiB total

## Deviation note
Real-repo metrics (3 OFBiz modules, ~5000+ triples) are unmeasured: no dataset at
dataset/apache-ofbiz-24.09.07 and no gate marker. Fixture-tree run is 100% green;
graph-size verdict is N/A until the Task 1.9 real-data run.
