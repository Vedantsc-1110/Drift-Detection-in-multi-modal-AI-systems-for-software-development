"""Task 1.3a tests: ECA extractor (PART1_PLAN Task 1.3).

Standalone on tests/fixtures/ofbiz (synthetic). Each <eca> yields one
fact with trigger/action/conditions/service calls + source location.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.parsers import eca as eca_parser  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for, parse_xml  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ofbiz"


def _parse(relpath):
    path = FIXTURES / relpath
    assert path.is_file(), "missing fixture %s" % relpath
    artifact = artifact_for(FIXTURES, path, "eca-mixed")
    tree = parse_xml(path)
    ctx = ParseContext(repo_root=FIXTURES, repo_id="fixture-ofbiz-24.09", artifact=artifact, tree=tree)
    ctx.component_name = relpath.split("/")[1]
    return eca_parser.parse(path, ctx), artifact


def _by_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]


def test_entity_eca_trigger_action_conditions():
    (facts, candidates), _ = _parse("applications/order/testdef/eecas.xml")
    ecas = _by_kind(facts, "eca")
    assert len(ecas) == 2
    by_trigger = {e["props"]["trigger_entity"]: e for e in ecas}
    assert set(by_trigger) == {"OrderHeader", "OrderItem"}
    assert by_trigger["OrderHeader"]["props"]["operation"] == "create-store"
    conds = {(c["props"]["field"], c["props"]["operator"], c["props"]["value"]) for c in _by_kind(facts, "condition")}
    assert ("statusId", "equals", "ORDER_COMPLETED") in conds
    assert ("needsInventoryIssuance", "equals", "Y") in conds
    actions = _by_kind(facts, "eca_action")
    assert any(a["props"]["service"] == "issueImmediatelyFulfilledOrder" and a["props"]["mode"] == "sync" for a in actions)
    assert any(c["edge"] == "triggersService" and c["to_name"] == "issueImmediatelyFulfilledOrder" for c in candidates)
    assert any(c["edge"] == "triggeredOnEntity" and c["to_name"] == "OrderHeader" for c in candidates)


def test_service_eca_trigger_and_multiple_actions():
    (facts, candidates), _ = _parse("applications/order/servicedef/secas.xml")
    ecas = _by_kind(facts, "eca")
    assert len(ecas) == 2
    by_trigger = {e["props"]["trigger_service"]: e for e in ecas}
    assert set(by_trigger) == {"changeOrderItemStatus", "storeOrder"}
    assert by_trigger["changeOrderItemStatus"]["props"]["eca_class"] == "ServiceECA"
    targets = {c["to_name"] for c in candidates if c["edge"] == "triggersService"}
    assert {"cancelOrderItemInventory", "notifyCustomerOnCancel", "createOrderContent"} <= targets


def test_eca_provenance_on_every_fact():
    for rel in (
        "applications/order/testdef/eecas.xml",
        "applications/order/servicedef/secas.xml",
        "applications/accounting/testdef/eecas.xml",
        "applications/party/testdef/eecas.xml",
    ):
        (facts, _), artifact = _parse(rel)
        assert len(artifact.sha256) == 64
        for fact in facts:
            prov = fact["prov"]
            assert prov["file"] == artifact.relpath, fact["id"]
            assert prov["line"] and prov["line"] > 0, fact["id"]
            assert prov["xpath"], fact["id"]
