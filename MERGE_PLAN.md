# Integration plan and current repository layout

Reviewed 2026-10-17. The project is consolidated under
`enterprise-context-graph/`; the four originally planned sibling part folders
and branch-specific layouts are historical. Do not use their old import paths
or test filenames as current run instructions.

## Current layout

```text
EDITY/
  Context_Drift_Detection_Complete_Proposal.docx
  CONTRACT.md
  PART1_PLAN.md ... PART4_PLAN.md
  OPEN_QUESTIONS.md
  enterprise-context-graph/
    src/contextgraph/       # shared parsers, contract graph, API
      prob/                 # Part 2 processors and model interfaces
      drift/                # Part 4 components
    ontology/               # baseline and contract vocabularies/shapes
    dashboard/              # HTML, CSS, JS, vendored renderer
    tests/fixtures/         # independent component inputs
    scripts/run_offline_tests.py
    serve_contract_api.py
    README.md
    HowToRun.md
    BRUTAL_REVIEW.md
```

## Existing integration path

1. Part 1's `contract_pipeline` writes structural/Airflow/CI Turtle files.
2. Part 2 processors produce semantic/document/contract/filing graphs. Existing
   integration tests inject recorded responses; a full live run remains work.
3. `ContractStore` loads named graphs. Bridge discovery and SHACL validation are
   separate Python operations. The server loads provided artifacts; it does not
   automatically run extraction or discover bridges.
4. The browser explorer displays facts and their available evidence. It has no
   live event feed or active-agent registry.
5. Part 4 receives supplied version graphs and snapshots, computes changes,
   recommendations, and patches. Component tests exercise Git detection,
   incremental extraction hooks, versions, and event logging. They are not one
   continuously running orchestration service.

## Verification gates

From `enterprise-context-graph/`:

```powershell
python scripts/run_offline_tests.py
python -m pytest tests/test_merged_end_to_end.py -q
python serve_contract_api.py --demo
```

Browser verification is opt-in; see [the run guide](HowToRun.md).
The unrestricted suite requires the unbundled OFBiz checkout. Dataset source
validation also requires that checkout. Missing prerequisites must remain visible.

## What completion still requires

The old merge test uses fixture-generated outputs and a controlled OFBiz rename.
It does not implement or verify the supplied Word proposal's FinPay, VTOP, and
MediTrack scenarios, five specialized drift workflows, EARS registry, real agent
notification, six executable remediation actions, or live event/agent dashboard.
Its section 7.2/7.3 citations refer to the earlier extraction brief, not Revision 2.

Keep fixture conformance, real-data extraction quality, and operational agent
behavior as separate acceptance gates. A fixture test pass cannot stand in for a
missing live benchmark. Use [the status matrix](docs/implementation-status.md)
and [the review](BRUTAL_REVIEW.md) to track these gaps.
