"""Task 1.3c tests: build.gradle module deps (PART1_PLAN Task 1.3)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.parsers.gradle_controller import parse_gradle  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ofbiz"


def _parse(relpath):
    path = FIXTURES / relpath
    assert path.is_file(), "missing fixture %s" % relpath
    artifact = artifact_for(FIXTURES, path, "build-gradle")
    ctx = ParseContext(repo_root=FIXTURES, repo_id="fixture-ofbiz-24.09", artifact=artifact, tree=None)
    ctx.component_name = relpath.split("/")[1]
    return parse_gradle(path, ctx), artifact


def test_order_gradle_deps():
    (facts, _), _ = _parse("applications/order/build.gradle")
    deps = {f["props"]["depends_on"]: f["props"] for f in facts if f["kind"] == "module_dependency"}
    assert ":applications:party" in deps
    assert ":applications:accounting" in deps
    assert "org.apache.commons:commons-lang3:3.14.0" in deps
    assert all(f["props"]["module"] == "order" for f in facts)
    assert deps[":applications:party"]["configuration"] == "implementation"


def test_other_modules_gradle_deps():
    (facts, _), _ = _parse("applications/accounting/build.gradle")
    deps = {f["props"]["depends_on"] for f in facts if f["kind"] == "module_dependency"}
    assert ":applications:party" in deps
    (facts, _), _ = _parse("applications/party/build.gradle")
    deps = {f["props"]["depends_on"] for f in facts if f["kind"] == "module_dependency"}
    assert "org.apache.commons:commons-collections4:4.4" in deps


def test_gradle_provenance():
    (facts, _), artifact = _parse("applications/order/build.gradle")
    assert len(artifact.sha256) == 64
    assert facts, "expected module_dependency facts"
    for fact in facts:
        prov = fact["prov"]
        assert prov["file"] == artifact.relpath, fact["id"]
        assert prov["line"] and prov["line"] > 0, fact["id"]
        assert prov["extraction_type"] == "direct", fact["id"]
