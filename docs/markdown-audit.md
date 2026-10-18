# Markdown audit

Reviewed 2026-10-17.

The review covered **78 original product Markdown files**: seven workspace
plans/contracts and 71 files in the runnable project, including the distribution
copies. Agent tooling/skills under `.agents/` and `.claude/`, Git internals,
caches, and locally installed browser tooling are outside this product-document
count. The supplied Word proposal was text-extracted and compared separately.

## Findings and corrections

1. The supplied Word proposal is Revision 2 and differs from the earlier PART
   brief. Its section 7 is the stack, not the cited extraction Algorithms 1–3.
   Added explicit reconciliation; preserved earlier task IDs as historical targets.
2. The four part directories and several test/entrypoint paths did not exist.
   Updated plans to real consolidated modules, corrected test filenames, and
   replaced the broken standalone uvicorn instruction with the server CLI.
3. The old README described only the baseline and said no later layers existed.
   Rewrote it and the run guide around implemented behavior and actual limits.
4. Open questions already had code-level decisions. Replaced stale questions
   with those decisions and kept genuinely unresolved product/research gaps.
5. Metadata claims implied universal per-triple coverage; implementation usually
   attaches metadata to subjects and verifies only a subset. Corrected contract wording.
6. The dependency-scope report counted 112 base entities yet claimed they were
   outside scope, and labeled mixed parameter totals directly extracted. Fixed
   the report generator and rerendered archived JSON/MD from existing artifacts.
7. Baseline documentation was easily mistaken for current whole-project scope.
   Added scope notices and current links; kept accurate baseline restrictions.
8. Archived fixture scores were presented without a prominent scope distinction.
   Labeled them archived; did not turn failed/unrated benchmarks into successes.
9. The restart metric is an undisturbed-agent proxy, and latency excludes upstream
   work. Corrected plan wording and documented measurement limits.
10. Dataset prose implied OFBiz was locally included. It is unbundled. Recorded
    missing-source prerequisites and kept the frozen corpus copies intact.

## Validation and boundaries

- Relative Markdown links were checked after edits; no broken local links remain.
- Referenced `test_*.py` names in the four root plans now resolve in the project.
- The 20 source corpus documents and 20 distribution Markdown copies are identical.
- Corpus validation confirms 20 documents, 72 facts, 18 negatives, and 78 links,
  but still fails 40 OFBiz source-path checks without the external checkout.
- No archived accuracy score, source evidence, ground-truth label, or negative case
  was altered to improve a benchmark. Report scope prose was corrected from the data.
- Planning targets are requirements, not completed work. Unsupported claims remain
  visible in the [brutal review](../BRUTAL_REVIEW.md) and
  [implementation status](implementation-status.md).

## Original file inventory

Paths are relative to the workspace root.

| Original Markdown file | Review disposition |
|---|---|
| `CONTRACT.md` | Corrected current locations, decisions, or integration scope; earlier brief distinguished from Revision 2. |
| `enterprise-context-graph/dataset/README.md` | Corrected external-source availability, evaluation status, and baseline versus newer AST scope. |
| `enterprise-context-graph/dataset/synthetic-enterprise/designs/D01-order-management-service-design.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/designs/D02-validation-processing-design.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/designs/D03-fulfillment-service-design.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/designs/D04-payment-integration-design.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/designs/D05-customer-party-integration-design.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/policies/P01-order-approval-policy.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/policies/P02-payment-authorization-policy.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/policies/P03-order-cancellation-policy.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/policies/P04-customer-data-access-policy.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/policies/P05-fulfillment-inventory-policy.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/README.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/requirements/R01-order-to-cash-requirements.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/requirements/R02-order-creation-validation-requirements.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/requirements/R03-fulfillment-inventory-requirements.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/requirements/R04-payment-status-requirements.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/requirements/R05-customer-party-requirements.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/sops/S01-order-processing-sop.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/sops/S02-exception-handling-procedure.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/sops/S03-payment-reconciliation-procedure.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/sops/S04-fulfillment-escalation-procedure.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dataset/synthetic-enterprise/sops/S05-architecture-decision-record.md` | Reviewed as synthetic evidence; metadata/IDs/cross-links and distribution parity checked; evidence text preserved. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/DATASET_CARD.md` | Frozen-package scope clarified; external OFBiz/source-validation prerequisite recorded. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/LICENSES_AND_SOURCES.md` | Reviewed package/source descriptions; license text preserved; no new rights or legal conclusions asserted. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/ofbiz/README.md` | Frozen-package scope clarified; external OFBiz/source-validation prerequisite recorded. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/README.md` | Frozen-package scope clarified; external OFBiz/source-validation prerequisite recorded. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/designs/D01-order-management-service-design.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/designs/D02-validation-processing-design.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/designs/D03-fulfillment-service-design.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/designs/D04-payment-integration-design.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/designs/D05-customer-party-integration-design.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/policies/P01-order-approval-policy.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/policies/P02-payment-authorization-policy.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/policies/P03-order-cancellation-policy.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/policies/P04-customer-data-access-policy.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/policies/P05-fulfillment-inventory-policy.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/README.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/requirements/R01-order-to-cash-requirements.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/requirements/R02-order-creation-validation-requirements.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/requirements/R03-fulfillment-inventory-requirements.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/requirements/R04-payment-status-requirements.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/requirements/R05-customer-party-requirements.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/sops/S01-order-processing-sop.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/sops/S02-exception-handling-procedure.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/sops/S03-payment-reconciliation-procedure.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/sops/S04-fulfillment-escalation-procedure.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/dist/enterprise-context-dataset-v1.0/synthetic-enterprise/sops/S05-architecture-decision-record.md` | Frozen corpus copy checked against source; kept unchanged. |
| `enterprise-context-graph/docs/context-ontology.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/docs/ofbiz-context-extraction.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/docs/oxigraph-store.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/docs/part1-evaluation.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/docs/probabilistic-layer.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/docs/provenance-model.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/docs/rdf-graph.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/docs/scope-comparison.md` | Marked as baseline/early-experiment documentation; current implementation linked. |
| `enterprise-context-graph/evaluation/README.md` | Clarified baseline-only evaluation and source/store prerequisites. |
| `enterprise-context-graph/experiments/context-identification/README.md` | Clarified baseline-only evaluation and source/store prerequisites. |
| `enterprise-context-graph/experiments/context-identification/results/comparison-report.md` | Reviewed existing nine-item stub experiment; already explicitly excludes live LLM quality claims; retained. |
| `enterprise-context-graph/HowToRun.md` | Rewritten with current UI entrypoint, dependency scopes, validation commands, and prerequisites. |
| `enterprise-context-graph/outputs/evaluation/part1-evaluation.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/outputs/merged_end_to_end_report.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/outputs/order-context-report.md` | Fixed generator's false scope narrative; JSON/MD rebuilt from archived RDF and facts, counts retained. |
| `enterprise-context-graph/outputs/order-report.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/outputs/part1_integration_report.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/outputs/part2_integration_report.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/outputs/part3_integration_report.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/outputs/part4_integration_report.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/outputs-deps/order-context-report.md` | Fixed generator's false scope narrative; JSON/MD rebuilt from archived RDF and facts, counts retained. |
| `enterprise-context-graph/outputs-deps/order-report.md` | Marked archived fixture/baseline measurement; original results retained (Part 2 percent typo corrected). |
| `enterprise-context-graph/README.md` | Rewritten with current UI entrypoint, dependency scopes, validation commands, and prerequisites. |
| `enterprise-context-graph/tests/fixtures/docs/procurement_policy.md` | Reviewed as controlled synthetic extractor input; preserved so tests keep their original evidence. |
| `MERGE_PLAN.md` | Corrected current locations, decisions, or integration scope; earlier brief distinguished from Revision 2. |
| `OPEN_QUESTIONS.md` | Corrected current locations, decisions, or integration scope; earlier brief distinguished from Revision 2. |
| `PART1_PLAN.md` | Corrected current locations, decisions, or integration scope; earlier brief distinguished from Revision 2. |
| `PART2_PLAN.md` | Corrected current locations, decisions, or integration scope; earlier brief distinguished from Revision 2. |
| `PART3_PLAN.md` | Corrected current locations, decisions, or integration scope; earlier brief distinguished from Revision 2. |
| `PART4_PLAN.md` | Corrected current locations, decisions, or integration scope; earlier brief distinguished from Revision 2. |
