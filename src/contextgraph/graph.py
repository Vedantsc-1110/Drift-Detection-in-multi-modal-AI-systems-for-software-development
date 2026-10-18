"""Facts -> RDF/Turtle builder using ontology/context-ontology.ttl (v0.4).

Dependency-free hand-rolled writer (deterministic output); tests validate
with rdflib. Stable IDs: every URI derives from repository/module/path/name
or file-hash + document order. No timestamps in identifiers (use --as-of for
byte-reproducible builds).

Coverage: all ontology-mapped concepts. Auxiliary facts (resource bindings,
param overrides, auto-attributes directives, permission checks, view members /
view links, ECA action nodes) stay in facts.jsonl; see docs/rdf-graph.md.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from . import EXTRACTOR_NAME, EXTRACTOR_VERSION, NAMESPACE

NB = NAMESPACE
OFBIZ = "ofbiz:"
RDF_TYPE = "a"

METHOD_ENGINES = {"java", "groovy", "simple"}


def _method_uri(location: str, invoke: str) -> str:
    # Keep URIs readable: locations are dotted class names or component:// paths
    # (all URI-legal characters); encode anything else.
    return NB + "method/%s#%s" % (quote(location, safe="/:."), quote(invoke, safe=""))

EDGE_WHITELIST = {
    "hasInput",
    "hasOutput",
    "referencesService",
    "triggersService",
    "triggeredOnEntity",
    "triggeredOnService",
    "operatesOn",
    "relationTo",
}

SKIP_NODE_KINDS = {
    "resource",
    "resource_loader",
    "param_override",
    "auto_attributes",
    "permission_check",
    "view_member",
    "view_link",
    "eca_action",
}


def _esc(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _u(uri: str) -> str:
    return "<%s>" % uri


def _lit(text: str) -> str:
    return '"%s"' % _esc(text)


def _int(n) -> str:
    return '"%d"^^xsd:integer' % int(n)


def _bool(b) -> str:
    return '"%s"^^xsd:boolean' % ("true" if b else "false")


class Graph:
    def __init__(self):
        self.triples = set()
        self.emitted_nodes = set()

    def add(self, s, p, o):
        self.triples.add((s, p, o))

    def uri_node(self, uri, rdf_class, prov, artifact_of, extraction_of, extra=()):
        """Type + provenance triples shared by every emitted individual.

        Source-level duplicate definitions (same URI, e.g. a service defined
        twice in one file) merge into one node: first occurrence wins, extra
        defining files are cited via hasSourceArtifact.
        """
        s = _u(uri)
        if uri in self.emitted_nodes:
            self.add(s, OFBIZ + "hasSourceArtifact", _u(artifact_of(prov["file"])))
            return
        self.emitted_nodes.add(uri)
        self.add(s, RDF_TYPE, OFBIZ + rdf_class)
        art = artifact_of(prov["file"])
        self.add(s, OFBIZ + "definedIn", _u(art))
        self.add(s, OFBIZ + "extractionType", _lit(prov["extraction_type"]))
        self.add(s, OFBIZ + "generatedBy", _u(extraction_of(prov["method"], prov["file"])))
        if prov.get("line") is not None:
            self.add(s, OFBIZ + "evidenceLine", _int(prov["line"]))
        if prov.get("xpath"):
            self.add(s, OFBIZ + "sourceXPath", _lit(prov["xpath"]))
        for p, o in extra:
            self.add(s, p, o)
        for i, ev in enumerate(prov.get("evidence") or []):
            evid = "%s/evidence/%d" % (uri, i)
            self.add(s, OFBIZ + "hasEvidence", _u(evid))
            self.add(_u(evid), RDF_TYPE, OFBIZ + "Evidence")
            self.add(_u(evid), OFBIZ + "quotedFrom", _u(artifact_of(ev["file"])))
            line = ev.get("line") or 0
            self.add(_u(evid), OFBIZ + "lineStart", _int(line))
            self.add(_u(evid), OFBIZ + "lineEnd", _int(line))
            if ev.get("xpath"):
                self.add(_u(evid), OFBIZ + "sourceXPath", _lit(ev["xpath"]))
            if ev.get("snippet"):
                self.add(_u(evid), OFBIZ + "snippet", _lit(ev["snippet"]))


def _opt_lit(value):
    return _lit(value) if value else None


def build(facts_path, manifest_path, out_path, as_of=None, repo_path=""):
    facts_path, manifest_path, out_path = Path(facts_path), Path(manifest_path), Path(out_path)
    facts = [json.loads(line) for line in facts_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    facts.sort(key=lambda f: (f["kind"], f["id"]))

    repo_id = manifest.get("repository", "unknown")
    repo_uri = NB + "repo/" + quote(repo_id, safe="")
    extractor_uri = NB + "extraction/" + EXTRACTOR_NAME + "/" + EXTRACTOR_VERSION

    artifacts = {}  # relpath -> uri
    for f in manifest.get("files", []):
        artifacts[f["relpath"]] = NB + "source/" + f["relpath"]

    def artifact_of(relpath):
        return artifacts.get(relpath, NB + "source/" + relpath)

    used_by_method = {}
    for fact in facts:
        used_by_method.setdefault(fact["prov"].get("method", ""), set()).add(fact["prov"]["file"])

    def extraction_of(method, _file):
        slug = quote(method or "unknown", safe="")
        return NB + "extraction/%s/%s" % (EXTRACTOR_VERSION, slug)

    g = Graph()

    # --- provenance scaffolding ---
    g.add(_u(repo_uri), RDF_TYPE, OFBIZ + "Repository")
    g.add(_u(repo_uri), OFBIZ + "repositoryId", _lit(repo_id))
    if repo_path:
        g.add(_u(repo_uri), OFBIZ + "repositoryPath", _lit(repo_path))
    g.add(_u(extractor_uri), RDF_TYPE, OFBIZ + "Extractor")
    g.add(_u(extractor_uri), OFBIZ + "extractorName", _lit(EXTRACTOR_NAME))
    g.add(_u(extractor_uri), OFBIZ + "extractorVersion", _lit(EXTRACTOR_VERSION))
    extracted_at = as_of or manifest.get("extracted_at", "")
    for method in sorted(used_by_method):
        ex = extraction_of(method, None)
        g.add(_u(ex), RDF_TYPE, OFBIZ + "Extraction")
        if extracted_at:
            g.add(_u(ex), OFBIZ + "extractedAt", '"%s"^^xsd:dateTime' % extracted_at)
        g.add(_u(ex), OFBIZ + "extractionMethod", _lit(method))
        g.add(_u(ex), "prov:wasAssociatedWith", _u(extractor_uri))
        for rel in sorted(used_by_method[method]):
            g.add(_u(ex), "prov:used", _u(artifact_of(rel)))
    for f in manifest.get("files", []):
        a = _u(artifact_of(f["relpath"]))
        g.add(a, RDF_TYPE, OFBIZ + "SourceArtifact")
        g.add(a, OFBIZ + "filePath", _lit(f["relpath"]))
        g.add(a, OFBIZ + "sha256", _lit(f.get("sha256", "")))
        g.add(a, OFBIZ + "artifactType", _lit(f.get("artifact_type", "")))
        g.add(a, OFBIZ + "fromRepository", _u(repo_uri))

    # ECA action lookup for statement-level mode: (file, line) -> action props.
    action_by_site = {}
    for fact in facts:
        if fact["kind"] == "eca_action":
            action_by_site[(fact["prov"]["file"], fact["prov"].get("line"))] = fact["props"]

    # --- nodes ---
    methods = {}  # method uri -> (service prov for provenance)
    for fact in facts:
        kind, fid, props, prov = fact["kind"], fact["id"], fact["props"], fact["prov"]
        if kind == "component":
            g.uri_node(fid, "Component", prov, artifact_of, extraction_of, [(OFBIZ + "name", _lit(props["name"]))])
        elif kind == "service":
            extra = [(OFBIZ + "name", _lit(props["name"]))]
            if props.get("engine"):
                extra.append((OFBIZ + "engine", _lit(props["engine"])))
            if props.get("location"):
                extra.append((OFBIZ + "implLocation", _lit(props["location"])))
            if props.get("invoke"):
                extra.append((OFBIZ + "implInvoke", _lit(props["invoke"])))
            if props.get("description"):
                extra.append((OFBIZ + "description", _lit(props["description"])))
            if props.get("default-entity-name"):
                extra.append((OFBIZ + "defaultEntityName", _lit(props["default-entity-name"])))
            g.uri_node(fid, "Service", prov, artifact_of, extraction_of, extra)
            if props.get("engine") in METHOD_ENGINES and props.get("location") and props.get("invoke"):
                mid = _method_uri(props["location"], props["invoke"])
                methods.setdefault(mid, (props["invoke"], prov))
        elif kind == "service_param":
            extra = [(OFBIZ + "name", _lit(props["name"])), (OFBIZ + "role", _lit("service-parameter"))]
            if props.get("type"):
                extra.append((OFBIZ + "attrType", _lit(props["type"])))
            if props.get("mode"):
                extra.append((OFBIZ + "paramMode", _lit(props["mode"])))
            if props.get("optional"):
                extra.append((OFBIZ + "optional", _lit(props["optional"])))
            g.uri_node(fid, "Attribute", prov, artifact_of, extraction_of, extra)
        elif kind == "entity":
            extra = [(OFBIZ + "name", _lit(props["name"]))]
            if props.get("description"):
                extra.append((OFBIZ + "description", _lit(props["description"])))
            g.uri_node(fid, "Entity", prov, artifact_of, extraction_of, extra)
        elif kind == "view_entity":
            g.uri_node(
                fid, "ViewEntity", prov, artifact_of, extraction_of, [(OFBIZ + "name", _lit(props["name"]))]
            )
        elif kind == "entity_field":
            extra = [
                (OFBIZ + "name", _lit(props["name"])),
                (OFBIZ + "role", _lit("entity-field")),
                (OFBIZ + "isPrimaryKey", _bool(props.get("is_primary_key", False))),
            ]
            if props.get("type"):
                extra.append((OFBIZ + "attrType", _lit(props["type"])))
            g.uri_node(fid, "Attribute", prov, artifact_of, extraction_of, extra)
            g.add(_u(NB + "entity/" + props["entity"]), OFBIZ + "hasAttribute", _u(fid))
        elif kind == "view_alias":
            extra = [(OFBIZ + "name", _lit(props["name"])), (OFBIZ + "role", _lit("view-alias"))]
            g.uri_node(fid, "Attribute", prov, artifact_of, extraction_of, extra)
            g.add(_u(NB + "entity/" + props["view"]), OFBIZ + "hasAttribute", _u(fid))
        elif kind == "eca":
            cls = "EntityECA" if props.get("eca_class") == "EntityECA" else "ServiceECA"
            extra = []
            if props.get("event"):
                extra.append((OFBIZ + "ecaEvent", _lit(props["event"])))
            if props.get("operation"):
                extra.append((OFBIZ + "ecaOperation", _lit(props["operation"])))
            if props.get("trigger_entity"):
                extra.append((OFBIZ + "triggerEntityName", _lit(props["trigger_entity"])))
            if props.get("trigger_service"):
                extra.append((OFBIZ + "triggerServiceName", _lit(props["trigger_service"])))
            g.uri_node(fid, cls, prov, artifact_of, extraction_of, extra)
        elif kind == "condition":
            extra = []
            if props.get("field"):
                extra.append((OFBIZ + "condField", _lit(props["field"])))
            if props.get("operator"):
                extra.append((OFBIZ + "condOperator", _lit(props["operator"])))
            if props.get("value"):
                extra.append((OFBIZ + "condValue", _lit(props["value"])))
            g.uri_node(fid, "Condition", prov, artifact_of, extraction_of, extra)
            g.add(_u(props["eca"]), OFBIZ + "hasCondition", _u(fid))
        elif kind == "relation":
            extra = []
            if props.get("type"):
                extra.append((OFBIZ + "relationType", _lit(props["type"])))
            if props.get("fk_name"):
                extra.append((OFBIZ + "fkName", _lit(props["fk_name"])))
            for km in props.get("key_maps", []):
                rel = km.get("rel_field_name") or ""
                extra.append((OFBIZ + "keyMap", _lit("%s->%s" % (km.get("field_name", ""), rel))))
            g.uri_node(fid, "Relation", prov, artifact_of, extraction_of, extra)
            g.add(_u(fid), OFBIZ + "relationFrom", _u(NB + "entity/" + props["subject"]))
        elif kind in SKIP_NODE_KINDS:
            continue
        elif kind == "edge":
            continue  # second pass below
        else:
            continue

    # --- synthesized Method nodes + implementedBy ---
    for mid in sorted(methods):
        invoke, prov = methods[mid]
        g.uri_node(mid, "Method", prov, artifact_of, extraction_of, [(OFBIZ + "name", _lit(invoke))])
    for fact in facts:
        if fact["kind"] != "service":
            continue
        props = fact["props"]
        if props.get("engine") in METHOD_ENGINES and props.get("location") and props.get("invoke"):
            mid = _method_uri(props["location"], props["invoke"])
            g.add(_u(fact["id"]), OFBIZ + "implementedBy", _u(mid))

    # --- component membership (owner = owning component per source path; dependency
    # files attribute to their own component, e.g. datamodel) ---
    def _owner_of(relpath):
        parts = relpath.split("/")
        if len(parts) > 1 and parts[0] == "applications":
            return parts[1]
        return manifest.get("component", "")

    comp_uri = NB + "component/" + manifest.get("component", "")
    for fact in facts:
        if fact["kind"] == "service":
            g.add(_u(comp_uri), OFBIZ + "containsService", _u(fact["id"]))
            g.add(_u(fact["id"]), OFBIZ + "belongsToComponent", _u(comp_uri))
        elif fact["kind"] in ("entity", "view_entity"):
            owner_uri = NB + "component/" + _owner_of(fact["prov"]["file"])
            g.add(_u(owner_uri), OFBIZ + "containsEntity", _u(fact["id"]))
            g.add(_u(fact["id"]), OFBIZ + "belongsToComponent", _u(owner_uri))

    # --- edges with reified statements ---
    edge_facts = sorted(
        [f for f in facts if f["kind"] == "edge" and f["props"].get("predicate") in EDGE_WHITELIST],
        key=lambda f: (f["props"]["predicate"], f["props"]["from"], f["props"]["to"]),
    )
    for i, ef in enumerate(edge_facts):
        pred, s, o = ef["props"]["predicate"], ef["props"]["from"], ef["props"]["to"]
        prov = ef["prov"]
        g.add(_u(s), OFBIZ + pred, _u(o))
        stmt = NB + "statement/%d" % i
        g.add(_u(stmt), RDF_TYPE, "rdf:Statement")
        g.add(_u(stmt), "rdf:subject", _u(s))
        g.add(_u(stmt), "rdf:predicate", _u(NB + pred))
        g.add(_u(stmt), "rdf:object", _u(o))
        g.add(_u(stmt), OFBIZ + "definedIn", _u(artifact_of(prov["file"])))
        g.add(_u(stmt), OFBIZ + "extractionType", _lit(prov["extraction_type"]))
        if prov.get("line") is not None:
            g.add(_u(stmt), OFBIZ + "evidenceLine", _int(prov["line"]))
        if pred == "triggersService":
            action = action_by_site.get((prov["file"], prov.get("line")))
            if action and action.get("mode"):
                g.add(_u(stmt), OFBIZ + "actionMode", _lit(action["mode"]))
        if pred in ("triggeredOnEntity", "triggeredOnService"):
            g.add(_u(s), OFBIZ + "appliesTo", _u(o))

    # --- serialize ---
    header = [
        "# Context Graph (deterministic, ontology v0.4).",
        "# Generator: %s %s; repository: %s; component: %s." % (EXTRACTOR_NAME, "rdfgen-0.1.0", repo_id, manifest.get("component", "")),
        "# Source facts sha256: %s." % _sha_file(facts_path),
        "# extractedAt: %s." % (as_of or manifest.get("extracted_at", "")),
    ]
    prefixes = [
        "@prefix ofbiz: <%s> ." % NB,
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "",
    ]
    lines = header + prefixes
    for s, p, o in sorted(g.triples):
        lines.append("%s %s %s ." % (s, p, o))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"triples": len(g.triples), "path": str(out_path)}


def _sha_file(path: Path) -> str:
    import hashlib as _hl

    h = _hl.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
