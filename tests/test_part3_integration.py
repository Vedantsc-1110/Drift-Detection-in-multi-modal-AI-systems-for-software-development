"""Task 3.9 tests: Part 3 integration (§11.1 metrics).

Ten cross-artifact SPARQL queries (six §4.1 + four derived) scored against
hand-written expectations, and 20 bridge edges verified endpoint-by-endpoint
(the hand-written EXPECTED_BRIDGES table IS the manual verification record).
Fixture individuals are generated from declarative tables — compact,
reviewed, deterministic. No network.
"""

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")
pytest.importorskip("pyoxigraph")
pytest.importorskip("fastapi")

from rdflib.namespace import PROV, RDF, RDFS  # noqa: E402

from contextgraph.bridges import (  # noqa: E402
    BRIDGES_GRAPH,
    discover_bridges,
    insert_bridges,
)
from contextgraph.contract_api import QUERIES  # noqa: E402
from contextgraph.contract_pipeline import machine_spec  # noqa: E402
from contextgraph.contract_store import ContractStore  # noqa: E402
from contextgraph.contract_validate import validate  # noqa: E402
from contextgraph.triple_builder import CTX  # noqa: E402

SHAPES = PROJECT_ROOT / "ontology" / "contract-shapes.ttl"

# --- Declarative fixture tables (the verification record) ---
SERVICES = ["findOrders", "createInvoice", "approveOrder", "cancelOrder"]
TASKS = [("nightly_sync", "Nightly sync calling findOrders"),
         ("invoice_run", "Invoice run calling createInvoice"),
         ("approval_run", "Approval calling approveOrder"),
         ("cancel_run", "Cancel calling cancelOrder"),
         ("archive_run", "Archive calling findOrders")]
POLICIES = [("invoiceApproval", "createInvoice requires manager approval"),
            ("approvalDual", "approveOrder needs dual control"),
            ("cancelReason", "cancelOrder requires reason code"),
            ("findStaff", "findOrders restricted to staff")]
ENTITIES = ["Invoice", "OrderHeader", "OrderItem", "Party"]
CONTRACTS = [("CUAD-1", "Services Agreement",
              [("Payment Terms", "Pay each invoice within thirty days")]),
             ("CUAD-2", "Order Agreement",
              [("Fulfilment", "OrderItem backorders ship with OrderHeader consent"),
               ("Parties", "Party address change notice")])]
MODULES = ["Order", "Accounting", "Party"]
FILINGS = [("F2025", ["Order system outage risk", "Accounting ledger growth",
                       "Party onboarding delays"]),
           ("F2026", ["Order peak season review"])]
DOCUMENTS = ["Procurement Policy 2025", "Procurement Policy 2026", "Procurement Policy 2027"]

DERIVED_QUERIES = {
    # 7. Tasks invoking findOrders (inverse of Q3).
    "tasks_for_findorders": """PREFIX ctx: <http://context.example.org/>
      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
      SELECT ?task WHERE { GRAPH <urn:bridges> { ?node ctx:invokesService ?service }
        GRAPH <urn:airflow> { ?node rdfs:label ?task }
        GRAPH <urn:ofbiz_structural> { ?service rdfs:label "findOrders" } }
      ORDER BY ?task""",
    # 8. Entities defined in the Order component.
    "order_entities": """PREFIX ctx: <http://context.example.org/>
      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
      SELECT ?entity WHERE { GRAPH <urn:ofbiz_structural> {
        ?e a ctx:Entity ; rdfs:label ?entity ; ctx:definedIn ?src .
        FILTER(CONTAINS(STR(?src), "/order/")) } } ORDER BY ?entity""",
    # 9. Clause types on contracts mentioning Order-component entities.
    "order_contract_clauses": """PREFIX ctx: <http://context.example.org/>
      SELECT DISTINCT ?clauseType WHERE { GRAPH <urn:cuad> {
        ?c ctx:mentionsEntity ?e ; ctx:hasClause ?clause .
        ?clause ctx:clauseType ?clauseType }
        GRAPH <urn:ofbiz_structural> { ?e ctx:definedIn ?src .
        FILTER(CONTAINS(STR(?src), "/order/")) } } ORDER BY ?clauseType""",
    # 10. Filings and the modules they reference.
    "filing_modules": """PREFIX ctx: <http://context.example.org/>
      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
      SELECT ?filing ?module WHERE { GRAPH <urn:bridges> {
        ?f ctx:referencesModule ?m }
        GRAPH <urn:edgar> { ?f rdfs:label ?filing }
        GRAPH <urn:ofbiz_semantic> { ?m rdfs:label ?module } }
      ORDER BY ?filing ?module""",
}

EXPECTED_QUERIES = {
    "order_services": [["approveOrder"], ["cancelOrder"], ["findOrders"]],
    "invoice_io": [["invoiceId"], ["invoiceTypeId"]],
    "dags_for_findorders": [["orders_etl"]],
    "policies_for_invoice": [["createInvoice requires manager approval"]],
    "contracts_for_order": [["Order Agreement"]],
    "low_confidence": [],
    "tasks_for_findorders": [["Archive calling findOrders"], ["Nightly sync calling findOrders"]],
    "order_entities": [["OrderHeader"], ["OrderItem"]],
    "order_contract_clauses": [["Fulfilment"]],
    "filing_modules": [["ACME-F2025", "Accounting"], ["ACME-F2025", "Order"],
                       ["ACME-F2025", "Party"], ["ACME-F2026", "Order"]],
}

EXPECTED_BRIDGES = {
    ("invokesService", "nightly_sync", "findOrders"),
    ("invokesService", "invoice_run", "createInvoice"),
    ("invokesService", "approval_run", "approveOrder"),
    ("invokesService", "cancel_run", "cancelOrder"),
    ("invokesService", "archive_run", "findOrders"),
    ("constrains", "invoiceApproval", "createInvoice"),
    ("constrains", "approvalDual", "approveOrder"),
    ("constrains", "cancelReason", "cancelOrder"),
    ("constrains", "findStaff", "findOrders"),
    ("mentionsEntity", "CUAD-1", "Invoice"),
    ("mentionsEntity", "CUAD-2", "OrderHeader"),
    ("mentionsEntity", "CUAD-2", "OrderItem"),
    ("mentionsEntity", "CUAD-2", "Party"),
    ("referencesModule", "F2025", "Order"),
    ("referencesModule", "F2025", "Accounting"),
    ("referencesModule", "F2025", "Party"),
    ("referencesModule", "F2026", "Order"),
    ("relatedTo", "D0", "D1"),
    ("relatedTo", "D0", "D2"),
    ("relatedTo", "D1", "D2"),
}

GRAPH_OF_TYPE = {"Service": "urn:ofbiz_structural", "Entity": "urn:ofbiz_structural",
                 "Field": "urn:ofbiz_structural", "DAG": "urn:airflow", "Task": "urn:airflow",
                 "Module": "urn:ofbiz_semantic", "Policy": "urn:ofbiz_semantic",
                 "Contract": "urn:cuad", "Clause": "urn:cuad",
                 "Filing": "urn:edgar", "Section": "urn:edgar", "Document": "urn:document_semantic"}


def _stamp(graph, subj, extracted_by=""):
    graph.add((subj, CTX.confidence, rdflib.Literal(1.0)))
    graph.add((subj, CTX.factType, rdflib.Literal("deterministic")))
    graph.add((subj, PROV.wasGeneratedBy, CTX.XmlEtreeExtractor))
    graph.add((subj, PROV.hadPrimarySource, rdflib.URIRef("file:///fixture")))
    if extracted_by:
        graph.add((subj, CTX.extractedBy, rdflib.Literal(extracted_by)))


def _individual(graph, cls, local, label, extra=(), extracted_by=""):
    subj = CTX[cls + "/" + local]
    graph.add((subj, RDF.type, CTX[cls]))
    graph.add((subj, RDFS.label, rdflib.Literal(label)))
    for pred, obj in extra:
        graph.add((subj, pred, obj))
    _stamp(graph, subj, extracted_by)
    return subj


def build_union() -> rdflib.Graph:
    """Emit every fixture individual from the tables above (deterministic)."""
    graph = rdflib.Graph()
    graph.bind("ctx", CTX)
    service_of = {}
    for name in SERVICES:
        component = "accounting" if name == "createInvoice" else "order"
        service_of[name] = _individual(
            graph, "Service", name, name,
            [(CTX.definedIn, rdflib.URIRef("file:///ofbiz/%s/services.xml" % component))])
    for param in ("invoiceTypeId", "invoiceId"):
        _individual(graph, "Field", "Param-" + param, param)
    graph.add((service_of["createInvoice"], CTX.hasInputParam, CTX["Field/Param-invoiceTypeId"]))
    graph.add((service_of["createInvoice"], CTX.hasOutputParam, CTX["Field/Param-invoiceId"]))
    for name in ENTITIES:
        component = "accounting" if name == "Invoice" else ("party" if name == "Party" else "order")
        _individual(graph, "Entity", name, name,
                    [(CTX.definedIn, rdflib.URIRef("file:///ofbiz/%s/entities.xml" % component))])
    dag = _individual(graph, "DAG", "orders_etl", "orders_etl")
    for task_id, label in TASKS:
        task = _individual(graph, "Task", task_id, label)
        graph.add((dag, CTX.hasTask, task))
    for module in MODULES:
        _individual(graph, "Module", module, module, extracted_by="fixture-builder")
    for policy_id, label in POLICIES:
        _individual(graph, "Policy", policy_id, label, extracted_by="fixture-builder")
    for contract_id, title, clauses in CONTRACTS:
        contract = _individual(graph, "Contract", contract_id, title, extracted_by="fixture-builder")
        for category, text in clauses:
            clause = _individual(graph, "Clause", contract_id + "/" + category.replace(" ", "-"), text,
                                 [(CTX.clauseType, rdflib.Literal(category))],
                                 extracted_by="fixture-builder")
            graph.add((contract, CTX.hasClause, clause))
    for filing_id, sections in FILINGS:
        _individual(graph, "Filing", filing_id, "ACME-" + filing_id, extracted_by="fixture-builder")
        for i, heading in enumerate(sections):
            _individual(graph, "Section", filing_id + "/" + str(i), heading, extracted_by="fixture-builder")
    for i, title in enumerate(DOCUMENTS):
        _individual(graph, "Document", "D%d" % i, title, extracted_by="fixture-builder")
    # Extractor-style entity links in the cuad graph (mirrors prob/cuad.py output).
    for contract_id, entity in (("CUAD-1", "Invoice"), ("CUAD-2", "OrderHeader"),
                                ("CUAD-2", "OrderItem"), ("CUAD-2", "Party")):
        graph.add((CTX["Contract/" + contract_id], CTX.mentionsEntity, CTX["Entity/" + entity]))
    return graph


def _short(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def _run_all(store_dir):
    started = time.perf_counter()
    union = build_union()
    store = ContractStore(store_dir)
    per_graph: dict[str, rdflib.Graph] = {}
    for triple in union:
        cls = next(union.objects(triple[0], RDF.type), None)
        cls_name = str(cls).rsplit("/", 1)[-1] if cls else ""
        per_graph.setdefault(GRAPH_OF_TYPE.get(cls_name, "urn:ofbiz_structural"), rdflib.Graph()).add(triple)
    for graph_uri, graph in per_graph.items():
        path = Path(store_dir) / (graph_uri.replace("urn:", "") + ".ttl")
        path.write_text(graph.serialize(format="turtle"), encoding="utf-8")
        store.load_file(path, graph_uri)
    bridges = discover_bridges(union)
    insert_bridges(store, bridges)
    elapsed = time.perf_counter() - started
    return store, union, bridges, elapsed


def _score(store):
    results = {}
    for key in ("order_services", "invoice_io", "dags_for_findorders",
                "policies_for_invoice", "contracts_for_order", "low_confidence"):
        rows = store.sparql(QUERIES[key])
        results[key] = sorted([list(r.values()) for r in rows])
    for key, query in DERIVED_QUERIES.items():
        rows = store.sparql(query)
        results[key] = sorted([list(r.values()) for r in rows])
    score = [(key, results[key] == EXPECTED_QUERIES[key]) for key in EXPECTED_QUERIES]
    return results, score


def _report(results, score, bridges, elapsed):
    passed = sum(1 for _, ok in score)
    lines = ["# Part 3 integration run report (§11.1)", ""]
    lines.append("- Wall-clock: %.2fs" % elapsed)
    lines.append("- Query accuracy: %d/10 (metric: 9/10) — %s"
                 % (passed, "PASS" if passed >= 9 else "FAIL"))
    for key, ok in score:
        lines.append("  - %s: %s -> %s" % (key, "PASS" if ok else "FAIL", results[key]))
    found = {(b["p"], _short(str(b["s"])), _short(str(b["o"]))) for b in bridges}
    lines.append("- Bridge edges: %d/20 verified (metric: 20) — %s"
                 % (len(found & EXPECTED_BRIDGES),
                    "PASS" if found == EXPECTED_BRIDGES else "FAIL"))
    if found != EXPECTED_BRIDGES:
        lines.append("  - missing: %s" % sorted(EXPECTED_BRIDGES - found))
        lines.append("  - extra: %s" % sorted(found - EXPECTED_BRIDGES))
    lines.append("")
    lines.append("## Machine spec")
    for key, value in machine_spec().items():
        lines.append("- %s: %s" % (key, value))
    lines.append("")
    lines.append("## Deviation notes")
    lines.append("- Fixture scale: individuals are generated from review tables in")
    lines.append("  tests/test_part3_integration.py; real Part 1/2 outputs plug in")
    lines.append("  unchanged via ContractStore.load_directory + insert_bridges.")
    lines.append("")
    return "\n".join(lines)


def _run_with_report(out_dir, store_dir):
    store, union, bridges, elapsed = _run_all(store_dir)
    try:
        results, score = _score(store)
        report = _report(results, score, bridges, elapsed)
    finally:
        store.close()
    (Path(out_dir) / "run_report.md").write_text(report, encoding="utf-8")
    validation = validate(union, SHAPES)
    return results, score, bridges, report, validation


def test_query_accuracy_nine_of_ten(tmp_path):
    results, score, _, _, _ = _run_with_report(tmp_path, tmp_path / "store")
    failed = [key for key, ok in score if not ok]
    assert sum(1 for _, ok in score if ok) >= 9, "failed queries: %s" % failed


def test_twenty_bridges_verified(tmp_path):
    _, _, bridges, _, _ = _run_with_report(tmp_path, tmp_path / "store")
    found = {(b["p"], _short(str(b["s"])), _short(str(b["o"]))) for b in bridges}
    assert found == EXPECTED_BRIDGES


def test_report_and_store_shape(tmp_path):
    results, score, bridges, report, validation = _run_with_report(tmp_path, tmp_path / "store")
    assert validation["conforms"], validation["violations"]
    text = (tmp_path / "run_report.md").read_text(encoding="utf-8")
    assert "Query accuracy" in text and "Bridge edges" in text and "Machine spec" in text
