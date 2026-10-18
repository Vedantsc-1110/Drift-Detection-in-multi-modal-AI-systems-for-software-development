"""RDF triple builder: fact dicts -> CONTRACT-style rdflib Graph (PART1_PLAN Task 1.7).

Companion to (not a replacement for) ``graph.py``: graph.py serves the
existing ofbiz:-namespace pipeline with its locked metrics; this module
emits the shared-contract shape (proposal §7.2 1.4, CONTRACT.md §1–§6):

- Namespaces: ctx: <http://context.example.org/>, prov:, rdfs:.
- Every subject: rdf:type, rdfs:label, domain properties, ctx:definedIn,
  ctx:atLine, prov:hadPrimarySource, prov:wasGeneratedBy, ctx:sourceLocation,
  ctx:sourceHash, ctx:confidence 1.0, ctx:factType "deterministic".
- Timestamps use prov:generatedAtTime (PROV-O). prov:atTime is never emitted.
- Subject URIs are minted deterministically from kind + key properties.

Extractor labels (plan-fixed set):
  xml-attribute-read / xml-literal-reference -> ctx:XmlEtreeExtractor
  tree-sitter-java                          -> ctx:TreeSitterExtractor
  python-ast                                -> ctx:PythonAstExtractor
  yaml-read                                 -> ctx:YamlExtractor
  gradle-dependency-read                    -> ctx:XmlEtreeExtractor
      # Plan gap, documented: the gradle reader is stdlib-regex, but the plan
      # restricts wasGeneratedBy to the four names above; gradle facts join
      # the OFBiz-structural family. Flagged for contract review (Task 1.10).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS, XSD

from . import EXTRACTOR_NAME, EXTRACTOR_VERSION  # noqa: F401  (audit trail only)

CTX = Namespace("http://context.example.org/")

EXTRACTOR_BY_METHOD = {
    "xml-attribute-read": CTX.XmlEtreeExtractor,
    "xml-literal-reference": CTX.XmlEtreeExtractor,
    "tree-sitter-java": CTX.TreeSitterExtractor,
    "python-ast": CTX.PythonAstExtractor,
    "yaml-read": CTX.YamlExtractor,
    "gradle-dependency-read": CTX.XmlEtreeExtractor,
}

GRAPH_AIRFLOW = "urn:airflow"
GRAPH_CICD = "urn:cicd"


def _slug(text: str) -> str:
    return quote(str(text), safe="-_.")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def file_uri(relpath: str) -> URIRef:
    return URIRef("file:///" + relpath)


def subject_for(kind: str, props: dict, fact_id: str = "", relpath: str = "") -> URIRef:
    """Deterministic ctx: subject URI per fact kind.

    ECA-family and relation subjects fold in file identity (ECA internal-id
    tail carries a relpath hash + document index; relations add the file
    stem) so identical triggers in different files never share a subject.
    """
    if kind == "service":
        return CTX["Service/" + _slug(props.get("name", ""))]
    if kind == "service_param":
        return CTX["ServiceParam/" + _slug(props.get("service", "") or "") + "/" + _slug(props.get("name", ""))]
    if kind == "entity":
        return CTX["Entity/" + _slug(props.get("name", ""))]
    if kind == "view_entity":
        return CTX["ViewEntity/" + _slug(props.get("name", ""))]
    if kind == "entity_field":
        return CTX["Field/" + _slug(props.get("entity", "")) + "/" + _slug(props.get("name", ""))]
    if kind == "relation":
        file_slug = _slug(Path(relpath).stem) if relpath else "nofile"
        return CTX["Relation/" + _slug(props.get("subject", "")) + "/" + _slug(props.get("rel_entity_name", "")) + "/" + file_slug]
    if kind == "eca":
        tail = fact_id.rsplit("/", 2)[-2:]
        return CTX["ECA/" + _slug(tail[0] if len(tail) == 2 else "") + "/" + _slug(tail[-1] if tail else "")]
    if kind == "condition":
        tail = (props.get("eca", "")).rsplit("/", 2)[-2:]
        return CTX["Condition/" + _slug(tail[0] if len(tail) == 2 else "") + "/" + _slug(tail[-1] if tail else "") + "/" + _slug(props.get("field", ""))]
    if kind == "eca_action":
        tail = (props.get("eca", "")).rsplit("/", 2)[-2:]
        return CTX["ECAAction/" + _slug(tail[0] if len(tail) == 2 else "") + "/" + _slug(tail[-1] if tail else "") + "/" + _slug(props.get("service", ""))]
    if kind == "route":
        return CTX["Route/" + _slug(props.get("component", "")) + "/" + _slug(props.get("uri", ""))]
    if kind == "module_dependency":
        return CTX["ModuleDependency/" + _slug(props.get("module", "")) + "/" + _slug(props.get("depends_on", ""))]
    if kind == "java_class":
        return CTX["JavaClass/" + _slug(Path(relpath).stem if relpath else "nofile") + "/" + _slug(props.get("name", ""))]
    if kind == "java_method":
        return CTX["JavaMethod/" + _slug(Path(relpath).stem if relpath else "nofile") + "/" + _slug(props.get("class", "")) + "/" + _slug(props.get("name", ""))]
    if kind == "java_import":
        return CTX["Import/" + _slug(Path(relpath).stem if relpath else "nofile") + "/" + _slug(props.get("import", ""))]
    if kind == "java_call":
        return CTX["Call/" + _slug(Path(relpath).stem if relpath else "nofile") + "/" + _slug(props.get("caller_method", "")) + "/" + _slug(props.get("callee", ""))]
    if kind == "airflow_dag":
        return CTX["DAG/" + _slug(props.get("dag_id", ""))]
    if kind == "airflow_task":
        return CTX["Task/" + _slug(props.get("dag", "")) + "/" + _slug(props.get("task_id", ""))]
    if kind == "cicd_workflow":
        return CTX["Workflow/" + _slug(props.get("name", ""))]
    if kind == "cicd_job":
        return CTX["Job/" + _slug(props.get("workflow", "")) + "/" + _slug(props.get("job_id", ""))]
    if kind == "cicd_step":
        return CTX["Step/" + _slug(props.get("workflow", "")) + "/" + _slug(props.get("job", "")) + "/" + _slug(props.get("name", ""))]
    if kind == "edge":
        return CTX["Edge/" + _slug(props.get("predicate", "")) + "/" + _slug(props.get("from", "").rsplit("/", 1)[-1]) + "/" + _slug(props.get("to", "").rsplit("/", 1)[-1])]
    return CTX["Fact/" + _slug(props.get("name", kind))]


CLASS_BY_KIND = {
    "service": CTX.Service,
    "service_param": CTX.ServiceParam,
    "entity": CTX.Entity,
    "view_entity": CTX.ViewEntity,
    "entity_field": CTX.Field,
    "relation": CTX.Relation,
    "eca": CTX.ECA,
    "condition": CTX.Condition,
    "eca_action": CTX.ECAAction,
    "route": CTX.Route,
    "module_dependency": CTX.ModuleDependency,
    "java_class": CTX.JavaClass,
    "java_method": CTX.JavaMethod,
    "java_import": CTX.Import,
    "java_call": CTX.Call,
    "airflow_dag": CTX.DAG,
    "airflow_task": CTX.Task,
    "cicd_workflow": CTX.Workflow,
    "cicd_job": CTX.Job,
    "cicd_step": CTX.Step,
}

# kinds whose subjects are reified statements, not domain individuals
SKIP_SUBJECT_KINDS = {"edge", "permission_check", "param_override", "auto_attributes", "view_member", "view_link"}


def _label(kind: str, props: dict) -> str:
    for key in ("name", "dag_id", "task_id", "job_id", "uri", "import", "callee"):
        if props.get(key):
            return str(props[key])
    return kind


def build_graph(facts: list, repo_root, generated_at: str = "") -> Graph:
    """Map fact dicts to a CONTRACT-style rdflib Graph (deterministic).

    Pass 1 mints a subject per domain fact with full provenance. Pass 2
    attaches edge triples between minted subjects (mirroring the §7.2 1.1
    example: hasInputParam lives on the Service subject). Edge endpoints
    without a minted subject (out-of-scope references) become Literals —
    reported, never invented as nodes.
    """
    repo_root = Path(repo_root)
    graph = Graph()
    graph.bind("ctx", CTX)
    graph.bind("prov", PROV)
    hashes: dict[str, str] = {}

    def source_hash(relpath: str) -> str:
        if relpath not in hashes:
            candidate = repo_root / relpath
            hashes[relpath] = sha256_file(candidate) if candidate.is_file() else ""
        return hashes[relpath]

    id_to_subject: dict[str, URIRef] = {}
    for fact in sorted(facts, key=lambda f: (f["kind"], f["id"])):
        kind, props, prov = fact["kind"], fact["props"], fact["prov"]
        if kind == "edge" or kind in SKIP_SUBJECT_KINDS:
            continue
        relpath = prov.get("file", "")
        subject = subject_for(kind, props, fact["id"], relpath)
        id_to_subject[fact["id"]] = subject
        line = prov.get("line") or 0
        extractor = EXTRACTOR_BY_METHOD.get(prov.get("method", ""), CTX.XmlEtreeExtractor)
        graph.add((subject, RDF.type, CLASS_BY_KIND.get(kind, CTX.Fact)))
        graph.add((subject, RDFS.label, Literal(_label(kind, props))))
        _add_domain(graph, kind, subject, props)
        graph.add((subject, CTX.definedIn, file_uri(relpath)))
        graph.add((subject, CTX.atLine, Literal(int(line), datatype=XSD.integer)))
        graph.add((subject, PROV.hadPrimarySource, file_uri(relpath)))
        graph.add((subject, PROV.wasGeneratedBy, extractor))
        graph.add((subject, CTX.sourceLocation, Literal("%s:%d" % (relpath, line))))
        graph.add((subject, CTX.sourceHash, Literal(source_hash(relpath))))
        graph.add((subject, CTX.confidence, Literal(1.0, datatype=XSD.double)))
        graph.add((subject, CTX.factType, Literal("deterministic")))
        if generated_at:
            graph.add((subject, PROV.generatedAtTime, Literal(generated_at, datatype=XSD.dateTime)))

    for fact in sorted(facts, key=lambda f: f["id"]):
        if fact["kind"] != "edge":
            continue
        _add_edge(graph, fact["props"], id_to_subject)
    return graph


_EDGE_PREDICATES = {
    "hasInput": CTX.hasInputParam,
    "hasOutput": CTX.hasOutputParam,
    "dependsOn": CTX.dependsOn,
    "triggeredBy": CTX.triggeredBy,
    "hasStep": CTX.hasStep,
    "usesAction": CTX.usesAction,
    "referencesService": CTX.referencesService,
    "triggersService": CTX.triggersService,
    "triggeredOnEntity": CTX.triggeredOnEntity,
    "triggeredOnService": CTX.triggeredOnService,
    "operatesOn": CTX.operatesOn,
    "relationTo": CTX.relationTo,
}


def _add_domain(graph: Graph, kind: str, subject: URIRef, props: dict) -> None:
    """Domain properties per kind (mirrors the §7.2 1.1 example shape)."""
    if kind == "service":
        if props.get("engine"):
            graph.add((subject, CTX.engine, Literal(props["engine"])))
        if props.get("location") and props.get("invoke"):
            graph.add(
                (
                    subject,
                    CTX.implementedBy,
                    CTX["Method/" + _slug(props["location"]) + "#" + _slug(props["invoke"])],
                )
            )
        if props.get("description"):
            graph.add((subject, RDFS.comment, Literal(props["description"])))
    elif kind == "service_param":
        if props.get("type"):
            graph.add((subject, CTX.paramType, Literal(props["type"])))
        if props.get("mode"):
            graph.add((subject, CTX.mode, Literal(props["mode"])))
    elif kind == "entity_field":
        if props.get("type"):
            graph.add((subject, CTX.fieldType, Literal(props["type"])))
        graph.add((subject, CTX.isPrimaryKey, Literal(bool(props.get("is_primary_key", False)), datatype=XSD.boolean)))
    elif kind == "relation":
        if props.get("type"):
            graph.add((subject, CTX.relationType, Literal(props["type"])))
        if props.get("rel_entity_name"):
            graph.add((subject, CTX.relatesTo, CTX["Entity/" + _slug(props["rel_entity_name"])]))
        for km in props.get("key_maps", []):
            graph.add(
                (
                    subject,
                    CTX.keyMap,
                    Literal("%s->%s" % (km.get("field_name", ""), km.get("rel_field_name", ""))),
                )
            )
    elif kind == "eca":
        for key, pred in (("trigger_entity", CTX.triggerEntity), ("trigger_service", CTX.triggerService),
                          ("operation", CTX.operation), ("event", CTX.event)):
            if props.get(key):
                graph.add((subject, pred, Literal(props[key])))
    elif kind == "condition":
        for key, pred in (("field", CTX.condField), ("operator", CTX.condOperator), ("value", CTX.condValue)):
            if props.get(key):
                graph.add((subject, pred, Literal(props[key])))
    elif kind == "eca_action":
        if props.get("service"):
            graph.add((subject, CTX.callsService, CTX["Service/" + _slug(props["service"])]))
        if props.get("mode"):
            graph.add((subject, CTX.mode, Literal(props["mode"])))
    elif kind == "route":
        if props.get("uri"):
            graph.add((subject, CTX.uri, Literal(props["uri"])))
        if props.get("event_type"):
            graph.add((subject, CTX.eventType, Literal(props["event_type"])))
        if props.get("event_invoke"):
            graph.add((subject, CTX.eventInvoke, Literal(props["event_invoke"])))
    elif kind == "module_dependency":
        if props.get("depends_on"):
            graph.add((subject, CTX.dependsOnModule, Literal(props["depends_on"])))
        if props.get("configuration"):
            graph.add((subject, CTX.configuration, Literal(props["configuration"])))
    elif kind == "java_method":
        if props.get("return_type"):
            graph.add((subject, CTX.returnType, Literal(props["return_type"])))
        for param in props.get("params", []):
            graph.add((subject, CTX.hasParam, Literal("%s:%s" % (param.get("name", ""), param.get("type", "")))))
    elif kind == "java_call":
        if props.get("callee"):
            graph.add((subject, CTX.calls, CTX["JavaMethod/" + _slug(props.get("caller_class", "")) + "/" + _slug(props["callee"])]))
        if props.get("receiver"):
            graph.add((subject, CTX.receiver, Literal(props["receiver"])))
    elif kind == "java_import":
        if props.get("import"):
            graph.add((subject, CTX.imports, Literal(props["import"])))
    elif kind == "airflow_dag":
        if props.get("schedule"):
            graph.add((subject, CTX.scheduledAt, Literal(props["schedule"])))
    elif kind == "airflow_task":
        if props.get("operator"):
            graph.add((subject, CTX.operatorType, Literal(props["operator"])))
        if props.get("dag"):
            graph.add((subject, CTX.inDAG, CTX["DAG/" + _slug(props["dag"])]))
    elif kind == "cicd_step":
        if props.get("uses"):
            graph.add((subject, CTX.usesAction, Literal(props["uses"])))
        if props.get("run"):
            graph.add((subject, CTX.runCommand, Literal(props["run"])))
        for secret in props.get("secrets", []):
            graph.add((subject, CTX.usesSecret, Literal(secret)))
    elif kind == "edge":
        pass  # handled in pass 2 via _add_edge (no edge subjects minted)


def _add_edge(graph: Graph, props: dict, id_to_subject: dict) -> None:
    pred = props.get("predicate", "")
    if pred not in _EDGE_PREDICATES:
        return
    from_subj = id_to_subject.get(props.get("from", ""))
    if from_subj is None:
        return
    to_raw = props.get("to", "")
    to_subj = id_to_subject.get(to_raw, Literal(to_raw.rsplit("/", 1)[-1]))
    graph.add((from_subj, _EDGE_PREDICATES[pred], to_subj))


def route_filename(fact: dict) -> str:
    """Output file per fact: airflow / cicd / ofbiz_structural."""
    if fact["props"].get("graph") == GRAPH_AIRFLOW or fact["kind"] in ("airflow_dag", "airflow_task"):
        return "airflow.ttl"
    if fact["props"].get("graph") == GRAPH_CICD or fact["kind"] in ("cicd_workflow", "cicd_job", "cicd_step"):
        return "cicd.ttl"
    return "ofbiz_structural.ttl"
