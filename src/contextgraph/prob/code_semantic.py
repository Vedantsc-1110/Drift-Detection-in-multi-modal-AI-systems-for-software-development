"""Code semantic extractor (PART2_PLAN Task 2.4, proposal §7.2 2.1).

Module summary (class/method/service/entity names from Stage-1) -> LLM
(Task 2.1 router) -> JSON validation -> corroboration (Task 2.3) -> contract
triples in the <urn:ofbiz_semantic> family: ctx:businessPurpose,
ctx:BusinessConcept + ctx:belongsToConcept, ctx:BusinessRule, and
inter-module dependencies.

One-confidence-per-subject: each claim mints or reuses a dedicated subject
carrying its own confidence/extractedBy; unmapped predicates land in the
returned ``skipped`` list, never silently dropped.
"""

from __future__ import annotations

from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS, XSD

from .corroboration import corroborate
from .groq_client import EXTRACTED_BY as GROQ_EXTRACTED_BY
from .json_validator import validate_response
from .prompts import EXTRACTION_SYSTEM, build_extraction_prompt

CTX = Namespace("http://context.example.org/")
GRAPH = "urn:ofbiz_semantic"

RULE_PREDICATES = {"businessRule", "hasRule"}
DEPENDENCY_PREDICATES = {"dependsOn", "calls", "referencesService"}


def _slug(text: str) -> str:
    return quote(str(text), safe="-_.")


def _extracted_by(model_name: str) -> str:
    if model_name.startswith("groq:"):
        return GROQ_EXTRACTED_BY
    if model_name.startswith("ollama:"):
        return "qwen3.5:4b"
    return model_name


def build_module_summary(graph: Graph, module: str) -> list:
    """Render Stage-1 summary lines (exactly the proposal's LLM input)."""
    lines = ["module: %s" % module]
    for rdf_class, tag in ((CTX.Service, "service"), (CTX.Entity, "entity"), (CTX.JavaMethod, "method")):
        names = set()
        for subj in graph.subjects(RDF.type, rdf_class):
            label = next(graph.objects(subj, RDFS.label), None)
            if label:
                names.add(str(label))
        lines.append("%ss: %s" % (tag, ", ".join(sorted(names)) if names else "(none)"))
    return lines


def _label_index(graph: Graph) -> dict:
    index = {}
    for subj in set(graph.subjects(RDF.type, None)):
        for label in graph.objects(subj, RDFS.label):
            index.setdefault(str(label).strip().lower(), subj)
    return index


def _stamp(graph: Graph, subject: URIRef, scored: dict, extracted_by: str, generated_at: str, source: str) -> None:
    graph.add((subject, CTX.confidence, Literal(float(scored["confidence"]))))
    graph.add((subject, CTX.factType, Literal("probabilistic")))
    graph.add((subject, CTX.extractedBy, Literal(extracted_by)))
    graph.add((subject, PROV.wasGeneratedBy, URIRef("http://context.example.org/" + ("GroqLLMExtractor" if extracted_by == GROQ_EXTRACTED_BY else "OllamaLLMExtractor"))))
    graph.add((subject, PROV.hadPrimarySource, URIRef(source)))
    if generated_at:
        graph.add((subject, PROV.generatedAtTime, Literal(generated_at, datatype=XSD.dateTime)))


def extract_module_semantics(module: str, stage1: Graph, router, generated_at: str = "", source: str = "") -> dict:
    """Full Task 2.4 flow; router is a Task-2.1 Router (mockable). Returns dict."""
    summary = build_module_summary(stage1, module)
    prompt = build_extraction_prompt([], summary)
    text, model_name, call_errors = router.complete_json(EXTRACTION_SYSTEM, prompt)
    extracted_by = _extracted_by(model_name)
    response = validate_response(text, model_name)
    errors = list(call_errors) + list(response["errors"])
    scored = corroborate(response["claims"], stage1)

    graph = Graph()
    graph.bind("ctx", CTX)
    index = _label_index(stage1)
    module_subj = CTX["Module/" + _slug(module)]
    graph.add((module_subj, RDF.type, CTX.Module))
    graph.add((module_subj, RDFS.label, Literal(module)))
    skipped = []
    purpose_set = False
    for claim in scored:
        pred = claim["predicate"]
        if pred == "businessPurpose" and not purpose_set:
            graph.add((module_subj, CTX.businessPurpose, Literal(claim["object"])))
            _stamp(graph, module_subj, claim, extracted_by, generated_at, source or "stage1:%s" % module)
            purpose_set = True
        elif pred == "belongsToConcept":
            concept = CTX["BusinessConcept/" + _slug(claim["object"])]
            graph.add((concept, RDF.type, CTX.BusinessConcept))
            graph.add((concept, RDFS.label, Literal(claim["object"])))
            service = index.get(claim["subject"].strip().lower())
            if service is not None:
                graph.add((service, CTX.belongsToConcept, concept))
            _stamp(graph, concept, claim, extracted_by, generated_at, source or "stage1:%s" % module)
        elif pred in RULE_PREDICATES:
            rule = CTX["BusinessRule/" + _slug(claim["subject"]) + "/" + _slug(claim["object"])[:60]]
            graph.add((rule, RDF.type, CTX.BusinessRule))
            graph.add((rule, RDFS.label, Literal(claim["object"])))
            _stamp(graph, rule, claim, extracted_by, generated_at, source or "stage1:%s" % module)
        elif pred in DEPENDENCY_PREDICATES:
            dep = CTX["Module/" + _slug(claim["object"])]
            graph.add((dep, RDF.type, CTX.Module))
            graph.add((dep, RDFS.label, Literal(claim["object"])))
            graph.add((module_subj, CTX.dependsOn, dep))
            _stamp(graph, dep, claim, extracted_by, generated_at, source or "stage1:%s" % module)
        else:
            skipped.append(claim)
    return {"graph": graph, "scored": scored, "skipped": skipped, "errors": errors,
            "extracted_by": extracted_by, "summary": summary}
