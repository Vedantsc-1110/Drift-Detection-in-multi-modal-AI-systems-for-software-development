"""Entity parser tests on the real order entitydef view file."""
from conftest import by_kind, parse_file

VIEWS = "applications/order/entitydef/entitymodel_view.xml"


def test_view_count(repo_root):
    facts, _, _ = parse_file(repo_root, VIEWS, "entity", "entity-model")
    assert len(by_kind(facts, "view_entity")) == 53
    assert by_kind(facts, "entity") == []


def test_order_header_and_items_structure(repo_root):
    facts, candidates, _ = parse_file(repo_root, VIEWS, "entity", "entity-model")
    views = {f["props"]["name"]: f for f in by_kind(facts, "view_entity")}
    assert "OrderHeaderAndItems" in views
    members = [f for f in by_kind(facts, "view_member") if f["props"]["view"] == "OrderHeaderAndItems"]
    assert {m["props"]["alias"]: m["props"]["entity_ref"] for m in members} == {"OH": "OrderHeader", "OI": "OrderItem"}
    aliases = [f for f in by_kind(facts, "view_alias") if f["props"]["view"] == "OrderHeaderAndItems"]
    assert "orderId" in {a["props"]["name"] for a in aliases}
    links = [f for f in by_kind(facts, "view_link") if f["props"]["view"] == "OrderHeaderAndItems"]
    assert len(links) == 1
    assert links[0]["props"]["key_maps"] == [{"field_name": "orderId", "rel_field_name": ""}]


def test_member_refs_are_candidates_not_edges(repo_root):
    facts, candidates, _ = parse_file(repo_root, VIEWS, "entity", "entity-model")
    assert not [f for f in facts if f["kind"] == "edge"]
    mem_refs = [c for c in candidates if c["via"] == "member-entity"]
    assert any(c["to_name"] == "OrderHeader" for c in mem_refs)
