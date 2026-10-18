"""ECA parser tests on real eecas.xml (entity) and secas.xml (service) files."""
from conftest import by_kind, parse_file

EECAS = "applications/order/entitydef/eecas.xml"
SECAS = "applications/order/servicedef/secas.xml"


def test_entity_eca_count_and_shape(repo_root):
    facts, candidates, _ = parse_file(repo_root, EECAS, "eca", "entity-eca")
    ecas = by_kind(facts, "eca")
    assert len(ecas) == 3
    first = sorted(ecas, key=lambda f: f["id"])[0]
    assert first["props"]["eca_class"] == "EntityECA"
    assert first["props"]["trigger_entity"] == "OrderHeader"
    assert first["props"]["operation"] == "create-store"
    assert first["props"]["event"] == "return"


def test_entity_eca_conditions_and_action(repo_root):
    facts, candidates, _ = parse_file(repo_root, EECAS, "eca", "entity-eca")
    conds = by_kind(facts, "condition")
    assert {(c["props"]["field"], c["props"]["operator"], c["props"]["value"]) for c in conds} >= {
        ("statusId", "equals", "ORDER_COMPLETED"),
        ("needsInventoryIssuance", "equals", "Y"),
    }
    actions = by_kind(facts, "eca_action")
    assert any(a["props"]["service"] == "issueImmediatelyFulfilledOrder" and a["props"]["mode"] == "sync" for a in actions)
    triggers = [c for c in candidates if c["edge"] == "triggersService"]
    assert any(c["to_name"] == "issueImmediatelyFulfilledOrder" for c in triggers)


def test_service_eca_count(repo_root):
    facts, candidates, _ = parse_file(repo_root, SECAS, "eca", "service-eca")
    assert len(by_kind(facts, "eca")) == 108
    klasses = {f["props"]["eca_class"] for f in by_kind(facts, "eca")}
    assert klasses == {"ServiceECA"}
    assert any(c["edge"] == "triggeredOnService" and c["to_name"] == "storeOrder" for c in candidates)
