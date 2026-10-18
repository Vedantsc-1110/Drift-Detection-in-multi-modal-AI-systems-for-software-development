"""Task 1.4 tests: tree-sitter Java/Groovy AST extractor (PART1_PLAN Task 1.4).

Standalone on tests/fixtures/java + groovy (synthetic). Every class and
method appears; every call edge appears as a java_call fact; line numbers
match tests/fixtures/expected_ast_facts.json (hand-verified).
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.parsers import java_ast  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
EXPECTED = json.loads((FIXTURES / "expected_ast_facts.json").read_text(encoding="utf-8"))
SOURCES = {"java": FIXTURES / "java" / "OrderServices.java", "groovy": FIXTURES / "groovy" / "OrderHelper.groovy"}


def _parse(key):
    path = SOURCES[key]
    assert path.is_file(), "missing fixture %s" % path
    artifact = artifact_for(PROJECT_ROOT, path, "java-source")
    assert len(artifact.sha256) == 64
    ctx = ParseContext(repo_root=PROJECT_ROOT, repo_id="fixture-ofbiz-24.09", artifact=artifact, tree=None)
    ctx.component_name = "order"
    return java_ast.parse(path, ctx)


def _by_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]


def _check(key):
    (facts, _), exp = _parse(key), EXPECTED[key]
    by_class = {f["props"]["name"]: f for f in _by_kind(facts, "java_class")}
    for spec in exp["classes"]:
        assert spec["name"] in by_class, (key, spec["name"])
        assert by_class[spec["name"]]["prov"]["line"] == spec["line"], (key, spec["name"])
    by_method = {(f["props"]["class"], f["props"]["name"]): f for f in _by_kind(facts, "java_method")}
    for spec in exp["methods"]:
        f = by_method.get((spec["class"], spec["name"]))
        assert f is not None, (key, spec["name"])
        assert f["props"]["params"] == spec["params"], (key, spec["name"])
        assert f["props"]["return_type"] == spec["return_type"], (key, spec["name"])
        assert f["prov"]["line"] == spec["line"], (key, spec["name"])
    calls = {(f["props"]["caller_method"], f["props"]["callee"]): f for f in _by_kind(facts, "java_call")}
    for spec in exp["calls"]:
        f = calls.get((spec["caller_method"], spec["callee"]))
        assert f is not None, (key, spec)
        assert f["props"]["receiver"] == spec["receiver"], (key, spec)
        assert f["prov"]["line"] == spec["line"], (key, spec)
    imports = {(f["props"]["import"], f["prov"]["line"]) for f in _by_kind(facts, "java_import")}
    for spec in exp["imports"]:
        assert (spec["import"], spec["line"]) in imports, (key, spec)
    for fact in facts:
        assert fact["prov"]["file"], fact["id"]
        assert fact["prov"]["line"] and fact["prov"]["line"] > 0, fact["id"]
        assert fact["prov"]["extraction_type"] == "direct", fact["id"]


def test_java_fixture_fully_covered():
    _check("java")


def test_groovy_fixture_fully_covered():
    _check("groovy")


def test_cross_component_call_present():
    facts, _ = _parse("java")
    assert any(
        f["props"]["caller_method"] == "createOrder"
        and f["props"]["receiver"] == "PartyServices"
        and f["props"]["callee"] == "getParty"
        for f in _by_kind(facts, "java_call")
    ), "expected OrderServices -> PartyServices call edge"
