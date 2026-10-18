"""Experiment framework tests: template determinism, scoring math, schema shape."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXP = PROJECT_ROOT / "experiments" / "context-identification"
EVAL = EXP / "eval.py"


def _run(*args):
    proc = subprocess.run([sys.executable, str(EVAL), *args], cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc


def _synthetic(tmp_path):
    facts = [
        {"id": "A:f1", "kind": "service", "props": {"name": "f1"},
         "prov": {"file": "x.xml", "line": 1, "extraction_type": "direct"}},
        {"id": "A:f2", "kind": "service", "props": {"name": "f2"},
         "prov": {"file": "x.xml", "line": None, "extraction_type": "direct"}},
    ]
    facts_p = tmp_path / "facts.jsonl"
    facts_p.write_text("\n".join(json.dumps(f, sort_keys=True) for f in facts) + "\n", encoding="utf-8")
    proposals = [
        {"subject": "s", "predicate": "suggestsDomain", "object": "o",
         "evidence": ["f1"], "confidence": 0.5, "model": "stub-test-client",
         "promptVersion": "prob-v1", "extractionType": "probabilistic",
         "status": "accepted", "extractedAt": "2026-01-01T00:00:00+00:00"},
    ]
    prop_p = tmp_path / "prop.jsonl"
    prop_p.write_text("\n".join(json.dumps(p, sort_keys=True) for p in proposals) + "\n", encoding="utf-8")
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps({"name": "syn", "files": ["x.xml"]}), encoding="utf-8")
    return facts_p, prop_p, sample


def test_init_deterministic_and_sampling(tmp_path):
    facts_p, prop_p, sample = _synthetic(tmp_path)
    t1, t2 = tmp_path / "t1.jsonl", tmp_path / "t2.jsonl"
    _run("init", "--facts", str(facts_p), "--proposals", str(prop_p),
         "--sample", str(sample), "--out", str(t1), "--max-items", "1", "--seed", "7")
    _run("init", "--facts", str(facts_p), "--proposals", str(prop_p),
         "--sample", str(sample), "--out", str(t2), "--max-items", "1", "--seed", "7")
    assert t1.read_bytes() == t2.read_bytes()
    items = [json.loads(x) for x in t1.read_text(encoding="utf-8").splitlines()]
    assert sum(1 for x in items if x["arm"] == "A") == 1  # sampled
    assert sum(1 for x in items if x["arm"] == "B") == 1  # proposals always whole
    assert all(set(x) >= {"key", "arm", "kind", "summary", "file", "verdict", "reviewer", "note"} for x in items)


def test_score_math_on_synthetic(tmp_path):
    facts_p, prop_p, sample = _synthetic(tmp_path)
    template = [
        {"key": "A:A:f1", "arm": "A", "kind": "service", "summary": "s", "file": "x.xml",
         "line": 1, "verdict": "correct", "reviewer": "t", "note": ""},
        {"key": "A:A:f2", "arm": "A", "kind": "service", "summary": "s", "file": "x.xml",
         "line": None, "verdict": "incorrect", "reviewer": "t", "note": ""},
        {"key": "B:0:s|suggestsDomain|o", "arm": "B", "kind": "probabilistic-proposal",
         "summary": "s", "file": "(model)", "line": None, "verdict": "correct", "reviewer": "t", "note": ""},
    ]
    tmpl = tmp_path / "adj.jsonl"
    tmpl.write_text("\n".join(json.dumps(x, sort_keys=True) for x in template) + "\n", encoding="utf-8")
    out = tmp_path / "results.json"
    _run("score", "--template", str(tmpl), "--facts", str(facts_p), "--proposals", str(prop_p),
         "--sample", str(sample), "--out", str(out))
    results = json.loads(out.read_text(encoding="utf-8"))
    a, b, c = (results["arms"][k] for k in ("A_deterministic", "B_probabilistic", "C_hybrid"))
    assert (a["correct"], a["unsupported"], a["accuracy"]) == (1, 1, 0.5)
    assert a["provenance_coverage"] == {"covered": 1, "total": 2, "rate": 0.5}
    assert b["accuracy"] == 1.0
    # Proposal accepted -> joins hybrid C.
    assert c["extracted"] == 3 and c["accuracy"] == round(2 / 3, 4)
    rep = tmp_path / "report.md"
    _run("report", "--results", str(out), "--out-md", str(rep))
    assert "| Accuracy (adjudicated only) | 0.5 | 1.0 |" in rep.read_text(encoding="utf-8")


def test_committed_sample_results_recompute(tmp_path):
    """The committed numbers must be reproducible from committed inputs."""
    out = tmp_path / "re.json"
    _run("score",
         "--template", str(EXP / "ground-truth" / "order-reservations.adjudicated.jsonl"),
         "--facts", str(PROJECT_ROOT / "outputs" / "order-facts.jsonl"),
         "--proposals", str(PROJECT_ROOT / "outputs" / "prob" / "reservations-proposals.jsonl"),
         "--sample", str(EXP / "samples" / "order-reservations.json"),
         "--out", str(out))
    committed = json.loads((EXP / "results" / "order-reservations.results.json").read_text(encoding="utf-8"))
    fresh = json.loads(out.read_text(encoding="utf-8"))
    for arm in ("A_deterministic", "B_probabilistic", "C_hybrid"):
        for metric in ("extracted", "adjudicated", "correct", "unsupported", "pending", "accuracy"):
            assert fresh["arms"][arm][metric] == committed["arms"][arm][metric], (arm, metric)
