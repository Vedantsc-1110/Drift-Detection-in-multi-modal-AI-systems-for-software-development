# Dataset Card — Enterprise Context Identification Dataset (v1.0)

> **Frozen v1.0 dataset description.** Counts and baseline limitations describe
> the original extraction. OFBiz source and development tools are not included
> in this package; full source validation requires the external pinned checkout.
> Later contract/AST/dashboard implementation does not change these baseline
> measurements. The current project review is in `BRUTAL_REVIEW.md` in the development repository.

- Dataset name: Enterprise Context Identification Dataset
- Version: 1.0
- Purpose: Evaluate deterministic AND probabilistic enterprise-context
  extraction: does the Context Graph represent what exists, how components
  relate, what artifacts mean, and where knowledge came from — without
  hallucinating?
- Real component: Apache OFBiz 24.09.07 (read-only primary artifact; order
  component plus order-entitymodel.xml scope; 467 services, 112 base + 55
  view entities, 567 relations, 111 ECAs, 10,204 facts, 117,788 triples).
- Synthetic component: 20 controlled documents about the fictional Meridian
  Retail Group (5 requirements, 5 designs, 5 policies, 5 SOPs/decisions;
  DOCX primary + MD source; 9,926 MD words).
- Document types: requirements (R01–R05), designs (D01–D05), policies
  (P01–P05), SOPs/decision record (S01–S05), with explicit cross-document IDs.
- Ground-truth construction: 72 facts with statement, subject/predicate/
  object, support_type (DIRECT 22 / INDIRECT 13 / SYNTHETIC 31 / UNRESOLVED 6),
  OFBiz file+location where applicable, and honesty notes. Business readings
  over real artifacts are INDIRECT, never DIRECT.
- Negative examples: 18 cases (NOT_FOUND 6 / UNSUPPORTED 9 /
  PARTIALLY_SUPPORTED 3) covering nonexistent services/entities, wrong keys,
  fabricated rules, and false guarantees.
- Intended tasks: (1) deterministic structure/provenance evaluation (done);
  (2) probabilistic semantic extraction scored on support types;
  (3) hallucination-resistance measurement on negatives.
- Known limitations: order scope only; product/party masters unresolved by
  design; Java/Groovy bodies unparsed; synthetic docs controlled, not real
  enterprise text; doc lengths vary (~340–880 words, ~2 pages in DOCX).
- Reproducibility: deterministic generators (`scripts/build_synthetic_corpus.py`);
  `scripts/validate_dataset.py` exits non-zero on any inconsistency; statistics
  computed from files, never fabricated. OFBiz tree pinned at 24.09.07.
- Ethical/privacy: no real personal data; fictional authors/roles/dates;
  no real company affiliation.
- License/sources: OFBiz under Apache License 2.0 (not redistributed in
  dist/); synthetic corpus original fictional research content. See
  `LICENSES_AND_SOURCES.md`.
