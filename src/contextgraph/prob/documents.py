"""Synthetic document processor (PART2_PLAN Task 2.5, proposal §7.2 2.2).

DOCX/PDF/MD/TXT text extraction -> chunking -> spaCy NER -> LLM extraction
-> corroboration support-type tagging -> contract triples (Document, Policy,
BusinessRule; constrains / mentionsEntity where endpoints resolve).

Every minted subject carries supportType (the Document node itself is DIRECT:
its text was read verbatim). Corpus runner handles 30–40+ files.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS, XSD

from . import chunker, ner
from .code_semantic import _extracted_by
from .corroboration import corroborate
from .json_validator import validate_response
from .prompts import EXTRACTION_SYSTEM, build_extraction_prompt

CTX = Namespace("http://context.example.org/")
GRAPH = "urn:document_semantic"

POLICY_PREDICATES = {"policy", "hasPolicy", "policyRule", "requiresApproval", "threshold"}
RULE_PREDICATES = {"businessRule", "hasRule", "procedure", "operationalStep"}


def _slug(text: str) -> str:
    return quote(str(text), safe="-_.")


def read_docx(path: Path) -> str:
    import docx

    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def read_pdf(path: Path) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def read_document(path) -> str:
    """Dispatch text extraction by suffix (.docx/.pdf/.md/.txt)."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)
    if suffix in (".md", ".txt", ".text"):
        return path.read_text(encoding="utf-8")
    raise ValueError("unsupported document type: %s" % path.suffix)


def _stamp(graph: Graph, subject: URIRef, support: str, confidence: float,
           extracted_by: str, generated_at: str, source: str) -> None:
    graph.add((subject, CTX.supportType, Literal(support)))
    graph.add((subject, CTX.confidence, Literal(float(confidence))))
    graph.add((subject, CTX.factType, Literal("probabilistic")))
    graph.add((subject, CTX.extractedBy, Literal(extracted_by)))
    graph.add((subject, PROV.wasGeneratedBy, URIRef(str(CTX) + ("GroqLLMExtractor" if extracted_by == "llama-3.3-70b" else "OllamaLLMExtractor"))))
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


def process_document(doc_id: str, path, router, deterministic=None, generated_at: str = "") -> dict:
    """Extract one document to contract triples. Router is mockable."""
    path = Path(path)
    text = read_document(path)
    source = "file:///" + path.as_posix()
    chunks = chunker.chunk(text)
    entities = []
    for chunk in chunks[:4]:
        entities.extend(ner.extract_entities(chunk["text"]))
    summary = ["chunk %d [%s]: %s" % (c["index"], c["heading"] or "untitled", c["text"][:200]) for c in chunks[:4]]
    prompt = build_extraction_prompt(entities, summary)
    raw, model_name, call_errors = router.complete_json(EXTRACTION_SYSTEM, prompt)
    extracted_by = _extracted_by(model_name)
    response = validate_response(raw, model_name)
    errors = list(call_errors) + list(response["errors"])
    scored = corroborate(response["claims"], deterministic if deterministic is not None else [])

    graph = Graph()
    graph.bind("ctx", CTX)
    index = _label_index(deterministic)
    first_line = next((line.strip()[:120] for line in text.splitlines() if line.strip()), doc_id)
    document = CTX["Document/" + _slug(doc_id)]
    graph.add((document, RDF.type, CTX.Document))
    graph.add((document, RDFS.label, Literal(first_line)))
    _stamp(graph, document, "DIRECT", 1.0, extracted_by, generated_at, source)

    skipped = []
    for claim in scored:
        pred = claim["predicate"]
        if pred in POLICY_PREDICATES:
            node = CTX["Policy/" + _slug(doc_id) + "/" + _slug(claim["object"][:80])]
            graph.add((node, RDF.type, CTX.Policy))
            graph.add((node, RDFS.label, Literal(claim["object"])))
            service = index.get(claim["object"].strip().lower())
            if pred in ("policy", "hasPolicy") and service is not None:
                graph.add((node, CTX.constrains, service))
            _stamp(graph, node, claim["supportType"], claim["confidence"], extracted_by, generated_at, source)
        elif pred in RULE_PREDICATES:
            node = CTX["BusinessRule/" + _slug(doc_id) + "/" + _slug(claim["object"][:80])]
            graph.add((node, RDF.type, CTX.BusinessRule))
            graph.add((node, RDFS.label, Literal(claim["object"])))
            _stamp(graph, node, claim["supportType"], claim["confidence"], extracted_by, generated_at, source)
        elif pred == "mentionsEntity":
            entity = index.get(claim["object"].strip().lower())
            if entity is not None:
                # Edge only (claim keeps its support/confidence in scored);
                # re-stamping Document would fork its single confidence value.
                graph.add((document, CTX.mentionsEntity, entity))
            else:
                skipped.append(claim)
        else:
            skipped.append(claim)
    return {"graph": graph, "scored": scored, "skipped": skipped, "errors": errors,
            "extracted_by": extracted_by, "chunks": len(chunks), "entities": len(entities)}


def process_corpus(paths: list, router, doc_ids: list | None = None, deterministic=None, generated_at: str = "") -> dict:
    """Run process_document over many files; merge graphs deterministically."""
    merged = Graph()
    merged.bind("ctx", CTX)
    results, skipped, errors = [], [], []
    paths = [Path(p) for p in paths]
    ids = list(doc_ids) if doc_ids else [p.stem for p in paths]
    for doc_id, path in sorted(zip(ids, paths), key=lambda t: t[0]):
        result = process_document(doc_id, path, router, deterministic, generated_at)
        results.append({"doc_id": doc_id, "scored": result["scored"], "skipped": result["skipped"],
                        "errors": result["errors"], "chunks": result["chunks"]})
        for triple in result["graph"]:
            merged.add(triple)
        skipped.extend(result["skipped"])
        errors.extend(result["errors"])
    return {"graph": merged, "results": results, "skipped": skipped, "errors": errors}
