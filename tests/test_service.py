"""Service parser tests on real order servicedef files."""
from conftest import by_kind, parse_file

SVC_ORDER = "applications/order/servicedef/services_order.xml"
SVC_MAIN = "applications/order/servicedef/services.xml"


def test_service_count_matches_source(repo_root):
    facts, _, _ = parse_file(repo_root, SVC_ORDER, "service", "service-def")
    assert len(by_kind(facts, "service")) == 61


def test_entity_auto_service_binding(repo_root):
    facts, _, _ = parse_file(repo_root, SVC_ORDER, "service", "service-def")
    svc = {f["props"]["name"]: f for f in by_kind(facts, "service")}
    s = svc["createOrderAdjustmentAttribute"]
    assert s["props"]["engine"] == "entity-auto"
    assert s["props"]["invoke"] == "create"
    assert s["props"]["auth"] == "true"


def test_auth_and_validate_recorded(repo_root):
    facts, _, _ = parse_file(repo_root, SVC_MAIN, "service", "service-def")
    svc = {f["props"]["name"]: f for f in by_kind(facts, "service")}
    assert svc["storeOrder"]["props"]["auth"] == "true"
    assert svc["storeOrder"]["props"]["validate"] == "true"
    assert svc["getOrderHeaderInformation"]["props"]["validate"] == "false"


def test_explicit_params_have_modes(repo_root):
    facts, _, _ = parse_file(repo_root, SVC_MAIN, "service", "service-def")
    params = by_kind(facts, "service_param")
    assert len(params) > 100
    for p in params:
        assert p["prov"]["extraction_type"] == "direct"
        assert p["prov"]["line"] and p["prov"]["line"] > 0
        assert p["props"]["role"] == "service-parameter"


def test_interface_inheritance_candidate(repo_root):
    facts, candidates, _ = parse_file(repo_root, SVC_MAIN, "service", "service-def")
    impls = [c for c in candidates if c["via"] == "implements"]
    assert impls, "expected <implements> references"
    assert any(c["to_name"] == "orderNotificationInterface" for c in impls)


def test_group_invokes_are_candidates(repo_root):
    facts, candidates, _ = parse_file(repo_root, SVC_MAIN, "service", "service-def")
    group_refs = [c for c in candidates if c["via"] == "group-invoke"]
    assert any(c["to_name"] == "cancelRemainingPurchaseOrderItems" for c in group_refs)


def test_no_invented_edges_at_parse_time(repo_root):
    facts, _, _ = parse_file(repo_root, SVC_MAIN, "service", "service-def")
    assert not [f for f in facts if f["kind"] == "edge" and f["prov"]["extraction_type"] == "inferred"]
