"""Contract SPARQL API (§4.1): FastAPI over a ContractStore (PART3 Task 3.6).

Six predefined GET endpoints and a local SPARQL query endpoint accompany the
graph explorer. Run ``python serve_contract_api.py --demo`` from the project
directory, or instantiate create_app(store) in tests with TestClient.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from pyoxigraph import Literal

DASHBOARD_PATH = Path(__file__).resolve().parent.parent.parent / "dashboard" / "index.html"

PREFIXES = """PREFIX ctx: <http://context.example.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX prov: <http://www.w3.org/ns/prov#>
"""

# Q2 reads input/output *parameters* as the read/write proxy: the contract
# vocabulary has no Service→Entity data-flow property, so parameter names
# are the answerable surface (documented limitation, not a silent gap).
QUERIES = {
    # 1. Services defined in the Order component (via source path).
    "order_services": PREFIXES + """SELECT ?service WHERE {
      GRAPH <urn:ofbiz_structural> {
        ?s a ctx:Service ; rdfs:label ?service ; ctx:definedIn ?src .
        FILTER(CONTAINS(STR(?src), "/order/")) } } ORDER BY ?service""",
    # 2. createInvoice input/output parameter names.
    "invoice_io": PREFIXES + """SELECT ?param WHERE {
      GRAPH <urn:ofbiz_structural> {
        ?service rdfs:label "createInvoice" .
        { ?service ctx:hasInputParam ?p } UNION { ?service ctx:hasOutputParam ?p }
        ?p rdfs:label ?param } } ORDER BY ?param""",
    # 3. DAGs with a task invoking findOrders.
    "dags_for_findorders": PREFIXES + """SELECT DISTINCT ?dag WHERE {
      GRAPH <urn:airflow> { ?d a ctx:DAG ; rdfs:label ?dag ; ctx:hasTask ?task }
      GRAPH <urn:bridges> { ?task ctx:invokesService ?service }
      GRAPH <urn:ofbiz_structural> { ?service rdfs:label "findOrders" } }""",
    # 4. Policies constraining createInvoice.
    "policies_for_invoice": PREFIXES + """SELECT ?policy WHERE {
      GRAPH <urn:bridges> { ?node ctx:constrains ?service }
      GRAPH <urn:ofbiz_semantic> { ?node rdfs:label ?policy }
      GRAPH <urn:ofbiz_structural> { ?service rdfs:label "createInvoice" } }""",
    # 5. Contracts mentioning entities defined in the Order component
    # (directly on the contract or through its clauses).
    "contracts_for_order": PREFIXES + """SELECT DISTINCT ?contract WHERE {
      GRAPH <urn:cuad> { ?c rdfs:label ?contract .
        { ?c ctx:mentionsEntity ?entity } UNION
        { ?c ctx:hasClause ?clause . ?clause ctx:mentionsEntity ?entity } }
      GRAPH <urn:ofbiz_structural> { ?entity ctx:definedIn ?src .
        FILTER(CONTAINS(STR(?src), "/order/")) } }""",
    # 6. Probabilistic facts with confidence below 0.7.
    "low_confidence": PREFIXES + """SELECT ?subject ?confidence WHERE {
      GRAPH ?g { ?subject ctx:confidence ?confidence ;
        ctx:factType "probabilistic" ; rdfs:label ?label .
        FILTER(?confidence < 0.7) } } ORDER BY ?subject""",
}


class SparqlBody(BaseModel):
    query: str


# --- §4.2 dashboard data layer (the dashboard's query surface) ---

CONFIDENCE_BANDS = {"high": 0.85, "medium": 0.60, "all": 0.0}
EDGE_PROPS = ("invokesService", "constrains", "mentionsEntity",
              "referencesModule", "relatedTo", "dependsOn", "hasTask",
              "hasStep", "hasInputParam", "hasOutputParam", "belongsToConcept",
              "calls", "implementedBy", "hasField", "relatesTo", "hasClause",
              "hasParameter", "imports", "mentionsProcess")


def _iri(value: str) -> str:
    """Validate an absolute RDF IRI before embedding it in SPARQL."""
    # Reject SPARQL delimiters and controls at the input boundary.
    if (not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:.+", value)
            or re.search(r'[<>"{}|^`\\\x00-\x20]', value)):
        raise HTTPException(status_code=400, detail="invalid graph or node URI")
    return "<" + value + ">"


def _nodes_query(fact_type: str, min_confidence: float, graph: str, search: str) -> str:
    filters = ["?s a ?class ; rdfs:label ?label ; ctx:confidence ?confidence ; ctx:factType ?ft ."]
    if fact_type in ("deterministic", "probabilistic"):
        filters.append('FILTER(?ft = "%s")' % fact_type)
    filters.append("FILTER(?confidence >= %s)" % float(min_confidence))
    if search:
        # Use RDF literal serialization, never interpolate raw search text.
        filters.append('FILTER(CONTAINS(LCASE(?label), LCASE(%s)))' % Literal(search))
    inner = "\n        ".join(filters)
    if graph:
        if not graph.startswith("urn:"):
            raise HTTPException(status_code=400, detail="invalid graph")
        return PREFIXES + "SELECT ?s ?label ?class ?confidence ?ft WHERE { GRAPH %s { %s } } ORDER BY ?s ?class" % (_iri(graph), inner)
    return PREFIXES + "SELECT ?s ?label ?class ?confidence ?ft ?g WHERE { GRAPH ?g { %s } } ORDER BY ?s" % inner


def _edges_query(node_uris: list[str], graph: str = "") -> str:
    values = " ".join(_iri(uri) for uri in node_uris)
    members = ", ".join("ctx:%s" % p for p in EDGE_PROPS)
    scope = _iri(graph) if graph else "?g"
    return PREFIXES + "SELECT DISTINCT ?from ?p ?to ?g WHERE { GRAPH %s { ?from ?p ?to . FILTER(?p IN (%s)) } VALUES ?from { %s } } ORDER BY ?from ?p ?to ?g" % (scope, members, values)


def _check_name(service: str) -> None:
    if '"' in service or "\\" in service or "\n" in service:
        raise HTTPException(status_code=400, detail="invalid service name")


def create_app(store, *, data_info: dict | None = None) -> FastAPI:
    """Build the §4.1 API bound to a ContractStore."""
    app = FastAPI(title="Enterprise Context API (Part 3)")

    @app.get("/", include_in_schema=False)
    def home():
        return RedirectResponse("/dashboard")

    @app.get("/graph/summary")
    def graph_summary():
        rows = store.sparql("SELECT ?g (COUNT(*) AS ?count) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g ORDER BY ?g")
        return {"mode": (data_info or {}).get("mode", "local"),
                "source": (data_info or {}).get("source", "Connected local graph store"),
                "liveMonitoring": False,
                "graphs": [{"id": row["g"], "triples": int(row["count"])} for row in rows]}

    @app.post("/sparql")
    def sparql(body: SparqlBody):
        return JSONResponse({"rows": store.sparql(body.query)})

    @app.get("/services/order")
    def order_services():
        return JSONResponse({"rows": store.sparql(QUERIES["order_services"])})

    @app.get("/services/createInvoice/io")
    def invoice_io():
        return JSONResponse({"rows": store.sparql(QUERIES["invoice_io"])})

    @app.get("/dags/for-service")
    def dags_for_service(service: str = "findOrders"):
        _check_name(service)
        query = QUERIES["dags_for_findorders"].replace('"findOrders"', '"%s"' % service)
        return JSONResponse({"rows": store.sparql(query)})

    @app.get("/policies/for-service")
    def policies_for_service(service: str = "createInvoice"):
        _check_name(service)
        query = QUERIES["policies_for_invoice"].replace('"createInvoice"', '"%s"' % service)
        return JSONResponse({"rows": store.sparql(query)})

    @app.get("/contracts/for-module")
    def contracts_for_module():
        return JSONResponse({"rows": store.sparql(QUERIES["contracts_for_order"])})

    @app.get("/facts/low-confidence")
    def low_confidence(threshold: float = 0.7):
        query = QUERIES["low_confidence"].replace("< 0.7", "< %s" % float(threshold))
        return JSONResponse({"rows": store.sparql(query)})

    @app.get("/graph/nodes")
    def graph_nodes(confidence: str = "all", factType: str = "both",
                    graph: str = "", search: Annotated[str, Query(max_length=250)] = ""):
        """§4.2 node/edge payload honoring dashboard filters."""
        if confidence not in CONFIDENCE_BANDS:
            raise HTTPException(status_code=400, detail="invalid confidence band")
        if factType not in ("deterministic", "probabilistic", "both"):
            raise HTTPException(status_code=400, detail="invalid factType")
        rows = store.sparql(_nodes_query(factType, CONFIDENCE_BANDS[confidence], graph, search))
        node_ids = {r["s"] for r in rows}
        by_id = {}
        for row in rows:
            uri = row["s"]
            membership = row.get("g", graph)
            if uri not in by_id:
                by_id[uri] = {"id": uri, "label": row["label"], "class": row["class"],
                              "confidence": row["confidence"], "factType": row["ft"],
                              "graph": membership, "graphs": [], "classes": []}
            node = by_id[uri]
            if membership not in node["graphs"]:
                node["graphs"].append(membership)
            if row["class"] not in node["classes"]:
                node["classes"].append(row["class"])
        nodes = list(by_id.values())
        edges = []
        if node_ids:
            for row in store.sparql(_edges_query(sorted(node_ids), graph)):
                if row["to"] in node_ids:
                    edges.append({"from": row["from"], "to": row["to"],
                                  "label": row["p"].rsplit("/", 1)[-1].rsplit("#", 1)[-1],
                                  "graph": row.get("g") or graph})
        return JSONResponse({"nodes": nodes, "edges": edges})

    @app.get("/node")
    def node_provenance(uri: str, graph: str = ""):
        """§4.2 provenance panel payload for one node."""
        subject = _iri(uri)
        scope = _iri(graph) if graph else "?g"
        query = PREFIXES + """SELECT ?label ?class ?confidence ?ft ?extractedBy ?source ?line ?location ?generatedBy ?generatedAt ?g WHERE {
          GRAPH %s { %s rdfs:label ?label ; a ?class ; ctx:confidence ?confidence ; ctx:factType ?ft .
            OPTIONAL { %s ctx:extractedBy ?extractedBy }
            OPTIONAL { %s prov:hadPrimarySource ?source }
            OPTIONAL { %s ctx:atLine ?line }
            OPTIONAL { %s ctx:sourceLocation ?location }
            OPTIONAL { %s prov:wasGeneratedBy ?generatedBy }
            OPTIONAL { %s prov:generatedAtTime ?generatedAt }
          } } ORDER BY ?g ?class LIMIT 1""" % (scope, subject, subject, subject, subject, subject, subject, subject)
        rows = store.sparql(query)
        if not rows:
            raise HTTPException(status_code=404, detail="unknown node")
        return JSONResponse({"uri": uri, **rows[0], "graph": rows[0].get("g") or graph})

    @app.get("/dashboard", response_class=None)
    def dashboard():
        page = DASHBOARD_PATH.read_text(encoding="utf-8")
        return HTMLResponse(page)

    @app.get("/assets/{name}", include_in_schema=False)
    def dashboard_asset(name: str):
        # Serve only the authored assets, never arbitrary filesystem paths.
        if name not in {"dashboard.css", "dashboard.js"}:
            raise HTTPException(status_code=404, detail="unknown dashboard asset")
        media_type = "text/css" if name.endswith(".css") else "application/javascript"
        return FileResponse(DASHBOARD_PATH.parent / name, media_type=media_type)

    @app.get("/vendor/{name}")
    def vendor(name: str):
        from fastapi.responses import Response

        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise HTTPException(status_code=400, detail="invalid vendor file")
        path = DASHBOARD_PATH.parent / "vendor" / name
        if path.suffix != ".js" or not path.is_file():
            raise HTTPException(status_code=404, detail="unknown vendor file")
        return Response(path.read_bytes(), media_type="application/javascript")

    return app
