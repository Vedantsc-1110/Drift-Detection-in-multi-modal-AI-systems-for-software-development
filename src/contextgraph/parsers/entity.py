"""Parser: entitydef/*.xml -> entity / view-entity / field / relation facts.

Handles both <entity> (base) and <view-entity> (member-entity, alias,
view-link). All structural facts are direct; cross-entity name references
(member entities, rel-entity-name) are candidates resolved by the pipeline.
"""
from __future__ import annotations

from ..facts import base_prov, make_fact, snippet_of, uri
from ..provenance import child_text, localname

METHOD = "xml-attribute-read"


def _key_maps(element):
    out = []
    for km in element:
        if localname(km) == "key-map":
            out.append(
                {
                    "field_name": km.get("field-name", ""),
                    "rel_field_name": km.get("rel-field-name", ""),
                }
            )
    return out


def parse(path, ctx):
    facts = []
    candidates = []
    root = ctx.tree.getroot()
    for ent in root:
        tag = localname(ent)
        if tag == "entity":
            ename = ent.get("entity-name", "")
            if not ename:
                continue
            eid = uri("entity", ename)
            facts.append(
                make_fact(
                    "entity",
                    eid,
                    {
                        "name": ename,
                        "package": ent.get("package-name", ""),
                        "title": ent.get("title", ""),
                        "description": child_text(ent, "description") or "",
                    },
                    base_prov(ctx, ent, METHOD),
                )
            )
            pk_fields = set()
            for pk in ent:
                if localname(pk) == "prim-key" and pk.get("field"):
                    pk_fields.add(pk.get("field"))
            for child in ent:
                ctag = localname(child)
                if ctag == "field":
                    fname = child.get("name", "")
                    facts.append(
                        make_fact(
                            "entity_field",
                            uri("entity", ename, "field", fname),
                            {
                                "entity": ename,
                                "name": fname,
                                "role": "entity-field",
                                "type": child.get("type", ""),
                                "is_primary_key": fname in pk_fields,
                                "description": child_text(child, "description") or "",
                                "decl": snippet_of(child),
                            },
                            base_prov(ctx, child, METHOD),
                        )
                    )
                elif ctag == "relation":
                    rel = _parse_relation(ctx, ent, ename, child, is_view=False)
                    facts.append(rel["fact"])
                    if rel["target"]:
                        candidates.append(rel["candidate"])
        elif tag == "view-entity":
            ename = ent.get("entity-name", "")
            if not ename:
                continue
            eid = uri("entity", ename)
            facts.append(
                make_fact(
                    "view_entity",
                    eid,
                    {
                        "name": ename,
                        "package": ent.get("package-name", ""),
                        "title": ent.get("title", ""),
                        "description": child_text(ent, "description") or "",
                    },
                    base_prov(ctx, ent, METHOD),
                )
            )
            for child in ent:
                ctag = localname(child)
                if ctag == "member-entity":
                    alias = child.get("entity-alias", "")
                    target = child.get("entity-name", "")
                    facts.append(
                        make_fact(
                            "view_member",
                            uri("entity", ename, "member", alias or target),
                            {"view": ename, "alias": alias, "entity_ref": target},
                            base_prov(ctx, child, METHOD),
                        )
                    )
                    if target:
                        candidates.append(
                            {
                                "edge": "viewMemberEntity",
                                "from": eid,
                                "to_name": target,
                                "to_kind": "entity",
                                "via": "member-entity",
                                "prov": base_prov(ctx, child, METHOD),
                            }
                        )
                elif ctag == "alias":
                    facts.append(
                        make_fact(
                            "view_alias",
                            uri("entity", ename, "alias", child.get("name", "")),
                            {
                                "view": ename,
                                "name": child.get("name", ""),
                                "role": "view-alias",
                                "entity_alias": child.get("entity-alias", ""),
                                "field": child.get("field", ""),
                                "description": child_text(child, "description") or "",
                            },
                            base_prov(ctx, child, METHOD),
                        )
                    )
                elif ctag == "view-link":
                    facts.append(
                        make_fact(
                            "view_link",
                            uri("entity", ename, "viewlink", str(child.sourceline or 0)),
                            {
                                "view": ename,
                                "entity_alias": child.get("entity-alias", ""),
                                "rel_entity_alias": child.get("rel-entity-alias", ""),
                                "key_maps": _key_maps(child),
                            },
                            base_prov(ctx, child, METHOD),
                        )
                    )
                elif ctag == "relation":
                    rel = _parse_relation(ctx, ent, ename, child, is_view=True)
                    facts.append(rel["fact"])
                    if rel["target"]:
                        candidates.append(rel["candidate"])
        elif tag == "extend-entity":
            ename = ent.get("entity-name", "")
            facts.append(
                make_fact(
                    "extend_entity",
                    uri("entity", ename, "extend", str(ent.sourceline or 0)),
                    {"name": ename, "package": ent.get("package-name", "")},
                    base_prov(ctx, ent, METHOD),
                )
            )
    return facts, candidates


def _parse_relation(ctx, ent, ename, child, is_view):
    target = child.get("rel-entity-name", "")
    rid = uri("entity", ename, "relation", str(child.sourceline or 0))
    fact = make_fact(
        "relation",
        rid,
        {
            "subject": ename,
            "rel_entity_name": target,
            "type": child.get("type", ""),
            "fk_name": child.get("fk-name", ""),
            "title": child.get("title", ""),
            "key_maps": _key_maps(child),
            "description": child_text(child, "description") or "",
        },
        base_prov(ctx, child, METHOD),
    )
    candidate = None
    if target:
        candidate = {
            "edge": "relationTo",
            "from": rid,
            "from_kind": "relation",
            "to_name": target,
            "to_kind": "entity",
            "via": "relation",
            "prov": base_prov(ctx, child, METHOD),
        }
    return {"fact": fact, "target": target, "candidate": candidate}
