"""Datamodel-dependency scope tests on real OFBiz sources.

Order-only behavior is preserved (flag off); --include-dependencies adds the
datamodel entity model with per-file attribution and resolves in-scope targets.
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.graph import build as build_graph  # noqa: E402
from contextgraph.pipeline import run as run_extract  # noqa: E402
from contextgraph.scanner import COMPONENT_DEPENDENCIES, discover  # noqa: E402

rdflib = pytest.importorskip("rdflib")

NB = "http://example.org/ofbiz/0.1/"
DM_FILE = "applications/datamodel/entitydef/order-entitymodel.xml"


def _parse_repo_file(relpath, role, artifact_type):
    from contextgraph.parsers import PARSERS
    from contextgraph.provenance import ParseContext, artifact_for, parse_xml

    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    path = repo / relpath
    artifact = artifact_for(repo, path, artifact_type)
    tree = parse_xml(path)
    ctx = ParseContext(repo_root=repo, repo_id="apache-ofbiz-24.09.07", artifact=artifact, tree=tree)
    ctx.component_name = "datamodel"
    return PARSERS[role](path, ctx)


def _by_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]


def test_dependency_map_is_explicit_and_scoped():
    assert COMPONENT_DEPENDENCIES["order"]["files"] == [(DM_FILE, "entity")]
    assert COMPONENT_DEPENDENCIES["order"]["component_xml"] == "applications/datamodel/ofbiz-component.xml"


def test_scanner_default_unchanged():
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    found = discover(repo / "applications" / "order")
    assert all(owner == "order" for role in found for _p, owner in found[role])
    assert not any("datamodel" in p.as_posix() for role in found for p, _o in found[role])


def test_scanner_dependencies_attributed():
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    found = discover(repo / "applications" / "order", repo, include_dependencies=True)
    dm_entity = [(p, o) for p, o in found["entity"] if "datamodel" in p.as_posix()]
    assert len(dm_entity) == 1 and dm_entity[0][1] == "datamodel"
    dm_comp = [(p, o) for p, o in found["component"] if "datamodel" in p.as_posix()]
    assert len(dm_comp) == 1 and dm_comp[0][1] == "datamodel"


def test_base_entities_parse():
    facts, _cands = _parse_repo_file(DM_FILE, "entity", "entity-model")
    entities = {f["props"]["name"]: f for f in _by_kind(facts, "entity")}
    assert len(entities) == 112
    for name in ("OrderHeader", "OrderItem", "OrderPaymentPreference"):
        assert name in entities
        assert entities[name]["prov"]["file"] == DM_FILE
        assert entities[name]["prov"]["extraction_type"] == "direct"
    oh = entities["OrderHeader"]
    fields = {f["props"]["name"]: f for f in _by_kind(facts, "entity_field") if f["props"]["entity"] == "OrderHeader"}
    assert fields["orderId"]["props"]["is_primary_key"] is True
    assert fields["orderId"]["props"]["type"] == "id"
    assert fields["grandTotal"]["props"]["type"] == "currency-amount"
    rels = [f for f in _by_kind(facts, "relation") if f["props"]["subject"] == "OrderHeader"]
    assert len(rels) == 12
    by_target = {r["props"]["rel_entity_name"]: r["props"] for r in rels}
    assert by_target["OrderType"]["type"] == "one"
    assert by_target["OrderType"]["fk_name"] == "ORDER_HDR_TYPE"


def test_relations_carry_key_maps_and_lines():
    facts, _cands = _parse_repo_file(DM_FILE, "entity", "entity-model")
    rels = [f for f in _by_kind(facts, "relation") if f["props"]["subject"] == "OrderHeader" and f["props"]["rel_entity_name"] == "OrderType"]
    assert rels and rels[0]["props"]["key_maps"] == [{"field_name": "orderTypeId", "rel_field_name": ""}]
    assert rels[0]["prov"]["line"] and rels[0]["prov"]["line"] > 0


@pytest.fixture(scope="module")
def deps_run(tmp_path_factory):
    work = tmp_path_factory.mktemp("deps")
    fx = work / "fx"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    run_extract(repo, "order", fx, include_dependencies=True)
    ttl = work / "g.ttl"
    build_graph(fx / "order-facts.jsonl", fx / "order-manifest.json", ttl, as_of="2026-01-01T00:00:00+00:00")
    g = rdflib.Graph()
    g.parse(str(ttl), format="turtle")
    unresolved = json.loads((fx / "order-unresolved.json").read_text(encoding="utf-8"))
    manifest = json.loads((fx / "order-manifest.json").read_text(encoding="utf-8"))
    return g, unresolved, manifest, fx


def _has(g, s, p, o):
    OFB = rdflib.Namespace(NB)
    return (rdflib.URIRef(s), getattr(OFB, p), rdflib.URIRef(o) if o.startswith("http") else rdflib.Literal(o)) in g


def test_order_header_resolved_with_datamodel_evidence(deps_run):
    g, _u, _m, _fx = deps_run
    OFB = rdflib.Namespace(NB)
    oh = rdflib.URIRef(NB + "entity/OrderHeader")
    assert (oh, rdflib.RDF.type, OFB.Entity) in g
    assert (oh, OFB.definedIn, rdflib.URIRef(NB + "source/" + DM_FILE)) in g
    assert (oh, OFB.belongsToComponent, rdflib.URIRef(NB + "component/datamodel")) in g
    assert _has(g, NB + "service/createOrderAdjustmentAttribute", "operatesOn", NB + "entity/OrderAdjustmentAttribute")


def test_eca_path_connected(deps_run):
    g, _u, _m, _fx = deps_run
    OFB = rdflib.Namespace(NB)
    ecas = list(g.subjects(OFB.triggerEntityName, rdflib.Literal("OrderHeader")))
    assert ecas
    assert any((e, OFB.triggeredOnEntity, rdflib.URIRef(NB + "entity/OrderHeader")) in g for e in ecas)
    assert any((e, OFB.appliesTo, rdflib.URIRef(NB + "entity/OrderHeader")) in g for e in ecas)
    # The action target lives outside both scopes: reported, never minted.
    assert (rdflib.URIRef(NB + "service/issueImmediatelyFulfilledOrder"), rdflib.RDF.type, OFB.Service) not in g


def test_no_entity_from_mention(deps_run):
    g, unresolved, _m, _fx = deps_run
    OFB = rdflib.Namespace(NB)
    assert (rdflib.URIRef(NB + "entity/AccommodationSpot"), rdflib.RDF.type, OFB.Entity) not in g
    assert any(u.get("to_name") == "AccommodationSpot" for u in unresolved)


def test_auto_expansion_evidence(deps_run):
    g, _u, _m, fx = deps_run
    facts = [json.loads(x) for x in (fx / "order-facts.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    auto = [f for f in facts if f["kind"] == "auto_attributes" and f["props"].get("entity_ref") == "OrderHeader"]
    assert auto, "expected an OrderHeader auto-attributes directive in source"
    expanded = [f for f in facts if f["kind"] == "service_param" and f["prov"].get("method") == "auto-attributes-expansion"]
    assert expanded
    sample = expanded[0]
    assert sample["prov"]["extraction_type"] == "inferred"
    assert len(sample["prov"]["evidence"]) == 2
    assert any("datamodel" in e["file"] for e in sample["prov"]["evidence"])


def test_datamodel_component_node(deps_run):
    g, _u, manifest, _fx = deps_run
    OFB = rdflib.Namespace(NB)
    dm = rdflib.URIRef(NB + "component/datamodel")
    assert (dm, rdflib.RDF.type, OFB.Component) in g
    assert manifest["scope"]["include_dependencies"] is True
    assert DM_FILE in manifest["scope"]["dependency_files"]


def test_order_only_unchanged(tmp_path):
    fx = tmp_path / "fx"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    manifest = run_extract(repo, "order", fx)
    assert manifest["scope"]["include_dependencies"] is False
    facts = [json.loads(x) for x in (fx / "order-facts.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    # Order-only scope locks: 4555 legacy facts + 139 view <relation> elements
    # (previously dropped, now extracted) + 5 resolved relationTo edges.
    assert len(facts) == 4699
    assert not [f for f in facts if f["kind"] == "entity"]
    assert manifest["counts"].get("service") == 468
    assert manifest["counts"].get("relation") == 139
    assert manifest["counts"].get("view_entity") == 53
