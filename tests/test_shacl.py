"""SHACL tests: valid graph conforms, crafted invalid graph fails, reports produced."""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHAPES = PROJECT_ROOT / "ontology" / "context-shapes.ttl"

pyshacl = pytest.importorskip("pyshacl")

from contextgraph.validate import validate_graph  # noqa: E402

NB = "http://example.org/ofbiz/0.1/"

INVALID_TTL = """@prefix ofbiz: <http://example.org/ofbiz/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://ex/svc-no-name> a ofbiz:Service .

<http://ex/svc-no-impl> a ofbiz:Service ;
    ofbiz:name "x" ;
    ofbiz:implLocation "org.example.Svc" ;
    ofbiz:implInvoke "run" ;
    ofbiz:definedIn <http://ex/art> ;
    ofbiz:extractionType "direct" .

<http://ex/eca-no-event> a ofbiz:EntityECA ;
    ofbiz:ecaOperation "create-store" ;
    ofbiz:triggerEntityName "OrderHeader" ;
    ofbiz:definedIn <http://ex/art> ;
    ofbiz:extractionType "direct" .

<http://ex/cond-no-operator> a ofbiz:Condition ;
    ofbiz:condField "statusId" ;
    ofbiz:definedIn <http://ex/art> ;
    ofbiz:extractionType "direct" .

<http://ex/attr-no-prov> a ofbiz:Attribute ;
    ofbiz:name "lonely" .
"""


@pytest.fixture(scope="module")
def real_graph(tmp_path_factory):
    work = tmp_path_factory.mktemp("shacl")
    fx = work / "fx"
    repo = PROJECT_ROOT / "dataset" / "apache-ofbiz-24.09.07"
    assert repo.is_dir(), "OFBiz dataset missing"
    subprocess.run(
        [sys.executable, "extract.py", "--root", str(repo), "--component", "order", "--out", str(fx)],
        cwd=PROJECT_ROOT,
        check=True,
    )
    ttl = work / "order-graph.ttl"
    subprocess.run(
        [
            sys.executable, "build_graph.py", "--facts", str(fx / "order-facts.jsonl"),
            "--manifest", str(fx / "order-manifest.json"), "--out", str(ttl),
            "--as-of", "2026-01-01T00:00:00+00:00",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    return ttl


def test_valid_graph_conforms(real_graph):
    result = validate_graph(real_graph, SHAPES)
    assert result["conforms"] is True
    assert result["violations"] == []
    assert result["report_text"].strip() != ""


def test_warnings_do_not_fail(real_graph):
    result = validate_graph(real_graph, SHAPES)
    # Dangling out-of-component ECA actions are legitimately reported...
    assert len(result["warnings"]) > 0
    # ...but must not fail validation.
    assert result["conforms"] is True


def test_invalid_graph_fails(tmp_path):
    bad = tmp_path / "bad.ttl"
    bad.write_text(INVALID_TTL, encoding="utf-8")
    result = validate_graph(bad, SHAPES)
    assert result["conforms"] is False
    paths = {v["path"] for v in result["violations"]}
    messages = [v["message"] for v in result["violations"]]
    assert NB + "name" in paths  # service without name
    assert any("must link ofbiz:implementedBy" in m for m in messages)  # stated binding without link
    assert NB + "ecaEvent" in paths  # ECA without event
    assert NB + "condOperator" in paths  # condition without operator
    assert NB + "definedIn" in paths  # provenance missing
    assert result["report_text"].strip() != ""


def test_validation_report_file(real_graph, tmp_path):
    out = tmp_path / "validation.txt"
    proc = subprocess.run(
        [sys.executable, "validate_graph.py", "--graph", str(real_graph),
         "--shapes", str(SHAPES), "--out", str(out)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    text = out.read_text(encoding="utf-8")
    assert "conforms: True" in text
    assert "violations: 0" in text
    assert "Warnings" in text
