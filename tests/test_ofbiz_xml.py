"""Task 1.2 tests: OFBiz XML servicedef + entitydef (PART1_PLAN Task 1.2).

Standalone: uses tests/fixtures/ofbiz (synthetic, modeled on OFBiz 24.09),
no real dataset, no network. Exercises the real parsers
(contextgraph.parsers.service / .entity) so the plan's DONE criteria
(fixture extraction == hand-written expected fact list) guards the
production code path.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.parsers import entity as entity_parser  # noqa: E402
from contextgraph.parsers import service as service_parser  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for, parse_xml  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ofbiz"
REPO_ROOT = FIXTURES  # synthetic repo root; relpaths mirror real layout
EXPECTED = json.loads((FIXTURES / "expected_ofbiz_xml_facts.json").read_text(encoding="utf-8"))


def _parse(relpath, role):
    path = REPO_ROOT / relpath
    assert path.is_file(), "missing fixture %s" % relpath
    artifact_type = "service-def" if role == "service" else "entity-model"
    artifact = artifact_for(REPO_ROOT, path, artifact_type)
    assert len(artifact.sha256) == 64, "sha256 missing for %s" % relpath
    tree = parse_xml(path)
    ctx = ParseContext(repo_root=REPO_ROOT, repo_id="fixture-ofbiz-24.09", artifact=artifact, tree=tree)
    ctx.component_name = relpath.split("/")[1]
    parser = service_parser if role == "service" else entity_parser
    return parser.parse(path, ctx)


def _by_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]


def _assert_prov(facts):
    for fact in facts:
        prov = fact["prov"]
        assert prov["file"], fact["id"]
        assert prov["line"] and prov["line"] > 0, fact["id"]
        assert prov["xpath"], fact["id"]
        assert prov["extraction_type"] == "direct", fact["id"]


def test_every_service_yields_typed_facts():
    for spec in EXPECTED["services"]:
        facts, _ = _parse(spec["file"], "service")
        services = {f["props"]["name"]: f for f in _by_kind(facts, "service") if f["prov"]["file"] == spec["file"]}
        assert spec["name"] in services, "missing service %s" % spec["name"]
        svc = services[spec["name"]]
        for attr in ("engine", "location", "invoke"):
            assert svc["props"][attr] == spec[attr], (spec["name"], attr)
        assert "description" in svc["props"] and svc["props"]["description"]
        params = [f for f in _by_kind(facts, "service_param") if f["props"].get("service") in (None, spec["name"]) or spec["name"] in f["id"]]
        names = {p["props"]["name"] for p in params if spec["name"] in p["id"]}
        assert set(spec["inputs"]) | set(spec["outputs"]) <= names, (spec["name"], names)
        for p in params:
            if spec["name"] in p["id"]:
                assert p["props"]["type"], p["id"]
        _assert_prov(facts)


def test_input_output_edges_match_modes():
    for spec in EXPECTED["services"]:
        facts, _ = _parse(spec["file"], "service")
        edges = [f for f in _by_kind(facts, "edge") if spec["name"] in f["id"]]
        by_pred = {}
        for e in edges:
            to = e["props"]["to"]
            pname = to.rsplit("/param/", 1)[-1].split("/via/")[0].split("#")[0]
            by_pred.setdefault(e["props"]["predicate"], set()).add(pname)
        for name in spec["inputs"]:
            assert name in by_pred.get("hasInput", set()), (spec["name"], name)
        for name in spec["outputs"]:
            assert name in by_pred.get("hasOutput", set()), (spec["name"], name)


def test_every_entity_yields_fields_and_relations():
    for spec in EXPECTED["entities"]:
        facts, candidates = _parse(spec["file"], "entity")
        entities = {f["props"]["name"]: f for f in _by_kind(facts, "entity")}
        assert spec["name"] in entities, "missing entity %s" % spec["name"]
        fields = [f for f in _by_kind(facts, "entity_field") if f["props"]["entity"] == spec["name"]]
        assert {f["props"]["name"] for f in fields} == set(spec["fields"]), spec["name"]
        pks = {f["props"]["name"] for f in fields if f["props"]["is_primary_key"]}
        assert pks == set(spec["primary_keys"]), spec["name"]
        rels = [f for f in _by_kind(facts, "relation") if f["props"]["subject"] == spec["name"]]
        assert len(rels) == len(spec["relations"]), spec["name"]
        rels_sorted = sorted(rels, key=lambda f: f["props"]["rel_entity_name"])
        spec_sorted = sorted(spec["relations"], key=lambda r: r["target"])
        for rel_fact, rel_spec in zip(rels_sorted, spec_sorted):
            assert rel_fact["props"]["type"] == rel_spec["type"]
            assert rel_fact["props"]["rel_entity_name"] == rel_spec["target"]
            assert rel_fact["props"]["key_maps"] == rel_spec["key_maps"]
        targets = {c["to_name"] for c in candidates if c["via"] == "relation"}
        for rel_spec in spec["relations"]:
            assert rel_spec["target"] in targets, (spec["name"], rel_spec["target"])
        _assert_prov(facts)


def test_fixture_extraction_matches_expected_fact_list():
    all_services, all_entities = [], []
    seen_service_files, seen_entity_files = set(), set()
    for spec in EXPECTED["services"]:
        if spec["file"] not in seen_service_files:
            seen_service_files.add(spec["file"])
            facts, _ = _parse(spec["file"], "service")
            all_services.extend(_by_kind(facts, "service"))
    for spec in EXPECTED["entities"]:
        if spec["file"] not in seen_entity_files:
            seen_entity_files.add(spec["file"])
            facts, _ = _parse(spec["file"], "entity")
            all_entities.extend(_by_kind(facts, "entity"))
    assert {s["props"]["name"] for s in all_services} == {s["name"] for s in EXPECTED["services"]}
    assert {e["props"]["name"] for e in all_entities} == {e["name"] for e in EXPECTED["entities"]}
