"""Propose flow: deterministic input -> model -> validated ProbabilisticFacts."""
from __future__ import annotations

import datetime
import json

from . import prompts
from .schema import EXTRACTION_TYPE, is_valid, validate


def collect_example_services(facts, source_file: str):
    """Small controlled input: services + explicit params from one source file."""
    services = {}
    for fact in facts:
        prov = fact.get("prov", {})
        if prov.get("file") != source_file:
            continue
        if fact["kind"] == "service":
            services[fact["props"]["name"]] = {
                "uri": fact["id"],
                "name": fact["props"]["name"],
                "engine": fact["props"].get("engine", ""),
                "description": fact["props"].get("description", ""),
                "params": [],
            }
        elif fact["kind"] == "service_param" and "via" not in fact["id"]:
            for svc in services.values():
                if fact["id"].startswith(svc["uri"] + "/param/"):
                    svc["params"].append(
                        {"name": fact["props"]["name"], "type": fact["props"].get("type", ""),
                         "mode": fact["props"].get("mode", "")}
                    )
    return sorted(services.values(), key=lambda s: s["name"])


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def propose(client, services, model_name: str, now=None):
    """Call the model; return (facts, errors). Facts are status=proposed."""
    raw = client.complete_json(prompts.SYSTEM, prompts.build_user_prompt(services))
    try:
        items = json.loads(raw)
    except Exception as exc:
        return [], ["model output is not valid JSON: %s" % exc]
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return [], ["model output must be a JSON array"]
    now = now or _utcnow()
    facts, errors = [], []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append("item %d: not an object" % i)
            continue
        fact = {
            "subject": item.get("subject", ""),
            "predicate": item.get("predicate", ""),
            "object": item.get("object", ""),
            "evidence": item.get("evidence", []),
            "confidence": item.get("confidence"),
            "model": model_name,
            "promptVersion": prompts.PROMPT_VERSION,
            "extractionType": EXTRACTION_TYPE,
            "status": "proposed",
            "extractedAt": now,
        }
        problems = validate(fact)
        if problems:
            errors.append("item %d: %s" % (i, "; ".join(problems)))
            continue
        if fact["predicate"] not in prompts.ALLOWED_PREDICATES:
            errors.append("item %d: predicate outside controlled vocabulary" % i)
            continue
        facts.append(fact)
    return facts, errors
