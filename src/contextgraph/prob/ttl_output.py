"""Probabilistic triple builder + Turtle output (PART2_PLAN Task 2.8, §8 rdflib).

Merges the Task 2.4–2.7 extractor graphs into the four CONTRACT §6 files
(ofbiz_semantic, document_semantic, cuad, edgar — plain Turtle, no GRAPH
blocks) and validates every graph: confidence in 0.0–1.0, factType,
extractedBy, generatedAtTime, hadPrimarySource on each Part-2-minted
subject, and ctx: classes/properties within the CONTRACT §2–§3 lists.

Borrowed deterministic subjects (e.g. a Stage-1 Service carrying a
belongsToConcept edge) are exempt from probabilistic metadata — their
provenance lives in the Stage-1 file.
"""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF

CTX = Namespace("http://context.example.org/")
PROV = "http://www.w3.org/ns/prov#"

OUTPUT_FILES = ("ofbiz_semantic.ttl", "document_semantic.ttl", "cuad.ttl", "edgar.ttl")

CONTRACT_CLASSES = {
    "Module", "Service", "Entity", "Field", "JavaClass", "JavaMethod", "ECA",
    "DAG", "Task", "Workflow", "Job", "Step",
    "Document", "BusinessConcept", "Policy", "BusinessRule",
    "Contract", "Clause", "Party", "Filing", "Section", "RiskFactor",
}

CONTRACT_PROPS = {
    "calls", "implementedBy", "hasField", "relatesTo", "invokesService",
    "constrains", "mentionsEntity", "hasClause", "belongsToConcept",
    "referencesModule", "mentionsProcess",
    "engine", "hasInputParam", "hasOutputParam", "hasParameter", "hasTask",
    "dependsOn", "scheduledAt", "operatorType", "triggeredBy", "hasStep",
    "usesAction", "clauseType", "imports", "definedIn", "atLine",
    "sourceLocation", "sourceHash", "businessPurpose",
    "confidence", "factType", "extractedBy", "supportType",
}


def merge_graphs(graphs: list) -> Graph:
    """Deterministic union (sorted triple order has nooplevel effect on sets)."""
    merged = Graph()
    merged.bind("ctx", CTX)
    for graph in graphs:
        for triple in graph:
            merged.add(triple)
    return merged


def write_outputs(graphs: dict, out_dir, generated_note: str = "") -> dict:
    """Serialize {filename: Graph} as plain Turtle. Returns {name: info}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, graph in sorted(graphs.items()):
        path = out_dir / name
        path.write_text(graph.serialize(format="turtle"), encoding="utf-8")
        result[name] = {"path": str(path), "triples": len(graph)}
    return result


def validate_prob_graph(graph: Graph, deterministic: Graph | None = None) -> list:
    """Return error strings; empty means contract-clean."""
    errors = []
    borrowed = set(deterministic.subjects(RDF.type, None)) if deterministic is not None else set()
    for subj in set(graph.subjects(RDF.type, None)):
        if not str(subj).startswith(str(CTX)) or subj in borrowed:
            continue
        for rdf_class in graph.objects(subj, RDF.type):
            name = str(rdf_class)[len(str(CTX)):] if str(rdf_class).startswith(str(CTX)) else None
            if name is not None and name not in CONTRACT_CLASSES:
                errors.append("undocumented class %s on %s" % (rdf_class, subj))
        conf = list(graph.objects(subj, CTX.confidence))
        if len(conf) != 1:
            errors.append("confidence count != 1 on %s" % subj)
        elif not (isinstance(conf[0], Literal) and 0.0 <= float(conf[0]) <= 1.0):
            errors.append("confidence out of range on %s" % subj)
        if (subj, CTX.factType, Literal("probabilistic")) not in graph:
            errors.append("factType != probabilistic on %s" % subj)
        if next(graph.objects(subj, CTX.extractedBy), None) is None:
            errors.append("missing extractedBy on %s" % subj)
        if next(graph.objects(subj, Namespace(PROV).generatedAtTime), None) is None:
            errors.append("missing prov:generatedAtTime on %s" % subj)
        if next(graph.objects(subj, Namespace(PROV).hadPrimarySource), None) is None:
            errors.append("missing prov:hadPrimarySource on %s" % subj)
    for _, pred, _ in graph:
        if str(pred).startswith(str(CTX)):
            name = str(pred)[len(str(CTX)):]
            if name not in CONTRACT_PROPS:
                errors.append("undocumented property %s" % pred)
    return sorted(set(errors))
