"""Task 4.3 tests: incremental re-extraction (PART4_PLAN Task 4.3, Step 2).

Fake extractor command (pre-baked .ttl, subprocess, no imports); unchanged
files skipped; exactly the edited file re-processed; cache updated. Offline.
"""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.drift.incremental import run_incremental  # noqa: E402

TTL = """@prefix ctx: <http://context.example.org/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
ctx:%s a ctx:Service ; rdfs:label "%s" .
"""


@pytest.fixture()
def tree(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "a.xml").write_text("<a/>", encoding="utf-8")
    (root / "b.xml").write_text("<b/>", encoding="utf-8")
    (root / "sub").mkdir()
    (root / "sub" / "c.xml").write_text("<c/>", encoding="utf-8")
    baked = tmp_path / "baked.ttl"
    fake = tmp_path / "fake_extractor.py"
    fake.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "src, out, template = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])\n"
        "out.write_text(template.read_text(encoding='utf-8').replace('STUB', src.stem), encoding='utf-8')\n",
        encoding="utf-8")
    return root, tmp_path, baked, fake


def _cmd(fake, baked):
    return [sys.executable, str(fake), "{file}", "{out}", str(baked)]


def _bake(baked, name):
    baked.write_text(TTL % (name, name), encoding="utf-8")


def test_first_run_processes_all(tree, tmp_path):
    root, tmp, baked, fake = tree
    _bake(baked, "STUB")
    result = run_incremental(root, tmp / "cache.json", _cmd(fake, baked), tmp / "out")
    assert result["processed"] == ["a.xml", "b.xml", "sub/c.xml"]
    assert result["skipped"] == []
    assert result["triples"] == 3 * 2
    cache = json.loads((tmp / "cache.json").read_text(encoding="utf-8"))
    assert set(cache) == {"a.xml", "b.xml", "sub/c.xml"}


def test_second_run_skips_unchanged_and_reprocesses_edited(tree, tmp_path):
    root, tmp, baked, fake = tree
    _bake(baked, "STUB")
    cache = tmp / "cache.json"
    out = tmp / "out"
    run_incremental(root, cache, _cmd(fake, baked), out)
    (root / "b.xml").write_text("<b><changed/></b>", encoding="utf-8")
    result = run_incremental(root, cache, _cmd(fake, baked), out)
    assert result["processed"] == ["b.xml"]
    assert result["skipped"] == ["a.xml", "sub/c.xml"]
    merged = rdflib.Graph()
    merged.parse(result["merged"], format="turtle")
    assert len(merged) == 2
    assert (rdflib.URIRef("http://context.example.org/b"),
            rdflib.RDF.type,
            rdflib.URIRef("http://context.example.org/Service")) in merged


def test_extractor_contract_enforced(tree, tmp_path):
    root, tmp, baked, fake = tree
    with pytest.raises(ValueError):
        run_incremental(root, tmp / "cache.json", [sys.executable, "x.py"], tmp / "out")


def test_same_basename_in_different_directories_does_not_overwrite(tree):
    root, tmp, baked, fake = tree
    (root / "sub" / "a.xml").write_text("<another/>", encoding="utf-8")
    _bake(baked, "STUB")
    result = run_incremental(root, tmp / "cache.json", _cmd(fake, baked), tmp / "out")
    assert result["processed"] == ["a.xml", "b.xml", "sub/a.xml", "sub/c.xml"]
    assert (tmp / "out" / "a.xml.ttl").is_file()
    assert (tmp / "out" / "sub" / "a.xml.ttl").is_file()


def test_missing_cached_output_is_rebuilt(tree):
    root, tmp, baked, fake = tree
    _bake(baked, "STUB")
    cache = tmp / "cache.json"
    run_incremental(root, cache, _cmd(fake, baked), tmp / "out")
    # A hash cache alone must not skip files after its extraction outputs vanish.
    result = run_incremental(root, cache, _cmd(fake, baked), tmp / "fresh-out")
    assert result["processed"] == ["a.xml", "b.xml", "sub/c.xml"]
