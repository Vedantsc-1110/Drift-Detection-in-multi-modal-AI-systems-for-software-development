"""Task 1.7 tests: triple builder + Turtle serializer (PART1_PLAN Task 1.7).

Runs the real parsers over every fixture (Tasks 1.2–1.6), serializes to the
three CONTRACT §6 files, and asserts: each .ttl parses with rdflib;
re-parsed count equals in-memory count; every subject carries provenance;
the §7.2 1.1 example shape holds for createInvoice; no GRAPH blocks.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.parsers import airflow_dag, cicd_yaml, eca as eca_parser  # noqa: E402
from contextgraph.parsers import entity as entity_parser  # noqa: E402
from contextgraph.parsers import gradle_controller, java_ast  # noqa: E402
from contextgraph.parsers import service as service_parser  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for, parse_xml  # noqa: E402
from contextgraph.serializer import OUTPUT_FILES, serialize  # noqa: E402
from contextgraph.triple_builder import CTX, build_graph  # noqa: E402

FIX = PROJECT_ROOT / "tests" / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"

XML_JOBS = [
    ("ofbiz/applications/order/servicedef/services.xml", "service", "service-def", service_parser),
    ("ofbiz/applications/accounting/servicedef/services.xml", "service", "service-def", service_parser),
    ("ofbiz/applications/party/servicedef/services.xml", "service", "service-def", service_parser),
    ("ofbiz/applications/order/entitydef/order-entitymodel.xml", "entity", "entity-model", entity_parser),
    ("ofbiz/applications/accounting/entitydef/accounting-entitymodel.xml", "entity", "entity-model", entity_parser),
    ("ofbiz/applications/party/entitydef/party-entitymodel.xml", "entity", "entity-model", entity_parser),
    ("ofbiz/applications/order/testdef/eecas.xml", "eca", "eca-mixed", eca_parser),
    ("ofbiz/applications/order/servicedef/secas.xml", "eca", "eca-mixed", eca_parser),
    ("ofbiz/applications/accounting/testdef/eecas.xml", "eca", "eca-mixed", eca_parser),
    ("ofbiz/applications/party/testdef/eecas.xml", "eca", "eca-mixed", eca_parser),
    ("ofbiz/applications/order/webapp/ordermgr/WEB-INF/controller.xml", "controller", "controller", gradle_controller),
    ("ofbiz/applications/accounting/webapp/accounting/WEB-INF/controller.xml", "controller", "controller", gradle_controller),
    ("ofbiz/applications/party/webapp/partymgr/WEB-INF/controller.xml", "controller", "controller", gradle_controller),
]


def _parse_xml(rel, role, atype, module):
    path = FIX / rel
    artifact = artifact_for(PROJECT_ROOT, path, atype)
    tree = parse_xml(path)
    ctx = ParseContext(repo_root=PROJECT_ROOT, repo_id="fixture", artifact=artifact, tree=tree)
    ctx.component_name = rel.split("/")[2]
    parse = module.parse if hasattr(module, "parse") else module.parse_controller
    if role == "controller":
        return gradle_controller.parse_controller(path, ctx)
    return parse(path, ctx)


def _parse_text(rel, atype, module, component):
    path = FIX / rel
    artifact = artifact_for(PROJECT_ROOT, path, atype)
    ctx = ParseContext(repo_root=PROJECT_ROOT, repo_id="fixture", artifact=artifact, tree=None)
    ctx.component_name = component
    return module.parse(path, ctx)


def collect_facts():
    facts = []
    for rel, role, atype, module in XML_JOBS:
        f, _ = _parse_xml(rel, role, atype, module)
        facts.extend(f)
    for rel, comp in [
        ("ofbiz/applications/order/build.gradle", "order"),
        ("ofbiz/applications/accounting/build.gradle", "accounting"),
        ("ofbiz/applications/party/build.gradle", "party"),
    ]:
        f, _ = _parse_text(rel, "build-gradle", gradle_controller, comp)
        facts.extend(f)
    for rel in ["java/OrderServices.java", "groovy/OrderHelper.groovy"]:
        f, _ = _parse_text(rel, "java-source", java_ast, "order")
        facts.extend(f)
    for name in ["dag_orders_etl.py", "dag_inventory_sync.py"]:
        f, _ = _parse_text("airflow/" + name, "airflow-dag", airflow_dag, "airflow")
        facts.extend(f)
    for name in ["ci.yml", "release.yml"]:
        f, _ = _parse_text("cicd/.github/workflows/" + name, "cicd-workflow", cicd_yaml, "cicd")
        facts.extend(f)
    return facts


@pytest.fixture(scope="module")
def serialized(tmp_path_factory):
    facts = collect_facts()
    assert len(facts) > 100
    out = tmp_path_factory.mktemp("ttl")
    result = serialize(facts, PROJECT_ROOT, out, GENERATED_AT)
    graphs = {}
    for name in OUTPUT_FILES:
        g = rdflib.Graph()
        g.parse(str(out / name), format="turtle")
        graphs[name] = g
    return facts, result, graphs, out


def test_all_files_parse_and_counts_match(serialized):
    facts, result, graphs, out = serialized
    for name in OUTPUT_FILES:
        assert (out / name).is_file()
        assert result[name]["triples"] == len(graphs[name]), name
        assert result[name]["triples"] > 0, name


def test_every_subject_has_provenance(serialized):
    _, _, graphs, _ = serialized
    for name, graph in graphs.items():
        subjects = set(graph.subjects(rdflib.RDF.type, None))
        assert subjects, name
        for subj in subjects:
            if not str(subj).startswith(str(CTX)):
                continue
            assert (subj, CTX.confidence, rdflib.Literal(1.0)) in graph, (name, subj)
            assert (subj, CTX.factType, rdflib.Literal("deterministic")) in graph, (name, subj)
            assert next(graph.objects(subj, rdflib.URIRef("http://www.w3.org/ns/prov#wasGeneratedBy")), None) is not None, (name, subj)
            assert next(graph.objects(subj, rdflib.URIRef("http://www.w3.org/ns/prov#hadPrimarySource")), None) is not None, (name, subj)
            assert next(graph.objects(subj, CTX.sourceLocation), None) is not None, (name, subj)
            assert next(graph.objects(subj, CTX.sourceHash), None) is not None, (name, subj)


def test_create_invoice_matches_section_721_shape(serialized):
    _, _, graphs, _ = serialized
    graph = graphs["ofbiz_structural.ttl"]
    svc = CTX["Service/createInvoice"]
    assert (svc, rdflib.RDF.type, CTX.Service) in graph
    assert (svc, CTX.engine, rdflib.Literal("java")) in graph
    assert next(graph.objects(svc, CTX.implementedBy), None) is not None
    params = set(graph.objects(svc, CTX.hasInputParam)) | set(graph.objects(svc, CTX.hasOutputParam))
    assert params, "expected hasInputParam/hasOutputParam on createInvoice"
    assert any("invoiceTypeId" in str(p) for p in graph.objects(svc, CTX.hasInputParam))
    assert any("invoiceId" in str(p) for p in graph.objects(svc, CTX.hasOutputParam))
    assert next(graph.objects(svc, CTX.definedIn), None) is not None
    assert next(graph.objects(svc, CTX.atLine), None) is not None


def test_plain_turtle_no_graph_blocks_and_expected_extractors(serialized):
    _, _, graphs, out = serialized
    for name in OUTPUT_FILES:
        text = (out / name).read_text(encoding="utf-8")
        assert "GRAPH" not in text, name
    arrivals = set()
    for graph in graphs.values():
        arrivals.update(graph.objects(None, rdflib.URIRef("http://www.w3.org/ns/prov#wasGeneratedBy")))
    assert set(arrivals) <= {CTX.XmlEtreeExtractor, CTX.TreeSitterExtractor, CTX.PythonAstExtractor, CTX.YamlExtractor}
    assert CTX.XmlEtreeExtractor in arrivals and CTX.PythonAstExtractor in arrivals and CTX.YamlExtractor in arrivals


def test_outputs_routed_by_graph(serialized):
    _, _, graphs, _ = serialized
    assert (CTX["DAG/orders_etl"], rdflib.RDF.type, CTX.DAG) in graphs["airflow.ttl"]
    assert (CTX["Workflow/CI"], rdflib.RDF.type, CTX.Workflow) in graphs["cicd.ttl"]
    assert (CTX["Service/createOrder"], rdflib.RDF.type, CTX.Service) in graphs["ofbiz_structural.ttl"]
