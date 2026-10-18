"""Versioned prompts for the controlled probabilistic example."""
from __future__ import annotations

PROMPT_VERSION = "prob-v1"
ALLOWED_PREDICATES = ("suggestsDomain", "managesEntity", "relatesToService", "requiresEntity")

SYSTEM = """You propose enterprise-context hypotheses from Apache OFBiz service metadata.
Rules:
- Output ONLY a JSON array. Each item: {"subject","predicate","object","evidence","confidence"}.
- predicate MUST be one of: %s.
- subject/object: reuse a given "uri" when referring to a known service/entity; otherwise a short new label.
- evidence: 1+ strings quoted VERBATIM from the input (service names, descriptions, attribute names).
- confidence: number 0..1 (your uncertainty; be conservative).
- Propose only what the input supports. Never invent attribute names, engines, or file paths.
""" % (", ".join(ALLOWED_PREDICATES))


def build_user_prompt(services) -> str:
    """services: list of {uri, name, engine, description, params[]} from deterministic facts."""
    lines = ["Deterministic facts (trusted, do not restate as discoveries):"]
    for svc in services:
        lines.append("- uri: %s" % svc["uri"])
        lines.append("  name: %s | engine: %s | description: %s" % (svc["name"], svc.get("engine", "?"), svc.get("description", "")))
        for param in svc.get("params", []):
            lines.append("  param: %s (%s, %s)" % (param["name"], param.get("type", "?"), param.get("mode", "?")))
    lines.append("Propose hypotheses as a JSON array.")
    return "\n".join(lines)


# --- Stage-2 extraction prompt (Algorithm 2; output schema: json_validator) ---

EXTRACTION_SYSTEM = """You extract enterprise semantics from grounded context.
Context you receive: (1) NER entities found in the source text, (2) trusted
deterministic facts (services, entities, methods — do not restate these as
discoveries).
Task: extract business purpose, domain concepts, business rules, and
relationships between the entities below.
Output: ONLY JSON — an array of {"subject","predicate","object",
"confidence","evidence"} claims. confidence is your uncertainty in 0..1
(be conservative).
Grounding instruction: ONLY reference entities that appear in the provided context. Never invent attribute names, engines, file paths, or identifiers.
Propose only what the input supports."""

EXTRACTION_TASK = (
    "Extract business purpose, domain concepts, business rules, relationships"
)


def build_extraction_prompt(ner_entities, facts_summary) -> str:
    """ner_entities: [{text, label}]; facts_summary: pre-rendered fact lines."""
    lines = ["Named entities (spaCy grounding):"]
    for ent in ner_entities:
        lines.append("- %s [%s]" % (ent.get("text", ""), ent.get("label", "")))
    lines.append("Deterministic facts (trusted, do not restate as discoveries):")
    for fact in facts_summary:
        lines.append("- %s" % fact)
    lines.append("%s. Respond with a JSON array of claims." % EXTRACTION_TASK)
    return "\n".join(lines)
