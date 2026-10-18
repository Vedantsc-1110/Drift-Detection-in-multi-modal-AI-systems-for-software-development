# Experiment: Deterministic vs Probabilistic vs Hybrid Context Identification

> This is the historical baseline evaluation, not the merged contract/drift
> acceptance suite. The real OFBiz checkout and regenerated baseline store are
> prerequisites for source-backed reruns. See [the run guide](../../HowToRun.md).

Compares three arms on the SAME sample artifacts, scored against the SAME
manually adjudicated ground truth. No metric is computed without a human
verdict behind it; unreviewed items are reported as pending, never as correct.

## Arms

- **A deterministic**: `extract.py` (+ `build_graph.py`) output for the sample files.
- **B probabilistic**: `prob.py propose` output for the same files (stub-labeled
  unless a live Ollama run is recorded; stub numbers measure plumbing only).
- **C hybrid**: deterministic graph (unchanged) + `accepted` proposals as a
  sidecar. Rejected/unreviewed proposals never enter C.

## Metrics (see `eval-schema.json`)

Extracted, adjudicated, correct (verdict=correct vs source), unsupported
(verdict=incorrect), pending, accuracy = correct/adjudicated (null when empty),
provenance coverage (facts with file+line, proposals with evidence+model+
confidence), repeatability (rerun content agreement, timestamps excluded),
execution seconds (single timed runs, not benchmarks), SHACL validation
(A and C share the deterministic graph; B is n/a).

## Workflow

```
eval.py init   --facts … --proposals … --sample samples/<s>.json [--max-items N --seed S] --out ground-truth/<s>.template.jsonl
# ... human reviews the template: fill verdict/reviewer/note, save as <s>.adjudicated.jsonl ...
eval.py score  --template ground-truth/<s>.adjudicated.jsonl --facts … --proposals … --graph … --shapes … --sample samples/<s>.json [--timings … --facts-repeat … --proposals-repeat …] --out results/<s>.results.json
eval.py report --results results/<s>.results.json --out-md results/comparison-report.md
```

Current sample: `samples/order-reservations.json`
(`services_reservations.xml`, 8 A-facts + 1 stub proposal, 9/9 adjudicated).

## Adding a future dataset

1. Add `samples/<name>.json`: `{name, description, component, files[], proposal_source}`.
2. Run `eval.py init` for it (use `--max-items` + `--seed` for large scopes;
   record both in the results notes).
3. Adjudicate every template item against source evidence (verdict =
   `correct` | `incorrect`; never leave test-driven guesses).
4. Run `score` + `report`; commit template, adjudicated file, results, report.
