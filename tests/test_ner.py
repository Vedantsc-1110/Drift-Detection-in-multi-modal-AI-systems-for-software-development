"""Task 2.2 tests: spaCy NER + chunking (PART2_PLAN Task 2.2).

Fixture entities (org names, dates, jurisdictions, roles, systems) must be
found; the >4KB policy fixture must split at section boundaries. A stub-nlp
test proves model loading stays behind a fixture-friendly interface.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.prob import chunker  # noqa: E402
from contextgraph.prob import ner  # noqa: E402

POLICY = PROJECT_ROOT / "tests" / "fixtures" / "docs" / "procurement_policy.md"


def _texts(entities, role=None):
    return {e["text"] for e in entities if role is None or e["role"] == role}


def test_fixture_entities_found():
    text = POLICY.read_text(encoding="utf-8")
    entities = ner.extract_entities(text)
    orgs = _texts(entities, "organization")
    assert any("Acme Corporation" in o for o in orgs)
    assert any("2026" in d for d in _texts(entities, "date"))
    assert "California" in _texts(entities, "jurisdiction")
    assert any("Procurement Officer" in r for r in _texts(entities, "role"))
    assert any("Order Management System" in s for s in _texts(entities, "system"))
    for ent in entities:
        assert ent["end"] > ent["start"]


def test_chunker_splits_large_fixture_at_sections():
    text = POLICY.read_text(encoding="utf-8")
    assert len(text) > 4096
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    assert all(c["text"] for c in chunks)
    assert all(c["heading"] for c in chunks)
    assert [c["index"] for c in chunks] == list(range(len(chunks)))
    assert all(len(c["text"]) <= 4000 for c in chunks)
    joined = "".join(c["text"] for c in chunks)
    assert len(joined) >= len(text) - len(chunks)


def test_nlp_injectable_behind_interface():
    fake_doc = SimpleNamespace(ents=[SimpleNamespace(text="Acme", label_="ORG", start_char=0, end_char=4)])
    entities = ner.extract_entities("Acme", nlp=lambda text: fake_doc)
    assert entities[0] == {"text": "Acme", "label": "ORG", "role": "organization", "start": 0, "end": 4}
