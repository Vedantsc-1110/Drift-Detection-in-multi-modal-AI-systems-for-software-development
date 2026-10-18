# Context Atlas — enterprise context graphs and drift experiments

This project extracts facts from code and documents, stores them in RDF named
graphs, and provides an interactive evidence explorer. A separate Python drift
module compares supplied versions and agent snapshots and returns remediation
recommendations and patches.

The problem is stale agent context: code or requirements change while another
agent continues to use an older understanding. The proposed solution is to trace
dependencies, identify affected work, and recommend the smallest correction.
The repository currently demonstrates the building blocks with fixtures. It does
not control running agents or provide a complete live drift platform.

## Open the UI

From this directory, in PowerShell or a terminal:

```powershell
python -m pip install -r requirements.txt
python serve_contract_api.py --demo
```

Open **http://127.0.0.1:8000/dashboard**. The workspace combines a source navigator,
an interactive dark graph canvas, and an evidence inspector. It explains the
problem and solution, labels demo data, and loads assets locally. Explore node
neighborhoods with Focus/Clear, switch between Graph and List, filter by source,
confidence, method, or name, and export the visible graph as JSON. The list also
works with a keyboard or when the renderer is unavailable. On phones, secondary
filters are under Refine results. Do not open `dashboard/index.html` directly.

`requirements.txt` is the single dependency file for the dashboard, extraction,
and tests. It includes the spaCy English model from its official release wheel.
Browser tests use an installed Edge browser, or a separate Playwright browser
download; see the run guide.

Preview the redesigned workspace: [desktop](outputs/ui-redesign/desktop.png) ·
[mobile](outputs/ui-redesign/mobile.png).

Use `--data <directory>` instead of `--demo` to load contract pipeline outputs.
The loader accepts all seven canonical files plus `bridges.ttl`, and the original
`structural.ttl` / `semantic.ttl` fixture aliases. It does not automatically create
bridges. It reads source files into a temporary store without clearing any existing
project store.

## What is implemented

| Area | Implementation | Current evidence |
|---|---|---|
| Structural extraction | `contract_pipeline.py`, XML, Java AST, Airflow, YAML parsers | Small fixture trees and offline integration tests |
| Semantic extraction | `prob/`, Groq/Ollama interfaces, document/contract/filing processors | Recorded model responses; live quality targets unproven |
| RDF storage and API | `ContractStore`, ontology, SHACL shapes, predefined queries | Contract fixtures; metadata is primarily attached to subjects |
| Browser explorer | `dashboard/`, `contract_api.py` | Real-browser checks for interactions, failures, and mobile layout |
| Drift experiments | `drift/` | Controlled rename scenario; caller-supplied snapshots and labels |

There are two graph formats: the earlier `extract.py` / `build_graph.py` baseline
uses `http://example.org/ofbiz/0.1/` and a default graph. The contract pipeline uses
`http://context.example.org/` and named graphs. The dashboard consumes the latter;
the archived `outputs-deps/order-graph.ttl` is not a drop-in dashboard input.

## Read next

- [Run guide](HowToRun.md) — minimal UI setup, extraction, tests, and prerequisites.
- [Implementation status](docs/implementation-status.md) — maps PART 1–4 to real files and reconciles the Word proposal.
- [Brutal review](BRUTAL_REVIEW.md) — evidence, defects fixed, and candid remaining limitations.
- [Markdown audit](docs/markdown-audit.md) — findings across the original project Markdown files.
- [PART 1](PART1_PLAN.md), [PART 2](PART2_PLAN.md), [PART 3](PART3_PLAN.md),
  [PART 4](PART4_PLAN.md), and the [shared contract](CONTRACT.md) — original task specifications.
- [Complete proposal](Context_Drift_Detection_Complete_Proposal.docx) — the supplied Revision 2 design.

The supplied `Context_Drift_Detection_Complete_Proposal.docx` describes a different,
broader Revision 2 system than the older PART plans. Its spec registry, all five
drift types, six remediation levels, agent notification, and live event timeline
are not delivered by the current implementation. Passing fixture tests does not
establish those capabilities.

The earlier enterprise graph baseline came from
[enterprise-context-graph](https://github.com/ShubhamBadadale/enterprise-context-graph).
