"""Shared fixtures: real OFBiz files, read-only. Tests never write to the dataset."""
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.provenance import ParseContext, artifact_for, parse_xml  # noqa: E402


def _repo_root():
    env = os.environ.get("OFBIZ_ROOT")
    if env:
        return Path(env)
    return PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"


@pytest.fixture(scope="session")
def repo_root():
    root = _repo_root()
    assert root.is_dir(), "OFBiz dataset not found at %s" % root
    return root


@pytest.fixture(scope="session")
def order_dir(repo_root):
    d = repo_root / "applications" / "order"
    assert d.is_dir()
    return d


def parse_file(repo_root, relpath, role, artifact_type):
    """Parse one real file through its registered parser; return (facts, candidates, ctx)."""
    from contextgraph.parsers import PARSERS

    path = repo_root / relpath
    assert path.is_file(), "missing fixture file %s" % relpath
    artifact = artifact_for(repo_root, path, artifact_type)
    tree = parse_xml(path)
    ctx = ParseContext(repo_root=repo_root, repo_id="apache-ofbiz-24.09.07", artifact=artifact, tree=tree)
    ctx.component_name = "order"
    facts, candidates = PARSERS[role](path, ctx)
    return facts, candidates, ctx


def by_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]
