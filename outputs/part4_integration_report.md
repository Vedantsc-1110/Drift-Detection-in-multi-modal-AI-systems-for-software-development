# Part 4 integration run report (§11.2)

> **Archived measurement.** Scope, fixtures, and extraction timestamps below
> belong to the recorded run; these are not current whole-project acceptance
> results. See the current README, run guide, and brutal review.

- Agents: 21 (2 affected, 19 undisturbed) — restart reduction 0.9048 (metric: > 0.90) — PASS
- Detection latency: 347.5ms at 520 triples (metric: < 500ms) — PASS
- Precision: formatting-only re-serialization → zero findings — PASS
- Remediation mapping: 0.0/0.1/0.35/0.6/0.85 → CONTINUE/REFRESH/RE-BRIEF/RE-PLAN/ROLLBACK — PASS
- Determinism: 30 runs, single verdict SHA-256 — PASS

## Machine spec
- system: Windows
- release: 11
- version: 10.0.26200
- machine: AMD64
- processor: Intel64 Family 6 Model 154 Stepping 4, GenuineIntel
- cpu_count: 12
- ram: 16068 MiB total

## Deviation notes
- Demo scale (~500 triples) via deterministic padding; scenario
  semantics (A 0.725, B 0.0, C 0.82) from Task 4.9 fixtures.
