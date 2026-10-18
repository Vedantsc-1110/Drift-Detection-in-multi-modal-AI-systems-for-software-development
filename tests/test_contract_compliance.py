"""Task 1.10 tests: CONTRACT.md compliance gate (PART1_PLAN Task 1.10, PR #2 gate).

Adaptation note: no CONTRACT.md exists in this repo; the contract surface is
triple_builder.py (namespace ctx:, four extractor names, §6 file names).
To keep this a real gate rather than a tautology, the allowed class and
property lists below are hand-written and reviewed — the builder must stay
within them; extending the builder requires consciously updating this file.

Asserts per outputs file (ofbiz_structural.ttl, airflow.ttl, cicd.ttl):
- file names match §6; plain Turtle with NO GRAPH blocks;
- every ctx: subject carries confidence 1.0, factType "deterministic",
  wasGeneratedBy (one of the four), hadPrimarySource, sourceLocation,
  sourceHash (64-hex);
- only allow-listed ctx: classes/properties appear; prov:atTime never does.
"""

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.contract_pipeline import run  # noqa: E402
from contextgraph.triple_builder import CTX  # noqa: E402

FIXTURES = PROJECT_ROOT / "tests" / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"
EXPECTED_FILES = ("ofbiz_structural.ttl", "airflow.ttl", "cicd.ttl")

PROV = "http://www.w3.org/ns/prov#"
EXTRACTORS = {str(CTX.XmlEtreeExtractor), str(CTX.TreeSitterExtractor), str(CTX.PythonAstExtractor), str(CTX.YamlExtractor)}

ALLOW_CLASSES = {
    "Service", "ServiceParam", "Entity", "ViewEntity", "Field", "Relation",
    "ECA", "Condition", "ECAAction", "Route", "ModuleDependency",
    "JavaClass", "JavaMethod", "Import", "Call",
    "DAG", "Task", "Workflow", "Job", "Step",
}

ALLOW_PROPS = {
    "definedIn", "atLine", "sourceLocation", "sourceHash", "confidence", "factType",
    "engine", "implementedBy", "paramType", "mode", "fieldType", "isPrimaryKey",
    "relationType", "relatesTo", "keyMap", "triggerEntity", "triggerService",
    "operation", "event", "condField", "condOperator", "condValue",
    "callsService", "uri", "eventType", "eventInvoke", "dependsOnModule",
    "configuration", "returnType", "hasParam", "calls", "receiver", "imports",
    "scheduledAt", "operatorType", "inDAG", "usesAction", "runCommand", "usesSecret",
    "hasInputParam", "hasOutputParam", "dependsOn", "triggeredBy", "hasStep",
    "referencesService", "triggersService", "triggeredOnEntity",
    "triggeredOnService", "operatesOn", "relationTo",
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")


@pytest.fixture(scope="module")
def contract_outputs(tmp_path_factory):
    out = tmp_path_factory.mktemp("contract")
    manifest = run(FIXTURES, out, GENERATED_AT)
    assert manifest["errors"] == []
    graphs = {}
    for name in EXPECTED_FILES:
        g = rdflib.Graph()
        g.parse(str(out / name), format="turtle")
        graphs[name] = g
    return out, graphs


def _ctx_subjects(graph):
    return {s for s in graph.subjects(rdflib.RDF.type, None) if str(s).startswith(str(CTX))}


def test_file_names_match_section_6(contract_outputs):
    out, _ = contract_outputs
    assert sorted(p.name for p in out.glob("*.ttl")) == sorted(EXPECTED_FILES)


def test_no_graph_blocks(contract_outputs):
    out, _ = contract_outputs
    for name in EXPECTED_FILES:
        assert "GRAPH" not in (out / name).read_text(encoding="utf-8"), name


def test_subject_metadata_matches_section_5(contract_outputs):
    _, graphs = contract_outputs
    for name, graph in graphs.items():
        subjects = _ctx_subjects(graph)
        assert subjects, name
        for subj in subjects:
            assert (subj, CTX.confidence, rdflib.Literal(1.0)) in graph, (name, subj)
            assert (subj, CTX.factType, rdflib.Literal("deterministic")) in graph, (name, subj)
            gen = set(graph.objects(subj, rdflib.URIRef(PROV + "wasGeneratedBy")))
            assert len(gen) == 1 and str(next(iter(gen))) in EXTRACTORS, (name, subj)
            src = list(graph.objects(subj, rdflib.URIRef(PROV + "hadPrimarySource")))
            assert len(src) == 1 and str(src[0]).startswith("file:///"), (name, subj)
            loc = list(graph.objects(subj, CTX.sourceLocation))
            assert len(loc) == 1 and ":" in str(loc[0]), (name, subj)
            digest = list(graph.objects(subj, CTX.sourceHash))
            assert len(digest) == 1 and HEX64.match(str(digest[0])), (name, subj)


def test_only_documented_classes_and_properties(contract_outputs):
    _, graphs = contract_outputs
    seen_classes, seen_props = set(), set()
    for name, graph in graphs.items():
        for subj in _ctx_subjects(graph):
            for rdf_class in graph.objects(subj, rdflib.RDF.type):
                if str(rdf_class).startswith(str(CTX)):
                    seen_classes.add(str(rdf_class)[len(str(CTX)):])
        for _, pred, _ in graph:
            if str(pred).startswith(str(CTX)):
                seen_props.add(str(pred)[len(str(CTX)):])
    assert seen_classes - ALLOW_CLASSES == set(), "undocumented classes: %s" % (seen_classes - ALLOW_CLASSES)
    assert seen_props - ALLOW_PROPS == set(), "undocumented properties: %s" % (seen_props - ALLOW_PROPS)
    assert {"Service", "DAG", "Workflow"} <= seen_classes


def test_prov_attime_never_emitted(contract_outputs):
    _, graphs = contract_outputs
    for name, graph in graphs.items():
        assert len(list(graph.subject_objects(rdflib.URIRef(PROV + "atTime")))) == 0, name
