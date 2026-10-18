# PART 2 PLAN — Probabilistic Extraction (Proposal §7.2 Stage 2, Algorithm 2)

> **Status reviewed 2026-10-17.** This is the earlier enterprise-extraction
> task plan. Its section numbers refer to a brief different from the supplied
> `Context_Drift_Detection_Complete_Proposal.docx` Revision 2. Task acceptance
> targets below are not a claim of completion. See the
> [implementation status](docs/implementation-status.md)
> and [brutal review](BRUTAL_REVIEW.md).

Part 2 lives in `src/contextgraph/prob/`. Tests use
recorded model responses. Live full-corpus accuracy and corroboration targets
remain unproven; see `outputs/part2_integration_report.md` inside the project.

Hard rules:
- Stack per §8: spaCy 3.x (NER), Groq API (Llama 3.3 70B) as primary LLM,
  Ollama (caller-configured installed model) as local fallback, python-docx / PyPDF2 (document text),
  HuggingFace `datasets` (CUAD: "theatticusproject/cuad", split "test"),
  edgartools (SEC 10-K), rdflib 7.x (Turtle output).
- Every fact: ctx:confidence (0.0–1.0), ctx:factType "probabilistic",
  ctx:extractedBy, ctx:supportType where applicable, PROV-O provenance
  (prov:wasGeneratedBy, prov:hadPrimarySource, ctx:sourceLocation,
  prov:generatedAtTime) per CONTRACT.md §5.
- Corroboration rule (Algorithm 2 "Response Validation"): LLM claim matching a
  deterministic fact → confidence boosted to 0.95+; uncorroborated → clamps
  LLM raw confidence into the 0.70–0.85 band (not a calibrated probability).
- LLM calls MUST be mockable: all unit tests run without network/keys
  (fixtures of recorded LLM JSON responses). Live Groq/Ollama calls happen only
  in integration tasks.

Current folder layout (workspace view; task commands run inside the project):
```text
enterprise-context-graph/
  src/contextgraph/prob/   # clients, NER, extractors, corroboration, Turtle
  tests/fixtures/{llm,docs,cuad,edgar}/
  tests/test_*.py
  outputs/
```

## TASK 2.1 — LLM client layer + JSON validation
- Goal: Primary/fallback LLM inference with validated JSON output (Alg. 2).
- Inputs: Groq API key (env var) or local Ollama; fixture prompts.
- Steps: `src/contextgraph/prob/groq_client.py` (Llama 3.3 70B via Groq), `src/contextgraph/prob/client.py`
  (local, offline), `src/contextgraph/prob/router.py` (primary Groq → fallback Ollama on
  failure), `src/contextgraph/prob/json_validator.py` (reject malformed responses; parse claims
  as subject–predicate–object triples), `src/contextgraph/prob/prompts.py` (structured extraction
  prompt: context = NER results + deterministic facts; task "Extract business
  purpose, domain concepts, business rules, relationships"; output = JSON;
  grounding instruction "Only reference entities that appear in the provided
  context").
- Output: typed `LlmResponse` objects; validation errors surfaced, never
  silently dropped.
- TEST GATE: `pytest tests/test_llm_clients.py` — router falls back correctly on
  simulated Groq failure; validator rejects malformed JSON and accepts valid
  fixture responses; unit tests use mocks only.
- DONE CRITERIA: green without network.

## TASK 2.2 — spaCy NER preprocessing + chunking
- Goal: Grounding entities from text (Alg. 2 "Preprocessing").
- Inputs: fixture document text, contract text, filing text.
- Steps: `src/contextgraph/prob/ner.py`: extract organizations, systems, roles, dates,
  jurisdictions via spaCy; `src/contextgraph/prob/chunker.py`: chunk long documents
  into sections.
- Output: NER result structures attached to chunks.
- TEST GATE: `pytest tests/test_ner.py` — fixture entities (org names, dates)
  found; chunker splits a >4 KB fixture at section boundaries.
- DONE CRITERIA: green; spaCy model loading isolated behind a fixture-friendly
  interface.

## TASK 2.3 — Corroboration + confidence assignment
- Goal: Cross-reference LLM claims with deterministic facts (Alg. 2).
- Inputs: fixture Stage-1 .ttl (hand-made, CONTRACT.md-compliant, e.g.
  ctx:findOrders a ctx:Service ...); fixture LLM claims.
- Steps: `src/contextgraph/prob/corroboration.py`: for each claim, check for a matching
  deterministic triple (e.g. LLM "OrderService depends on ProductService" +
  matching tree-sitter import → corroborated → 0.95+). Uncorroborated → raw
  LLM confidence, kept within 0.70–0.85. Assign support types for documents:
  DIRECT / INDIRECT / SYNTHETIC / UNRESOLVED (§7.2 2.2).
- Output: scored, typed claims.
- TEST GATE: `pytest tests/test_corroboration.py` — corroborated claim ≥0.95;
  uncorroborated claim in 0.70–0.85; each support type assigned correctly on
  fixture sentences.
- DONE CRITERIA: green.

## TASK 2.4 — Code semantic extractor (§7.2 2.1)
- Goal: Business meaning for OFBiz modules from Stage-1 summaries.
- Inputs: module summary built from the fixture Stage-1 .ttl (class names,
  method signatures, service names, entity names — exactly what the proposal
  specifies as the LLM input).
- Steps: `src/contextgraph/prob/code_semantic.py`: build structured module summary → LLM
  (Task 2.1) → parse JSON → corroborate (Task 2.3) → triples:
  ctx:businessPurpose, domain concepts (ctx:BusinessConcept +
  ctx:belongsToConcept), business rules (ctx:BusinessRule), inter-module
  dependencies. Record ctx:extractedBy, ctx:confidence, ctx:factType,
  prov:generatedAtTime.
- Output: Named Graph <urn:ofbiz_semantic> triples.
- TEST GATE: `pytest tests/test_code_semantic.py` (mocked LLM) — example fact
  ctx:OrderModule ctx:businessPurpose "..." with extractedBy "llama-3.3-70b"
  and confidence in range appears; corroborated dependency claim ≥0.95.
- DONE CRITERIA: green.

## TASK 2.5 — Synthetic document processor (§7.2 2.2)
- Goal: Policies, rules, procedures from 30–40 enterprise documents.
- Inputs: team-authored fixture documents (DOCX/PDF): requirement specs,
  design docs, procurement policies, meeting notes, compliance docs.
- Steps: `src/contextgraph/prob/documents.py`: python-docx / PyPDF2 text extraction →
  spaCy NER → LLM extraction of business purpose, policy rules, approval
  thresholds, operational procedures, system references → support-type tagging
  (DIRECT/INDIRECT/SYNTHETIC/UNRESOLVED) → triples: ctx:Document, ctx:Policy,
  ctx:BusinessRule; ctx:constrains-ready facts.
- Output: Named Graph <urn:document_semantic> triples.
- TEST GATE: `pytest tests/test_documents.py` (mocked LLM) — each fixture doc
  yields typed facts; every fact has supportType; thresholds/policies extracted
  from the fixture procurement policy.
- DONE CRITERIA: green; 30–40 document set runnable in integration test.

## TASK 2.6 — CUAD contract processor (§7.2 2.3)
- Goal: Contract clauses from the CUAD dataset.
- Inputs: `datasets.load_dataset("theatticusproject/cuad", split="test")`,
  20–30 contracts; pre-annotated clause spans across 41 categories.
- Steps: `src/contextgraph/prob/cuad.py`: load contract text + annotated spans; spaCy NER
  for parties/dates/jurisdictions; LLM relationship extraction; link clauses to
  OFBiz entities where relevant (e.g. "payment terms" → Invoice entity) →
  triples: ctx:Contract, ctx:Clause, ctx:Party; ctx:hasClause, ctx:clauseType,
  ctx:mentionsEntity.
- Output: Named Graph <urn:cuad> triples.
- TEST GATE: `pytest tests/test_cuad.py` — loader consumed a fixture CUAD row;
  each annotated span yields a ctx:Clause with ctx:clauseType; party/date/juris
  NER present; links to fixture OFBiz entities created.
- DONE CRITERIA: green (dataset may be cached; mock at unit level).

## TASK 2.7 — SEC EDGAR filing processor (§7.2 2.4)
- Goal: Sections, risk factors, system mentions from 10-K filings.
- Inputs: edgartools: `Company(cik/ticker)`, `get_filings(form="10-K")`,
  `filing.text()` (~200 KB), `filing.obj()` parsed sections (Item 1, Item 1A...);
  10–20 companies.
- Steps: `src/contextgraph/prob/edgar.py`: fetch filings; extract structured sections
  (business description Item 1, risk factors Item 1A, financial statements);
  LLM extraction of mentioned systems, processes, risks, internal controls;
  link mentions to OFBiz modules (e.g. "order management system" → Order
  module; "accounts receivable" → Accounting module) → triples: ctx:Filing,
  ctx:Section, ctx:RiskFactor; ctx:mentionsProcess, ctx:referencesModule.
- Output: Named Graph <urn:edgar> triples.
- TEST GATE: `pytest tests/test_edgar.py` — fixture filing text (Item 1/1A)
  yields typed sections; module references linked; provenance complete.
- DONE CRITERIA: green (mock edgartools at unit level).

## TASK 2.8 — Triple builder + Turtle output
- Goal: Serialize all probabilistic facts to .ttl (§7.2 Stage 2 output, §8
  rdflib).
- Inputs: scored claims from Tasks 2.4–2.7.
- Steps: `src/contextgraph/prob/ttl_output.py` → outputs/ofbiz_semantic.ttl,
  outputs/document_semantic.ttl, outputs/cuad.ttl, outputs/edgar.ttl.
- Output: four .ttl files.
- TEST GATE: `pytest tests/test_ttl_output.py` — files parse with rdflib;
  every probabilistic fact has confidence in 0.0–1.0, factType, extractedBy,
  prov:generatedAtTime, prov:hadPrimarySource; only documented classes/
  properties used.
- DONE CRITERIA: green.

## TASK 2.9 — Fixtures & unit suite
- Goal: Standalone green suite.
- TEST GATE: `python scripts/run_offline_tests.py` — selected self-contained tests pass, zero network/keys required.
- DONE CRITERIA: clean-room run passes.

## TASK 2.10 — PART INTEGRATION TEST (§11.1 metrics)
- Goal: Live end-to-end run on real data with the LLM layer active.
- Inputs: real Groq key (or Ollama), OFBiz 3-module Stage-1 output (from Part 1
  if available, else Part 2's own contract-compliant fixture), 30–40 synthetic
  documents, 20–30 CUAD contracts, 10–20 EDGAR filings.
- Steps: run all four extractors; measure metrics.
- TEST GATE / metrics (§11.1):
  1. Probabilistic accuracy >80%: team manually rates 50 randomly sampled
     probabilistic facts as correct.
  2. Corroboration rate >60% of probabilistic facts supported by deterministic
     evidence.
  3. ~500+ probabilistic triples (OFBiz core); report actual counts per graph.
- DONE CRITERIA: metrics met or deviation documented.

## TASK 2.11 — HANDOFF — CONTRACT.md compliance
- Goal: Prove outputs conform to the shared contract.
- Steps: `tests/test_prob_contract_compliance.py`: four output .ttl files parse;
  metadata per CONTRACT.md §5; Named Graph targets per §4; file names per §6.
- TEST GATE: green.
- DONE CRITERIA: outputs ready for Parts 3 and 4.
