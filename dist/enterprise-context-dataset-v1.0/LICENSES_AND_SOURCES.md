# Licenses and Sources

## Apache OFBiz (referenced, not redistributed in dist/)

- Source: Apache OFBiz, version 24.09.07 (`dataset/apache-ofbiz-24.09.07`).
- License: Apache License 2.0 (see `LICENSE` and `NOTICE` in the OFBiz tree).
- The dist/ package intentionally omits the ~180MB OFBiz tree; see
  `ofbiz/README.md` for version, scope, and reproduction steps.
- No OFBiz code is copied into the synthetic documents (only identifier
  names such as service/entity titles, which are factual references).

## Synthetic enterprise corpus (included)

- Original fictional content created for this project (Meridian Retail Group).
- No real company documents, no real personal data, no third-party text.
- May be used freely within the project for extraction research and evaluation.
- Document authors are fictional team names; dates are fixed fictional dates.

## Deterministic extraction outputs (referenced)

- Baseline counts (10,204 facts, 117,788 triples) are measurements of the
  project pipeline over OFBiz 24.09.07, not redistributed artifacts.
- Reproduce with the commands in `ofbiz/README.md`.
