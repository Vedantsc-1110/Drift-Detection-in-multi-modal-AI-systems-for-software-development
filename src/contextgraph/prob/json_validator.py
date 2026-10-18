"""Validated LLM JSON output (PART2_PLAN Task 2.1, Algorithm 2).

Frozen extraction-output schema (OPEN_QUESTIONS Q13 contribution):
  top level: JSON array of claims, or {"claims": [...]}
  claim: {"subject": str, "predicate": str, "object": str,
          "confidence": number 0..1, "evidence": [str] (optional)}

Malformed responses are rejected with surfaced errors; valid claims are
returned as typed claim dicts. Nothing is silently dropped: every skipped
claim has a matching error entry.
"""

from __future__ import annotations

import json


def make_response(model: str, claims: list, errors: list) -> dict:
    return {"model": model, "claims": claims, "errors": errors}


def _claim_errors(item, index: int) -> list:
    errors = []
    if not isinstance(item, dict):
        return ["claim #%d: must be an object" % index]
    for field in ("subject", "predicate", "object"):
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append("claim #%d: missing/empty %r" % (index, field))
    conf = item.get("confidence")
    if not (isinstance(conf, (int, float)) and not isinstance(conf, bool) and 0.0 <= float(conf) <= 1.0):
        errors.append("claim #%d: confidence must be a number in [0, 1]" % index)
    if "evidence" in item:
        ev = item["evidence"]
        if not (isinstance(ev, list) and all(isinstance(x, str) for x in ev)):
            errors.append("claim #%d: evidence must be a list of strings" % index)
    return errors


def validate_response(text: str, model: str) -> dict:
    """Parse + validate raw LLM text into a typed LlmResponse dict."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return make_response(model, [], ["response is not valid JSON: %s" % exc])
    if isinstance(data, dict):
        if "claims" not in data:
            return make_response(model, [], ["response object must contain a 'claims' array"])
        items = data["claims"]
    elif isinstance(data, list):
        items = data
    else:
        return make_response(model, [], ["response must be a JSON array or {'claims': [...]}"])
    if not isinstance(items, list):
        return make_response(model, [], ["'claims' must be an array"])
    claims, errors = [], []
    for i, item in enumerate(items):
        item_errors = _claim_errors(item, i)
        if item_errors:
            errors.extend(item_errors)
            continue
        claims.append(
            {
                "subject": item["subject"].strip(),
                "predicate": item["predicate"].strip(),
                "object": item["object"].strip(),
                "confidence": float(item["confidence"]),
                "evidence": list(item.get("evidence") or []),
            }
        )
    return make_response(model, claims, errors)
