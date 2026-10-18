"""Task 4.2 tests: change detection (PART4_PLAN Task 4.2, §7.3 Step 1).

A tmp git repo (built at runtime) gets two commits; detection yields the
changed paths, commit SHA, and extractor-routing categories. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

git = pytest.importorskip("git")

from contextgraph.drift.change_detector import classify, detect_changes  # noqa: E402


def _commit(repo, message):
    repo.index.add([str(p.relative_to(repo.working_dir)) for p in Path(repo.working_dir).rglob("*") if p.is_file() and ".git" not in p.parts])
    return repo.index.commit(message)


@pytest.fixture()
def repo(tmp_path):
    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "drift-test")
        config.set_value("user", "email", "drift@example.org")
    (tmp_path / "servicedef").mkdir()
    (tmp_path / "servicedef" / "services.xml").write_text("<services/>", encoding="utf-8")
    _commit(repo, "initial import")
    (tmp_path / "servicedef" / "services.xml").write_text("<services><service/></services>", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "policy.md").write_text("# Policy", encoding="utf-8")
    _commit(repo, "update service + add policy")
    yield repo
    repo.close()


def test_changed_paths_and_sha(repo):
    event = detect_changes(repo.working_dir)
    assert len(event["commit_sha"]) == 40 and all(c in "0123456789abcdef" for c in event["commit_sha"])
    assert event["message"] == "update service + add policy"
    assert event["committed_at"]
    by_path = {c["path"]: c for c in event["changed"]}
    assert set(by_path) == {"servicedef/services.xml", "docs/policy.md"}
    assert by_path["servicedef/services.xml"]["change_type"] == "M"
    assert by_path["docs/policy.md"]["change_type"] == "A"


def test_classification_routes_extractors(repo):
    event = detect_changes(repo.working_dir)
    by_path = {c["path"]: c["category"] for c in event["changed"]}
    assert by_path == {"servicedef/services.xml": "source", "docs/policy.md": "document"}
    assert classify(".github/workflows/ci.yml") == "workflow"
    assert classify("notes.bin") == "other"


def test_explicit_since_sha(repo):
    first = repo.commit("HEAD~1").hexsha
    event = detect_changes(repo.working_dir, since_sha=first)
    assert event["commit_sha"] == repo.head.commit.hexsha
    assert {c["path"] for c in event["changed"]} == {"servicedef/services.xml", "docs/policy.md"}
    with pytest.raises(ValueError):
        detect_changes(repo.working_dir, since_sha="0" * 40)
