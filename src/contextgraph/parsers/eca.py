"""Parser: ECA files (entity-eca eecas.xml, service-eca secas.xml).

Direct: ECA nodes, conditions, actions. Candidates: trigger targets and
action-service targets, resolved by the pipeline against known services/entities.
"""
from __future__ import annotations

import hashlib

from ..facts import base_prov, make_fact, uri
from ..provenance import localname

METHOD = "xml-attribute-read"
REF_METHOD = "xml-literal-reference"


def parse(path, ctx):
    facts = []
    candidates = []
    root = ctx.tree.getroot()
    kind = localname(root)  # entity-eca | service-eca
    is_entity_eca = kind == "entity-eca"
    file_hash = hashlib.sha256(ctx.artifact.relpath.encode()).hexdigest()[:12]
    for i, eca in enumerate(root):
        if localname(eca) != "eca":
            continue
        eid = uri("eca", file_hash, str(i))
        eca_class = "EntityECA" if is_entity_eca else "ServiceECA"
        eprops = {"eca_class": eca_class, "event": eca.get("event", "")}
        if is_entity_eca:
            eprops["trigger_entity"] = eca.get("entity", "")
            eprops["operation"] = eca.get("operation", "")
        else:
            eprops["trigger_service"] = eca.get("service", "")
        facts.append(make_fact("eca", eid, eprops, base_prov(ctx, eca, METHOD)))

        trigger = eca.get("entity" if is_entity_eca else "service", "")
        if trigger:
            candidates.append(
                {
                    "edge": "triggeredOnEntity" if is_entity_eca else "triggeredOnService",
                    "from": eid,
                    "to_name": trigger,
                    "to_kind": "entity" if is_entity_eca else "service",
                    "via": "eca-trigger",
                    "prov": base_prov(ctx, eca, METHOD),
                }
            )
        for j, child in enumerate(eca):
            ctag = localname(child)
            if ctag == "condition":
                facts.append(
                    make_fact(
                        "condition",
                        uri("eca", file_hash, str(i), "condition", str(j)),
                        {
                            "eca": eid,
                            "field": child.get("field-name", ""),
                            "operator": child.get("operator", ""),
                            "value": child.get("value", ""),
                        },
                        base_prov(ctx, child, METHOD),
                    )
                )
            elif ctag == "action":
                target = child.get("service", "")
                aprops = {
                    "eca": eid,
                    "service": target,
                    "mode": child.get("mode", ""),
                    "persist": child.get("persist", ""),
                    "run_as_user": child.get("run-as-user", ""),
                }
                facts.append(
                    make_fact(
                        "eca_action",
                        uri("eca", file_hash, str(i), "action", str(j)),
                        aprops,
                        base_prov(ctx, child, METHOD),
                    )
                )
                if target:
                    candidates.append(
                        {
                            "edge": "triggersService",
                            "from": eid,
                            "to_name": target,
                            "to_kind": "service",
                            "via": "eca-action",
                            "prov": base_prov(ctx, child, REF_METHOD),
                        }
                    )
    return facts, candidates
