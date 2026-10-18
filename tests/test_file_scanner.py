"""Task 1.1 tests: incremental SHA-256 scanner (PART1_PLAN Task 1.1).

Covers the four required cases:
(a) first run returns all files;
(b) second run with no edits returns empty list;
(c) editing one file returns exactly that file;
(d) cache stores valid SHA-256 hex.

Standalone: uses tmp_path only, no OFBiz dataset, no network.
"""

import hashlib
import json
from pathlib import Path

from contextgraph.file_scanner import scan


def _make_tree(root: Path) -> list[Path]:
    files = [
        root / "applications" / "order" / "servicedef" / "services.xml",
        root / "applications" / "order" / "entitydef" / "order-entity.xml",
        root / "applications" / "order" / "src" / "OrderServices.java",
        root / "applications" / "order" / "src" / "OrderHelper.groovy",
        root / "applications" / "order" / "build.gradle",
        root / "applications" / "order" / "README.txt",  # must be ignored
    ]
    for path in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<root>%s</root>" % path.name, encoding="utf-8")
    return [p for p in files if p.suffix != ".txt"]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


EXTS = (".xml", ".java", ".groovy", ".gradle")


def test_first_run_returns_all_files(tmp_path):
    root = tmp_path / "repo"
    expected = _make_tree(root)
    cache = tmp_path / "out" / ".hash_cache.json"
    got = scan(root, EXTS, cache)
    assert sorted(got) == sorted(expected)


def test_second_run_no_edits_returns_empty(tmp_path):
    root = tmp_path / "repo"
    _make_tree(root)
    cache = tmp_path / "out" / ".hash_cache.json"
    assert scan(root, EXTS, cache)  # first run
    assert scan(root, EXTS, cache) == []  # second run, no edits


def test_editing_one_file_returns_exactly_that_file(tmp_path):
    root = tmp_path / "repo"
    _make_tree(root)
    cache = tmp_path / "out" / ".hash_cache.json"
    scan(root, EXTS, cache)
    target = root / "applications" / "order" / "src" / "OrderServices.java"
    target.write_text("edited content", encoding="utf-8")
    got = scan(root, EXTS, cache)
    assert got == [target]


def test_cache_stores_valid_sha256_hex(tmp_path):
    root = tmp_path / "repo"
    tracked = _make_tree(root)
    cache = tmp_path / "out" / ".hash_cache.json"
    scan(root, EXTS, cache)
    data = json.loads(cache.read_text(encoding="utf-8"))
    assert len(data) == len(tracked)
    for path in tracked:
        rel = path.relative_to(root).as_posix()
        assert rel in data
        digest = data[rel]
        assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
        assert digest == _sha256(path)


def test_missing_cache_dir_and_extension_param(tmp_path):
    root = tmp_path / "repo"
    only_py = root / "dags" / "etl.py"
    only_py.parent.mkdir(parents=True, exist_ok=True)
    only_py.write_text("x = 1", encoding="utf-8")
    cache = tmp_path / "newdir" / "nested" / "cache.json"
    # .py not in default XML set -> empty; proves extension list is a parameter
    assert scan(root, (".xml",), cache) == []
    assert scan(root, (".py",), cache) == [only_py]
