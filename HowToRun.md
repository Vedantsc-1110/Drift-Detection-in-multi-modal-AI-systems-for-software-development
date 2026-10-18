# Run Context Atlas locally

Commands below run from the repository root. Use Python 3.11 or later.
The interface runs without external datasets, model keys, or a spaCy model.

## 1. Start the dashboard

```powershell
python -m pip install -r requirements.txt
python serve_contract_api.py --demo --port 8000
```

Open **http://127.0.0.1:8000/dashboard**. `/` also redirects there. The badge
identifies curated demo fixtures; the counts reflect the loaded and filtered data.
All fonts, CSS, application JavaScript, and the graph renderer work without an
external CDN. Press Ctrl+C in the server terminal to stop.

To inspect extracted contract graphs:

```powershell
python serve_contract_api.py --data outputs/demo-part1 --port 8000
```

Accepted files: `ofbiz_structural.ttl`, `airflow.ttl`, `cicd.ttl`,
`ofbiz_semantic.ttl`, `document_semantic.ttl`, `cuad.ttl`, `edgar.ttl`, and
`bridges.ttl`. Only files that exist are loaded. An empty/unrecognized directory
is an error. The original API fixture aliases `structural.ttl` and `semantic.ttl`
are supported. The server does not run extraction or bridge discovery itself.
Its temporary store is rebuilt at startup; input files and existing stores are
not modified.

## 2. Use the explorer

1. Start in the graph workspace. A connected service is selected automatically
   so the evidence inspector immediately shows a useful example.
2. Browse the source navigator or search for a service, task, or policy. On a
   phone, open **Refine results** for confidence, method, and source filters.
3. Select a node for its source, location, extraction method, and confidence.
   Select an arrow for its recorded relationship and endpoint links.
4. Use **Focus** to bring the selected neighborhood into view, or **Clear** to
   restore the full graph's emphasis. Drag, zoom, fit, and auto-layout controls
   are available on the canvas.
5. Switch between **Graph** and **List**. The same filtered nodes are available
   through the list with keyboard navigation, including when rendering fails.
6. Press `/` outside an input to search, or Escape outside an input to clear
   selection. Search applies on Enter/Apply filters; dropdown filters apply
   when changed. Reset clears filters; browser Back/Forward restores them.
7. Use **Export graph** to download the displayed nodes, relationships, and
   successfully applied filters as JSON. An unsuccessful refresh retains the
   previous data and its actual applied filters.

Only arrows with two visible endpoints are drawn. Selecting one source graph also
restricts arrows to that graph; cross-source arrows live in `urn:bridges`.
Searching one service can therefore hide its neighbors. A blank evidence field is
shown as unavailable, never guessed. A node's provenance does not prove an arrow.

## 3. Dependency setup

```powershell
python -m pip install -r requirements.txt
```

`requirements.txt` is the only dependency file. It includes the dashboard,
extraction libraries, pytest, Playwright, and `edgartools`. The spaCy English
model uses its official release wheel URL because the model is not distributed
as a regular PyPI package. Installation needs network access, including access
to GitHub releases; the dashboard itself runs locally without model keys.
The CUAD processor currently reads the repository's adapted JSON schema rather
than downloading the original Hugging Face dataset. Live SEC fetching needs an
EDGAR identity configured through `edgartools` and is not part of offline tests.

## 4. Run self-contained checks

```powershell
python scripts/run_offline_tests.py
```

The runner selects fixture and pure-function tests, excludes the twelve modules
requiring an external OFBiz checkout, and deselects the live Ollama test. Browser
and store-dependent checks report their missing prerequisites as skips. Test
totals depend on installed optional packages; skips are not passes.

The original 2026-10-17 run passed **193 tests**, with 15 skips and one live test
deselected. Six skips were opt-in browser checks; nine required a regenerated
baseline store. The browser suite separately passed six checks. These figures
describe this environment and scope, not the unrestricted full suite.

The redesigned dashboard was verified on **2026-10-18** with **18 passing browser
checks** and **14 passing API/HTML regression checks**. Browser coverage includes
canvas selection, dragging, zoom, readable initial layout, source filtering,
Graph/List navigation, keyboard controls, failure recovery, JSON export, and
mobile evidence navigation. See the [desktop preview](outputs/ui-redesign/desktop.png)
and [mobile preview](outputs/ui-redesign/mobile.png).

The publication check on **2026-10-18** reran the offline suite: **193 passed,
27 skipped, and one live test deselected**. The skips were 18 opt-in browser
checks and nine checks requiring a regenerated baseline store. The browser
checks passed separately as described above.

For browser verification, install Playwright and use an installed Edge browser:

```powershell
python -m pip install -r requirements.txt
$env:RUN_BROWSER_TESTS='1'
python -m pytest tests/test_dashboard_browser.py -q
Remove-Item Env:RUN_BROWSER_TESTS
```

The browser tests intercept requests into the actual FastAPI app, so a separate
server and internet access are unnecessary. They write desktop/mobile screenshots
under `.tools/ui/`. Set `PLAYWRIGHT_CHANNEL=chrome` for an installed Chrome browser,
or install Chromium with `python -m playwright install chromium` and set
`PLAYWRIGHT_CHANNEL=chromium`. Browser binaries are not installed by pip.

## 5. Generate Part 1 contract outputs

```powershell
$env:PYTHONPATH='src'
python -m contextgraph.contract_pipeline --root tests/fixtures --out outputs/demo-part1 --generated-at 2026-01-01T00:00:00+00:00
python serve_contract_api.py --data outputs/demo-part1
```

This produces three Turtle files and `contract-manifest.json`. The pipeline does
a full rebuild; its scanner records changed-file hashes but it is not a complete
incremental fact cache. On bash use `export PYTHONPATH=src` instead.

Part 2 processors are Python interfaces under `src/contextgraph/prob/`; their
tests inject recorded responses. A Groq key alone does not turn the fixture tests
into live evaluation. No single production CLI currently runs all semantic
processors on the planned full corpus.

## 6. Run the drift example

```powershell
python -m pytest tests/test_drift_scenario.py tests/test_drift_integration.py -q
```

The canonical fixture produces A 0.725 → RE-PLAN, B 0 → CONTINUE, C 0.82 →
RE-PLAN. These are recommendations computed from supplied graphs and labels.
No real agent is notified, replanned, rolled back, or restarted.

## 7. Real-data validation and the full suite

The Apache OFBiz tree is deliberately unbundled. Most baseline integration tests
expect `dataset/apache-ofbiz-24.09.07`; some parser tests accept `OFBIZ_ROOT`.
Install the pinned source at the default path for the complete suite. Rebuild the
baseline graph/store using the commands in [the evaluation guide](docs/part1-evaluation.md).

```powershell
python -m pytest tests -q
python scripts/validate_dataset.py --stats-out .tools/dataset-statistics.json
```

The initial unrestricted run in this checkout had 10 failures and 71 setup errors
because the real source tree was absent. The dataset validator likewise reports
40 unavailable source references. The corpus structure is present: 20 documents,
72 mapped facts, 18 negatives, and identical Markdown distribution copies. Full
source validation remains a prerequisite, not a passed check.

## API and troubleshooting

`/docs` describes the API. `/graph/summary`, `/graph/nodes`, and `/node` serve the
explorer. The six predefined question endpoints remain available. The invoice
I/O endpoint returns parameter names, not verified database read/write behavior.
`POST /sparql` is a local developer query interface, without authentication,
query budgeting, or a production access-control boundary.

- No page: keep the server terminal open and use its printed port.
- No canvas: use the served `/dashboard` URL, not a `file://` HTML tab. The node
  directory remains usable if the vendor script fails.
- No matches: reset filters. Older baseline Turtle uses another vocabulary.
- No bridges: load a `bridges.ttl` artifact produced by bridge discovery.
- PyPDF2 and current Starlette/httpx integrations emit deprecation warnings in
  this environment. They do not fail the verified checks; dependency migration
  remains work to do.
