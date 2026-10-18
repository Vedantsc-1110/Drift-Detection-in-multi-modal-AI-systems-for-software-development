"""Task 1.3b tests: controller.xml routes (PART1_PLAN Task 1.3)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.parsers.gradle_controller import parse_controller  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for, parse_xml  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ofbiz"


def _parse(relpath):
    path = FIXTURES / relpath
    assert path.is_file(), "missing fixture %s" % relpath
    artifact = artifact_for(FIXTURES, path, "controller")
    tree = parse_xml(path)
    ctx = ParseContext(repo_root=FIXTURES, repo_id="fixture-ofbiz-24.09", artifact=artifact, tree=tree)
    ctx.component_name = relpath.split("/")[1]
    return parse_controller(path, ctx), artifact


def test_order_routes_with_event_mapping():
    (facts, candidates), _ = _parse("applications/order/webapp/ordermgr/WEB-INF/controller.xml")
    routes = {f["props"]["uri"]: f for f in facts if f["kind"] == "route"}
    assert set(routes) == {"searchorders", "orderview"}
    search = routes["searchorders"]
    assert search["props"]["event_type"] == "service"
    assert search["props"]["event_invoke"] == "findOrders"
    assert any(r["value"] == "findorders" for r in search["props"]["responses"])
    assert any(c["to_name"] == "findOrders" and c["via"] == "controller-event" for c in candidates)
    # Non-service event type is recorded but not a service candidate.
    assert routes["orderview"]["props"]["event_type"] == "java"
    assert not [c for c in candidates if c["to_name"] == "org.apache.ofbiz.order.web.OrderEvents.orderView"]


def test_other_modules_routes():
    for rel, uri, invoke in (
        ("applications/accounting/webapp/accounting/WEB-INF/controller.xml", "findinvoices", "findInvoices"),
        ("applications/party/webapp/partymgr/WEB-INF/controller.xml", "viewprofile", "getPartyProfile"),
    ):
        (facts, candidates), _ = _parse(rel)
        routes = {f["props"]["uri"]: f for f in facts if f["kind"] == "route"}
        assert routes[uri]["props"]["event_invoke"] == invoke
        assert any(c["to_name"] == invoke for c in candidates)


def test_route_provenance():
    (facts, _), artifact = _parse("applications/order/webapp/ordermgr/WEB-INF/controller.xml")
    assert len(artifact.sha256) == 64
    for fact in facts:
        prov = fact["prov"]
        assert prov["file"] == artifact.relpath, fact["id"]
        assert prov["line"] and prov["line"] > 0, fact["id"]
        assert prov["xpath"], fact["id"]
