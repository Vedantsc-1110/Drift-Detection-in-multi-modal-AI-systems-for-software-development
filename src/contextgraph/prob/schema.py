"""ProbabilisticFact schema + validation. No I/O, no LLM calls here."""
from __future__ import annotations

REQUIRED = ["subject", "predicate", "object", "evidence", "confidence",
            "model", "promptVersion", "extractionType", "status"]
STATUSES = ("proposed", "accepted", "rejected")
EXTRACTION_TYPE = "probabilistic"


def validate(data) -> list:
    """Return a list of error strings; empty means valid."""
    errors = []
    if not isinstance(data, dict):
        return ["fact must be an object"]
    for field in REQUIRED:
        if field not in data or data[field] in (None, ""):
            errors.append("missing/empty required field: %s" % field)
    for field in ("subject", "predicate", "object", "model", "promptVersion"):
        if field in data and not isinstance(data[field], str):
            errors.append("field must be a string: %s" % field)
    ev = data.get("evidence")
    if ev is not None and not (isinstance(ev, list) and ev and all(isinstance(x, str) and x.strip() for x in ev)):
        errors.append("evidence must be a non-empty list of non-empty strings")
    conf = data.get("confidence")
    if conf is not None and not (isinstance(conf, (int, float)) and not isinstance(conf, bool) and 0.0 <= float(conf) <= 1.0):
        errors.append("confidence must be a number in [0, 1]")
    if data.get("extractionType") != EXTRACTION_TYPE:
        errors.append("extractionType must be exactly %r" % EXTRACTION_TYPE)
    if data.get("status") not in STATUSES:
        errors.append("status must be one of %s" % (STATUSES,))
    return errors


def is_valid(data) -> bool:
    return validate(data) == []
