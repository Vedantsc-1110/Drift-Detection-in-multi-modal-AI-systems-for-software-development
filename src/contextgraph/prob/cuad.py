"""CUAD contract processor (PART2_PLAN Task 2.6, proposal §7.2 2.3).

Annotated clause spans (human ground truth) -> Clause nodes; spaCy NER for
parties/dates/jurisdictions; LLM relationship extraction for entity links
(e.g. payment terms -> Invoice). Span-derived nodes are stamped
probabilistic/DIRECT with extractedBy "cuad-annotator" (annotation, not LLM
output); LLM-derived nodes use the answering model label.

Fixture row schema (subset of theatticusproject/cuad test split):
  {contract_id, title, text, parties: [str],
   clauses: [{category, text, start, end}]}
A real-HF adapter (datasets.load_dataset mapping to this schema) is deferred
to the integration task — unit level uses fixtures only.

Contract-vocabulary note: mentionsEntity is declared Document→Entity; Clause
subjects use it here as contract parts (flagged for contract review).
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS, XSD

from . import ner
from .code_semantic import _extracted_by
from .corroboration import corroborate
from .json_validator import validate_response
from .prompts import EXTRACTION_SYSTEM, build_extraction_prompt

CTX = Namespace("http://context.example.org/")
GRAPH = "urn:cuad"
ANNOTATOR = "cuad-annotator"


def _slug(text: str) -> str:
    return quote(str(text), safe="-_.")


def load_rows(path) -> list:
    """Load + validate fixture CUAD rows (span offsets verified)."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("CUAD fixture must be a JSON array of rows")
    for row in rows:
        for field in ("contract_id", "title", "text"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError("row missing %r" % field)
        for clause in row.get("clauses", []):
            span = clause.get("text", "")
            start, end = clause.get("start"), clause.get("end")
            if not span or row["text"][start:end] != span:
                raise ValueError("clause span mismatch in %s: %r" % (row.get("contract_id"), clause.get("category")))
    return rows


def _stamp(graph: Graph, subject: URIRef, support: str, confidence: float,
           extracted_by: str, generated_at: str, source: str) -> None:
    graph.add((subject, CTX.supportType, Literal(support)))
    graph.add((subject, CTX.confidence, Literal(float(confidence))))
    graph.add((subject, CTX.factType, Literal("probabilistic")))
    graph.add((subject, CTX.extractedBy, Literal(extracted_by)))
    graph.add((subject, PROV.wasGeneratedBy, URIRef(str(CTX) + "CuadExtractor")))
    graph.add((subject, PROV.hadPrimarySource, URIRef(source)))
    if generated_at:
        graph.add((subject, PROV.generatedAtTime, Literal(generated_at, datatype=XSD.dateTime)))


def _label_index(deterministic) -> dict:
    index = {}
    if deterministic is None:
        return index
    for subj in sorted(set(deterministic.subjects(RDF.type, None)), key=str):
        for label in deterministic.objects(subj, RDFS.label):
            index.setdefault(str(label).strip().lower(), subj)
    return index


def extract_contract(row: dict, router, deterministic=None, generated_at: str = "") -> dict:
    """Extract one contract row to contract triples. Router is mockable."""
    source = "file:///cuad/%s" % row["contract_id"]
    entities = ner.extract_entities(row["text"])
    summary = ["clause [%s]: %s" % (c["category"], c["text"]) for c in row.get("clauses", [])]
    prompt = build_extraction_prompt(entities, summary)
    raw, model_name, call_errors = router.complete_json(EXTRACTION_SYSTEM, prompt)
    extracted_by = _extracted_by(model_name)
    response = validate_response(raw, model_name)
    errors = list(call_errors) + list(response["errors"])
    scored = corroborate(response["claims"], deterministic if deterministic is not None else [])

    graph = Graph()
    graph.bind("ctx", CTX)
    index = _label_index(deterministic)
    contract = CTX["Contract/" + _slug(row["contract_id"])]
    graph.add((contract, RDF.type, CTX.Contract))
    graph.add((contract, RDFS.label, Literal(row["title"])))
    _stamp(graph, contract, "DIRECT", 1.0, ANNOTATOR, generated_at, source)

    clause_nodes = {}
    for clause in row.get("clauses", []):
        node = CTX["Clause/" + _slug(row["contract_id"]) + "/" + _slug(clause["category"])]
        graph.add((node, RDF.type, CTX.Clause))
        graph.add((node, RDFS.label, Literal(clause["text"])))
        graph.add((node, CTX.clauseType, Literal(clause["category"])))
        graph.add((contract, CTX.hasClause, node))
        _stamp(graph, node, "DIRECT", 1.0, ANNOTATOR, generated_at, source)
        clause_nodes[clause["category"].strip().lower()] = node
        clause_nodes[clause["text"].strip().lower()] = node

    for party in row.get("parties", []):
        node = CTX["Party/" + _slug(party)]
        graph.add((node, RDF.type, CTX.Party))
        graph.add((node, RDFS.label, Literal(party)))
        _stamp(graph, node, "DIRECT", 1.0, ANNOTATOR, generated_at, source)

    skipped = []
    for claim in scored:
        if claim["predicate"] == "mentionsEntity":
            subject_key = claim["subject"].strip().lower()
            holder = clause_nodes.get(subject_key) or index.get(subject_key) or contract
            entity = index.get(claim["object"].strip().lower())
            if entity is not None:
                graph.add((holder, CTX.mentionsEntity, entity))
            else:
                skipped.append(claim)
        else:
            skipped.append(claim)
    return {"graph": graph, "scored": scored, "skipped": skipped, "errors": errors,
            "extracted_by": extracted_by, "entities": entities}
