"""Parser: servicedef/services*.xml -> service + param + directive facts.

Direct: service nodes, explicit <attribute>, <override>, <auto-attributes>
directives, <permission-service>, <description>. Candidate (resolve later):
<implements>, <permission-service> target, <group><invoke> targets.
"""
from __future__ import annotations

from ..facts import base_prov, make_fact, snippet_of, uri
from ..provenance import child_text, localname

METHOD = "xml-attribute-read"
REF_METHOD = "xml-literal-reference"


def _text_attr(element, *names):
    vals = {}
    for n in names:
        v = element.get(n)
        if v is not None:
            vals[n] = v
    return vals


def parse(path, ctx):
    facts = []
    candidates = []  # unresolved-tolerant reference records
    root = ctx.tree.getroot()
    for svc in root.iter():
        if localname(svc) != "service":
            continue
        sname = svc.get("name")
        if not sname:
            continue
        sid = uri("service", sname)
        sprov = base_prov(ctx, svc, METHOD)
        props = {"name": sname}
        props.update(
            _text_attr(
                svc,
                "engine",
                "location",
                "invoke",
                "default-entity-name",
                "auth",
                "validate",
                "require-new-transaction",
                "transaction-timeout",
            )
        )
        props["description"] = child_text(svc, "description") or ""
        facts.append(make_fact("service", sid, props, sprov))

        default_entity = svc.get("default-entity-name")
        if default_entity:
            candidates.append(
                {
                    "edge": "operatesOn",
                    "from": sid,
                    "to_name": default_entity,
                    "to_kind": "entity",
                    "via": "default-entity-name",
                    "prov": base_prov(ctx, svc, METHOD),
                }
            )

        seen_params = {}
        for child in svc:
            tag = localname(child)
            if tag == "attribute":
                aname = child.get("name", "")
                key = aname
                n = 1
                while (sname, key) in seen_params:
                    n += 1
                    key = "%s#%d" % (aname, n)
                seen_params[(sname, key)] = True
                pid = uri("service", sname, "param", key)
                paprops = {"name": aname, "role": "service-parameter", "service": sname}
                paprops.update(_text_attr(child, "type", "mode", "optional", "entity-name"))
                paprops["description"] = child_text(child, "description") or ""
                paprops["decl"] = snippet_of(child)  # verbatim declaration for inheritance evidence
                facts.append(make_fact("service_param", pid, paprops, base_prov(ctx, child, METHOD)))
                mode = (child.get("mode") or "").upper()
                if mode in ("IN", "INOUT"):
                    facts.append(
                        make_fact(
                            "edge",
                            uri("edge", "hasInput", sname, key),
                            {"predicate": "hasInput", "from": sid, "to": pid, "via": "attribute-mode"},
                            base_prov(ctx, child, METHOD),
                        )
                    )
                if mode in ("OUT", "INOUT"):
                    facts.append(
                        make_fact(
                            "edge",
                            uri("edge", "hasOutput", sname, key),
                            {"predicate": "hasOutput", "from": sid, "to": pid, "via": "attribute-mode"},
                            base_prov(ctx, child, METHOD),
                        )
                    )
                if not mode:
                    candidates.append(
                        {
                            "edge": "param_mode_absent",
                            "from": sid,
                            "to_name": key,
                            "to_kind": "service_param",
                            "via": "attribute-without-mode",
                            "prov": base_prov(ctx, child, METHOD),
                        }
                    )
            elif tag == "override":
                facts.append(
                    make_fact(
                        "param_override",
                        uri("service", sname, "override", child.get("name", ""), str(child.sourceline or 0)),
                        {"service": sname, "name": child.get("name", ""), **{k: v for k, v in child.attrib.items()}},
                        base_prov(ctx, child, METHOD),
                    )
                )
            elif tag == "auto-attributes":
                entity_ref = child.get("entity-name") or default_entity or ""
                facts.append(
                    make_fact(
                        "auto_attributes",
                        uri("service", sname, "auto", str(child.sourceline or 0)),
                        {
                            "service": sname,
                            "include": child.get("include", ""),
                            "mode": child.get("mode", ""),
                            "optional": child.get("optional", ""),
                            "entity_ref": entity_ref,
                            "decl": snippet_of(child),
                        },
                        base_prov(ctx, child, METHOD),
                    )
                )
            elif tag == "implements":
                target = child.get("service", "")
                if target:
                    candidates.append(
                        {
                            "edge": "referencesService",
                            "from": sid,
                            "to_name": target,
                            "to_kind": "service",
                            "via": "implements",
                            "prov": base_prov(ctx, child, REF_METHOD),
                            "inherit": True,
                            "inherit_el": child,
                        }
                    )
            elif tag == "permission-service":
                target = child.get("service-name", "")
                facts.append(
                    make_fact(
                        "permission_check",
                        uri("service", sname, "permission", str(child.sourceline or 0)),
                        {"service": sname, "service_name": target, "main_action": child.get("main-action", "")},
                        base_prov(ctx, child, METHOD),
                    )
                )
                if target:
                    candidates.append(
                        {
                            "edge": "referencesService",
                            "from": sid,
                            "to_name": target,
                            "to_kind": "service",
                            "via": "permission-service",
                            "prov": base_prov(ctx, child, REF_METHOD),
                        }
                    )
            elif tag == "group":
                for inv in child:
                    if localname(inv) == "invoke" and inv.get("name"):
                        candidates.append(
                            {
                                "edge": "referencesService",
                                "from": sid,
                                "to_name": inv.get("name"),
                                "to_kind": "service",
                                "via": "group-invoke",
                                "prov": base_prov(ctx, inv, REF_METHOD),
                            }
                        )
    return facts, candidates
