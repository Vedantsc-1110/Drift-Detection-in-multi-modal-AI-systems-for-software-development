# Enterprise Context Identification Dataset (v1.0) — Distributable Package

> **Frozen v1.0 dataset description.** Counts and baseline limitations describe
> the original extraction. OFBiz source and development tools are not included
> in this package; full source validation requires the external pinned checkout.
> Later contract/AST/dashboard implementation does not change these baseline
> measurements. The current project review is in `BRUTAL_REVIEW.md` in the development repository.

This package contains everything a teammate needs for the next
(probabilistic/semantic) evaluation stage, without the development repo.

## Contents

- `ofbiz/` — README + manifest describing the referenced Apache OFBiz 24.09.07
  source, extraction scope, and reproduction steps. The ~180MB OFBiz tree
  itself is NOT copied (see `ofbiz/README.md` and `LICENSES_AND_SOURCES.md`).
- `synthetic-enterprise/` — 20 synthetic documents (DOCX primary + MD source)
  across requirements/designs/policies/sops, plus `ground_truth/`
  (72 fact mappings + 18 negative cases), README, manifest, and statistics.
- `README.md` — this file (short version; full guide in the project
  `dataset/README.md`).
- `DATASET_CARD.md` — dataset card.
- `LICENSES_AND_SOURCES.md` — licenses and sources.

## Real vs synthetic

Real: Apache OFBiz 24.09.07 and its deterministic extraction (services,
entities, relations, ECAs, provenance, unresolved report). Synthetic: the
fictional Meridian Retail Group, all 20 documents, thresholds, roles, timers,
codes, and business interpretations. In-document labels ([OFBiz-existing],
[OFBiz-reference-out-of-scope], [SYNTHETIC]) keep them apart.

## Next-stage use

Run probabilistic extraction over `synthetic-enterprise/` documents, score
claims against `ground_truth/fact-mappings.yaml` (DIRECT/INDIRECT/SYNTHETIC/
UNRESOLVED) and `ground_truth/negative_cases.yaml` (UNSUPPORTED/NOT_FOUND/
PARTIALLY_SUPPORTED) to measure semantic recovery and hallucination
resistance. Do not modify OFBiz or the deterministic baseline.

## Validation

The package was validated with `scripts/validate_dataset.py` (20 docs,
5/5/5/5 split, metadata, cross-refs, OFBiz refs verified against extraction,
72 facts, 18 negatives) before zipping.
