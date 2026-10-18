"""Task 3.1 tests: contract OWL ontology (PART3_PLAN Task 3.1, §7.2 3.1).

Parses ontology/contract-ontology.ttl; every CONTRACT §2 class and §3
property is declared (hand-mirrored lists — a genuine gate); the eleven
§3.1 domain/range pairs match exactly.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from rdflib.namespace import OWL, RDF, RDFS

ONTOLOGY = PROJECT_ROOT / "ontology" / "contract-ontology.ttl"
CTX = "http://context.example.org/"

CLASSES = ["Module", "Service", "Entity", "Field", "JavaClass", "JavaMethod",
           "ECA", "DAG", "Task", "Workflow", "Job", "Step", "Document",
           "BusinessConcept", "Policy", "BusinessRule", "Contract", "Clause",
           "Party", "Filing", "Section", "RiskFactor"]

PROPERTIES = ["calls", "implementedBy", "hasField", "relatesTo",
              "invokesService", "constrains", "mentionsEntity", "hasClause",
              "belongsToConcept", "referencesModule", "mentionsProcess",
              "engine", "hasInputParam", "hasOutputParam", "hasParameter",
              "hasTask", "dependsOn", "scheduledAt", "operatorType",
              "triggeredBy", "hasStep", "usesAction", "clauseType", "imports",
              "definedIn", "atLine", "sourceLocation", "sourceHash",
              "businessPurpose", "confidence", "factType", "extractedBy",
              "supportType"]

DOMAINS_RANGES = {
    "calls": ("JavaMethod", "JavaMethod"),
    "implementedBy": ("Service", "JavaMethod"),
    "hasField": ("Entity", "Field"),
    "relatesTo": ("Entity", "Entity"),
    "invokesService": ("Task", "Service"),
    "constrains": ("Policy", "Service"),
    "mentionsEntity": ("Document", "Entity"),
    "hasClause": ("Contract", "Clause"),
    "belongsToConcept": ("Service", "BusinessConcept"),
    "referencesModule": ("Filing", "Module"),
    "mentionsProcess": ("Section", "Service"),
}


@pytest.fixture(scope="module")
def ontology():
    graph = rdflib.Graph()
    graph.parse(str(ONTOLOGY), format="turtle")
    return graph


def test_parses(ontology):
    assert len(ontology) > 50


def test_every_class_declared(ontology):
    for name in CLASSES:
        assert (rdflib.URIRef(CTX + name), RDF.type, OWL.Class) in ontology, name


def test_every_property_declared(ontology):
    for name in PROPERTIES:
        subj = rdflib.URIRef(CTX + name)
        assert (subj, RDF.type, OWL.ObjectProperty) in ontology or \
               (subj, RDF.type, OWL.DatatypeProperty) in ontology, name


def test_domains_ranges_match_section_31(ontology):
    for prop, (domain, range) in DOMAINS_RANGES.items():
        subj = rdflib.URIRef(CTX + prop)
        assert (subj, RDFS.domain, rdflib.URIRef(CTX + domain)) in ontology, prop
        assert (subj, RDFS.range, rdflib.URIRef(CTX + range)) in ontology, prop
