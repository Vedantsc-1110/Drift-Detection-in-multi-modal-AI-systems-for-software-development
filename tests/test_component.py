"""Component parser tests on the real applications/order/ofbiz-component.xml."""
from conftest import by_kind, parse_file

COMP = "applications/order/ofbiz-component.xml"


def test_component_name_and_provenance(repo_root):
    facts, candidates, ctx = parse_file(repo_root, COMP, "component", "component-descriptor")
    assert candidates == []
    comp = by_kind(facts, "component")
    assert len(comp) == 1
    assert comp[0]["props"]["name"] == "order"
    assert comp[0]["props"]["location"] == "order"
    prov = comp[0]["prov"]
    assert prov["file"] == COMP
    assert prov["line"] and prov["line"] > 0
    assert prov["extraction_type"] == "direct"


def test_service_resources_cover_servicedef(repo_root):
    facts, _, _ = parse_file(repo_root, COMP, "component", "component-descriptor")
    locs = sorted(f["props"]["location"] for f in by_kind(facts, "resource") if f["props"]["kind"] == "service")
    assert "servicedef/services.xml" in locs
    assert "servicedef/services_order.xml" in locs
    assert len(locs) >= 10


def test_webapp_mount_point(repo_root):
    facts, _, _ = parse_file(repo_root, COMP, "component", "component-descriptor")
    webapps = {f["props"]["name"]: f["props"] for f in by_kind(facts, "webapp")}
    assert webapps["order"]["mount_point"] == "/ordermgr"
    assert "ORDERMGR" in webapps["order"]["base_permission"]
