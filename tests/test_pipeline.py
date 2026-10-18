"""Pipeline tests: determinism, read-only dataset, resolution honesty."""
import hashlib
import json
from pathlib import Path

from contextgraph.pipeline import run


def _hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def test_pipeline_deterministic(repo_root, tmp_path):
    out1, out2 = tmp_path / "a", tmp_path / "b"
    run(repo_root, "order", out1)
    run(repo_root, "order", out2)
    for name in ("order-facts.jsonl", "order-unresolved.json"):
        assert (out1 / name).read_bytes() == (out2 / name).read_bytes()


def test_dataset_not_modified(repo_root):
    probe = repo_root / "applications" / "order" / "servicedef" / "services.xml"
    before = _hash_file(probe)
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        run(repo_root, "order", Path(tmp))
    assert _hash_file(probe) == before


def test_facts_have_provenance_and_no_confidence(repo_root, tmp_path):
    run(repo_root, "order", tmp_path)
    n = 0
    for line in (tmp_path / "order-facts.jsonl").read_text(encoding="utf-8").splitlines():
        fact = json.loads(line)
        prov = fact["prov"]
        assert prov["repository"] == "apache-ofbiz-24.09.07"
        assert prov["file"].startswith("applications/order/")
        assert prov["extraction_type"] in ("direct", "inferred")
        assert "confidence" not in fact["props"] and "confidence" not in prov
        if prov["extraction_type"] == "inferred":
            assert prov["evidence"], fact["id"]
        n += 1
    assert n > 1000


def test_out_of_scope_entities_unresolved_not_minted(repo_root, tmp_path):
    run(repo_root, "order", tmp_path)
    ids = set()
    for line in (tmp_path / "order-facts.jsonl").read_text(encoding="utf-8").splitlines():
        ids.add(json.loads(line)["id"])
    assert "http://example.org/ofbiz/0.1/entity/OrderHeader" not in ids
    unresolved = json.loads((tmp_path / "order-unresolved.json").read_text(encoding="utf-8"))
    assert any(u.get("to_name") == "OrderHeader" for u in unresolved)
