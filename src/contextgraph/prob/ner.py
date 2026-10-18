"""spaCy NER preprocessing (PART2_PLAN Task 2.2, Algorithm 2 "Preprocessing").

Extracts organizations, systems, roles, dates, jurisdictions from text.
Model loading is isolated behind load_model() and every entry point accepts
an injectable ``nlp`` so tests stay fixture-friendly (pass a stub or a
blank pipeline; production passes None for the cached default model).
"""

from __future__ import annotations

import re
from typing import Any

MODEL_NAME = "en_core_web_sm"

# spaCy label -> plan role
ROLE_BY_LABEL = {
    "ORG": "organization",
    "PRODUCT": "system",
    "PERSON": "person",
    "DATE": "date",
    "TIME": "date",
    "GPE": "jurisdiction",
    "LOC": "jurisdiction",
}

_ROLE_TITLE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Officer|Manager|Administrator|Clerk|Approver|Auditor))\b"
)
_SYSTEM_HINT = re.compile(r"\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\s+System)\b")

_nlp_cache: dict[str, Any] = {}


def load_model(name: str = MODEL_NAME):
    """Load (and cache) a spaCy model. Isolated for tests to stub."""
    if name not in _nlp_cache:
        import spacy

        _nlp_cache[name] = spacy.load(name)
    return _nlp_cache[name]


def extract_entities(text: str, nlp=None) -> list:
    """Return [{text, label, role, start, end}] sorted by offset, deduped."""
    if nlp is None:
        nlp = load_model()
    doc = nlp(text)
    found: list = []
    for ent in getattr(doc, "ents", []):
        role = ROLE_BY_LABEL.get(getattr(ent, "label_", ""), "other")
        found.append(
            {
                "text": ent.text,
                "label": getattr(ent, "label_", ""),
                "role": _refine_role(ent.text, role),
                "start": int(getattr(ent, "start_char", 0)),
                "end": int(getattr(ent, "end_char", 0)),
            }
        )
    for match in _ROLE_TITLE.finditer(text):
        found.append({"text": match.group(1), "label": "TITLE", "role": "role",
                      "start": match.start(1), "end": match.end(1)})
    seen, out = set(), []
    for ent in sorted(found, key=lambda e: (e["start"], e["end"])):
        key = (ent["text"], ent["role"], ent["start"])
        if key not in seen:
            seen.add(key)
            out.append(ent)
    return out


def _refine_role(text: str, role: str) -> str:
    if role == "organization" and _SYSTEM_HINT.search(text):
        return "system"
    return role
