"""SEC EDGAR filing processor (PART2_PLAN Task 2.7, proposal §7.2 2.4).

 filing text -> Item sections (deterministic split) -> Item 1A risk
paragraphs -> LLM extraction (systems, processes, risks, controls) ->
module links ("order management system" -> Order, "accounts receivable" ->
Accounting) -> contract triples (Filing, Section, RiskFactor,
mentionsProcess, referencesModule).

edgartools is imported ONLY inside fetch_filing(); unit tests use fixture
text and never need it installed. Deterministic section/risk splits are
stamped extractedBy "edgar-parser"; LLM-derived nodes use the model label.
"""

from __future__ import annotations

import re
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
GRAPH = "urn:edgar"
PARSER = "edgar-parser"

_ITEM = re.compile(r"^ITEM\s+(1A|1|7|8)\b[.\)]?\s*(.*)$", re.IGNORECASE)


def _slug(text: str) -> str:
    return quote(str(text), safe="-_.")


def fetch_filing(cik: str, form: str = "10-K", limit: int = 1):
    """Live EDGAR fetch via edgartools (integration only, never unit tests)."""
    try:
        from edgar import Company
    except ImportError as exc:
        raise RuntimeError("edgartools is required for live EDGAR fetch") from exc
    company = Company(cik)
    filings = company.get_filings(form=form)
    return [filings[i] for i in range(min(limit, len(filings)))]


def split_sections(text: str) -> list:
    """Split filing text at ITEM headings -> [{item, heading, text}]."""
    sections, item, heading, buf = [], "", "", []
    for line in text.splitlines(keepends=True):
        match = _ITEM.match(line.strip())
        if match:
            sections.append((item, heading, "".join(buf)))
            item, heading, buf = match.group(1).upper(), line.strip(), []
        else:
            buf.append(line)
    sections.append((item, heading, "".join(buf)))
    return [{"item": i or "preamble", "heading": h, "text": b}
            for i, h, b in sections if h or b.strip()]


def risk_paragraphs(item1a_text: str) -> list:
    """Item 1A body -> risk-factor paragraphs (blank-line separated)."""
    return [p.strip() for p in re.split(r"\n\s*\n", item1a_text) if p.strip()]


def _stamp(graph: Graph, subject: URIRef, support: str, confidence: float,
           extracted_by: str, generated_at: str, source: str) -> None:
    graph.add((subject, CTX.supportType, Literal(support)))
    graph.add((subject, CTX.confidence, Literal(float(confidence))))
    graph.add((subject, CTX.factType, Literal("probabilistic")))
    graph.add((subject, CTX.extractedBy, Literal(extracted_by)))
    graph.add((subject, PROV.wasGeneratedBy, URIRef(str(CTX) + "EdgarExtractor")))
    graph.add((subject, PROV.hadPrimarySource, URIRef(source)))
    if generated_at:
        graph.add((subject, PROV.generatedAtTime, Literal(generated_at, datatype=XSD.dateTime)))


def _label_index(deterministic) -> dict:
    index = {}
    if deterministic is None:
        return index

    def rank(subj):
        types = set(deterministic.objects(subj, RDF.type))
        if CTX.Service in types:
            return 0
        if CTX.Entity in types:
            return 1
        return 2

    for subj in sorted(set(deterministic.subjects(RDF.type, None)), key=lambda s: (rank(s), str(s))):
        for label in deterministic.objects(subj, RDFS.label):
            index.setdefault(str(label).strip().lower(), subj)
    return index


def extract_filing(filing_id: str, text, router, deterministic=None, generated_at: str = "") -> dict:
    """Extract one filing (text or path) to contract triples. Router mockable."""
    if isinstance(text, Path) or (isinstance(text, str) and "\n" not in text and Path(text).is_file()):
        text = Path(text).read_text(encoding="utf-8")
    source = "file:///edgar/%s" % filing_id
    sections = split_sections(text)
    entities = ner.extract_entities(text[:4000])
    summary = ["section [%s %s]: %s" % (s["item"], s["heading"][:60], s["text"][:200]) for s in sections]
    prompt = build_extraction_prompt(entities, summary)
    raw, model_name, call_errors = router.complete_json(EXTRACTION_SYSTEM, prompt)
    extracted_by = _extracted_by(model_name)
    response = validate_response(raw, model_name)
    errors = list(call_errors) + list(response["errors"])
    scored = corroborate(response["claims"], deterministic if deterministic is not None else [])

    graph = Graph()
    graph.bind("ctx", CTX)
    index = _label_index(deterministic)
    filing = CTX["Filing/" + _slug(filing_id)]
    graph.add((filing, RDF.type, CTX.Filing))
    graph.add((filing, RDFS.label, Literal(filing_id)))
    _stamp(graph, filing, "DIRECT", 1.0, PARSER, generated_at, source)

    section_nodes = {}
    for section in sections:
        excerpt = " ".join(section["text"].split())[:100]
        label = section["heading"] + (" — " + excerpt if excerpt else "")
        node = CTX["Section/" + _slug(filing_id) + "/" + _slug(section["item"].strip() or "preamble")]
        graph.add((node, RDF.type, CTX.Section))
        graph.add((node, RDFS.label, Literal(label)))
        _stamp(graph, node, "DIRECT", 1.0, PARSER, generated_at, source)
        section_nodes[section["item"].strip().lower()] = node
        heading_key = (section["heading"] or "").strip().lower().rstrip(".")
        section_nodes[heading_key] = node
        tail = heading_key.split(".", 1)[-1].strip() if "." in heading_key else ""
        if tail:
            section_nodes[tail] = node
        if section["item"] == "1A":
            for i, para in enumerate(risk_paragraphs(section["text"])):
                risk = CTX["RiskFactor/" + _slug(filing_id) + "/" + str(i)]
                graph.add((risk, RDF.type, CTX.RiskFactor))
                graph.add((risk, RDFS.label, Literal(para[:200])))
                _stamp(graph, risk, "DIRECT", 1.0, PARSER, generated_at, source)

    skipped = []
    for claim in scored:
        if claim["predicate"] == "referencesModule":
            module = CTX["Module/" + _slug(claim["object"])]
            graph.add((module, RDF.type, CTX.Module))
            graph.add((module, RDFS.label, Literal(claim["object"])))
            graph.add((filing, CTX.referencesModule, module))
            _stamp(graph, module, claim["supportType"], claim["confidence"], extracted_by, generated_at, source)
        elif claim["predicate"] == "mentionsProcess":
            holder = section_nodes.get(claim["subject"].strip().lower().rstrip("."), filing)
            service = index.get(claim["object"].strip().lower())
            if service is not None:
                graph.add((holder, CTX.mentionsProcess, service))
            else:
                skipped.append(claim)
        else:
            skipped.append(claim)
    return {"graph": graph, "scored": scored, "skipped": skipped, "errors": errors,
            "extracted_by": extracted_by, "sections": len(sections)}
