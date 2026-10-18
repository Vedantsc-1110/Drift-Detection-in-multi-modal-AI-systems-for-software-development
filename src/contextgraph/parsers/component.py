"""Parser: ofbiz-component.xml -> component, resource, webapp facts (all direct)."""
from __future__ import annotations

from ..facts import base_prov, make_fact, uri
from ..provenance import child_text, localname

METHOD = "xml-attribute-read"


def parse(path, ctx):
    facts = []
    root = ctx.tree.getroot()
    name = root.get("name", ctx.component_name)
    comp_id = uri("component", name)
    prov = base_prov(ctx, root, METHOD)
    facts.append(
        make_fact(
            "component",
            comp_id,
            {
                "name": name,
                "location": ctx.component_name,  # component directory name
                "description": child_text(root, "description") or "",
            },
            prov,
        )
    )
    for i, child in enumerate(root):
        tag = localname(child)
        if tag == "resource-loader":
            facts.append(
                make_fact(
                    "resource_loader",
                    uri("component", name, "loader", child.get("name", str(i))),
                    {"name": child.get("name", ""), "type": child.get("type", "")},
                    base_prov(ctx, child, METHOD),
                )
            )
        elif tag in ("entity-resource", "service-resource", "test-suite", "testsuite"):
            kind = "entity" if tag == "entity-resource" else ("service" if tag == "service-resource" else "test")
            facts.append(
                make_fact(
                    "resource",
                    uri("component", name, "resource", str(i)),
                    {
                        "kind": kind,
                        "type": child.get("type", ""),
                        "reader": child.get("reader-name", ""),
                        "loader": child.get("loader", ""),
                        "location": child.get("location", ""),
                    },
                    base_prov(ctx, child, METHOD),
                )
            )
        elif tag == "webapp":
            wname = child.get("name", str(i))
            facts.append(
                make_fact(
                    "webapp",
                    uri("component", name, "webapp", wname),
                    {
                        "name": wname,
                        "title": child.get("title", ""),
                        "mount_point": child.get("mount-point", ""),
                        "location": child.get("location", ""),
                        "base_permission": child.get("base-permission", ""),
                    },
                    base_prov(ctx, child, METHOD),
                )
            )
    return facts, []
