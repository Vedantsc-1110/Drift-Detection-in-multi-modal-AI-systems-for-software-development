"""Task 1.6 tests: CI/CD GitHub Actions extractor (PART1_PLAN Task 1.6).

Standalone on tests/fixtures/cicd (synthetic). Every job/step/trigger/needs
edge extracted; secrets and env references recorded; full provenance;
graph == urn:cicd.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.parsers import cicd_yaml  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "cicd" / ".github" / "workflows"


def _parse(name):
    path = FIXTURES / name
    assert path.is_file(), "missing fixture %s" % name
    artifact = artifact_for(PROJECT_ROOT, path, "cicd-workflow")
    assert len(artifact.sha256) == 64
    ctx = ParseContext(repo_root=PROJECT_ROOT, repo_id="fixture-cicd", artifact=artifact, tree=None)
    ctx.component_name = "cicd"
    return cicd_yaml.parse(path, ctx)


def _by_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]


def test_ci_triggers_jobs_and_needs():
    facts, _ = _parse("ci.yml")
    (wf,) = _by_kind(facts, "cicd_workflow")
    assert wf["props"]["name"] == "CI"
    assert {t["event"] for t in wf["props"]["triggers"]} == {"push", "pull_request"}
    jobs = {f["props"]["job_id"]: f for f in _by_kind(facts, "cicd_job")}
    assert set(jobs) == {"test", "lint"}
    assert jobs["lint"]["props"]["needs"] == ["test"]
    needs = {(e["props"]["from"].rsplit("/", 1)[-1], e["props"]["to"].rsplit("/", 1)[-1]) for e in _by_kind(facts, "edge") if e["props"]["predicate"] == "dependsOn"}
    assert needs == {("lint", "test")}


def test_ci_steps_uses_and_secrets():
    facts, _ = _parse("ci.yml")
    steps = _by_kind(facts, "cicd_step")
    assert len(steps) == 5  # 3 in test + 2 in lint
    uses = {s["props"]["uses"] for s in steps if s["props"]["uses"]}
    assert uses == {"actions/checkout@v4", "actions/setup-python@v5"}
    assert any(
        s["props"]["name"] == "Run tests" and s["props"]["secrets"] == ["TEST_TOKEN"] for s in steps
    )
    assert any("PYTHON_VERSION" in s["props"]["env_refs"] for s in steps)
    assert len([e for e in _by_kind(facts, "edge") if e["props"]["predicate"] == "usesAction"]) == 3
    assert len([e for e in _by_kind(facts, "edge") if e["props"]["predicate"] == "hasStep"]) == 5


def test_release_schedule_trigger_and_deploy_chain():
    facts, _ = _parse("release.yml")
    (wf,) = _by_kind(facts, "cicd_workflow")
    events = {t["event"] for t in wf["props"]["triggers"]}
    assert events == {"push", "schedule", "workflow_dispatch"}
    assert any(t["event"] == "schedule" and "cron" in t["detail"] for t in wf["props"]["triggers"])
    jobs = {f["props"]["job_id"]: f for f in _by_kind(facts, "cicd_job")}
    assert jobs["deploy"]["props"]["needs"] == ["build"]
    steps = _by_kind(facts, "cicd_step")
    build_img = next(s for s in steps if s["props"]["name"] == "Build image")
    assert build_img["props"]["uses"] == "docker/build-push-action@v6"
    assert build_img["props"]["secrets"] == ["DOCKER_PASSWORD", "DOCKER_USER"]
    scan = next(s for s in steps if s["props"]["name"] == "Scan image")
    assert "REGISTRY" in scan["props"]["env_refs"]
    deploy = next(s for s in steps if s["props"]["name"] == "Deploy")
    assert deploy["props"]["secrets"] == ["DEPLOY_TOKEN"]


def test_provenance_and_graph():
    for name in ("ci.yml", "release.yml"):
        facts, _ = _parse(name)
        assert facts, name
        for fact in facts:
            assert fact["props"].get("graph") == "urn:cicd", fact["id"]
            prov = fact["prov"]
            assert prov["file"].endswith(name), fact["id"]
            assert prov["line"] and prov["line"] > 0, fact["id"]
            assert prov["extraction_type"] == "direct", fact["id"]
