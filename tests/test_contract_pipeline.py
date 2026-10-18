"""Task 1.8 tests: fixtures + unit suite + pipeline CLI (PART1_PLAN Task 1.8).

End-to-end run of contract_pipeline over tests/fixtures (zero network):
outputs exist and parse, all extractor areas represented, byte-deterministic
triple sets across runs, and no network imports in Part 1 modules.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

rdflib = pytest.importorskip("rdflib")

from contextgraph.contract_pipeline import run  # noqa: E402
from contextgraph.serializer import OUTPUT_FILES  # noqa: E402

FIXTURES = PROJECT_ROOT / "tests" / "fixtures"
GENERATED_AT = "2026-01-01T00:00:00+00:00"

REQUIRED_KINDS = {
    "service", "service_param", "entity", "entity_field", "relation",
    "eca", "condition", "eca_action", "route", "module_dependency",
    "java_class", "java_method", "java_call", "java_import",
    "airflow_dag", "airflow_task", "cicd_workflow", "cicd_job", "cicd_step",
}


def _triples(path):
    g = rdflib.Graph()
    g.parse(str(path), format="turtle")
    return set(g)


def test_end_to_end_outputs_and_manifest(tmp_path):
    manifest = run(FIXTURES, tmp_path, GENERATED_AT)
    assert manifest["errors"] == []
    assert manifest["skipped"] == []
    assert len(manifest["files"]) >= 20
    for name in OUTPUT_FILES:
        assert (tmp_path / name).is_file()
        assert manifest["outputs"][name] > 0, name
    missing = REQUIRED_KINDS - set(manifest["counts"])
    assert not missing, "unrepresented areas: %s" % sorted(missing)


def test_deterministic_triple_sets(tmp_path):
    out_a, out_b = tmp_path / "a", tmp_path / "b"
    run(FIXTURES, out_a, GENERATED_AT)
    run(FIXTURES, out_b, GENERATED_AT)
    for name in OUTPUT_FILES:
        assert _triples(out_a / name) == _triples(out_b / name), name


def test_no_network_usage_in_part1_modules():
    base = PROJECT_ROOT / "src" / "contextgraph"
    modules = [base / "file_scanner.py", base / "triple_builder.py", base / "serializer.py",
               base / "contract_pipeline.py", base / "scanner.py", base / "provenance.py",
               base / "facts.py"] + sorted((base / "parsers").glob("*.py"))
    assert len(modules) > 10
    for path in modules:
        text = path.read_text(encoding="utf-8")
        for banned in ("import requests", "urllib.request", "urllib.error", "import socket", "http.client", "urlopen"):
            assert banned not in text, "%s uses %s" % (path.name, banned)
