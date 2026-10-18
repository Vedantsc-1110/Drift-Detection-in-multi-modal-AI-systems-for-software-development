"""Contract quad store: seven §4 Named Graphs in pyoxigraph (PART3 Task 3.3).

Companion to store.py (default-graph prototype store): this module loads one
contract .ttl file per Named Graph, verifies §5 metadata per subject, and
exports per-graph Turtle. No network access.
"""

from __future__ import annotations

from pathlib import Path

import rdflib
from pyoxigraph import NamedNode, Quad, Store

CTX = "http://context.example.org/"
PROV = "http://www.w3.org/ns/prov#"

# CONTRACT.md §4 Named Graphs in load order.
GRAPH_FILES = {
    "urn:ofbiz_structural": "ofbiz_structural.ttl",
    "urn:airflow": "airflow.ttl",
    "urn:cicd": "cicd.ttl",
    "urn:ofbiz_semantic": "ofbiz_semantic.ttl",
    "urn:document_semantic": "document_semantic.ttl",
    "urn:cuad": "cuad.ttl",
    "urn:edgar": "edgar.ttl",
}

REQUIRED_METADATA = ("confidence", "factType")


def _value(term):
    if term is None:
        return None
    value = getattr(term, "value", None)
    return value if value is not None else str(term)


def _bare(term) -> str:
    """String form without N-Triples <> wrapping."""
    return str(term).strip("<>")


class ContractStore:
    """Persistent pyoxigraph store holding the seven contract Named Graphs."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._store = Store(str(self.path))

    def load_file(self, ttl_path, graph_uri: str) -> int:
        """Parse Turtle with rdflib, add quads to graph_uri. Returns count."""
        graph = rdflib.Graph()
        graph.parse(str(ttl_path), format="turtle")
        target = NamedNode(graph_uri)
        count = 0
        for subj, pred, obj in sorted(graph, key=lambda t: tuple(str(x) for x in t)):
            self._store.add(_quad(subj, pred, obj, target))
            count += 1
        self._store.flush()
        return count

    def load_directory(self, directory) -> dict:
        """Load every §4 file found in directory. Returns {graph: count}."""
        directory = Path(directory)
        result = {}
        for graph_uri, filename in GRAPH_FILES.items():
            path = directory / filename
            if path.is_file():
                result[graph_uri] = self.load_file(path, graph_uri)
        return result

    def graphs(self) -> list:
        return sorted({_bare(q.graph_name) for q in self._store if _bare(q.graph_name).startswith("urn:")})

    def count(self, graph_uri: str | None = None) -> int:
        if graph_uri is None:
            return len(self._store)
        target = NamedNode(graph_uri)
        return sum(1 for q in self._store if q.graph_name == target)

    def sparql(self, query: str) -> list:
        result = self._store.query(query)
        var_names = [v.value for v in result.variables]
        return [{name: _value(terms[i]) for i, name in enumerate(var_names)} for terms in (list(s) for s in result)]

    def export_graph(self, graph_uri: str, out_path) -> int:
        """Dump one Named Graph to plain Turtle. Returns triple count."""
        target = NamedNode(graph_uri)
        graph = rdflib.Graph()
        for quad in self._store:
            if quad.graph_name == target:
                graph.add((_rdflib(quad.subject), _rdflib(quad.predicate), _rdflib(quad.object)))
        Path(out_path).write_text(graph.serialize(format="turtle"), encoding="utf-8")
        return len(graph)

    def verify_metadata(self, graph_uri: str, borrowed: frozenset = frozenset()) -> list:
        """§5 metadata per subject: confidence, factType, wasGeneratedBy,
        hadPrimarySource. Returns error strings (empty = clean).

        borrowed: subject URIs defined elsewhere (e.g. deterministic
        endpoints of probabilistic edges) — exempt, mirroring the Part 2
        validator; their provenance lives in their home graph.
        """
        target = NamedNode(graph_uri)
        by_subject: dict[str, set] = {}
        for quad in self._store:
            if quad.graph_name == target:
                by_subject.setdefault(_bare(quad.subject), set()).add(_bare(quad.predicate))
        errors = []
        for subject in sorted(by_subject):
            if subject in borrowed:
                continue
            predicates = by_subject[subject]
            for prop in ("confidence", "factType"):
                if CTX + prop not in predicates:
                    errors.append("%s: missing ctx:%s in %s" % (subject, prop, graph_uri))
            for prop in ("wasGeneratedBy", "hadPrimarySource"):
                if PROV + prop not in predicates:
                    errors.append("%s: missing prov:%s in %s" % (subject, prop, graph_uri))
        return errors

    def clear(self):
        self._store.clear()
        self._store.flush()

    def close(self):
        self._store.flush()


def _quad(subj, pred, obj, graph_name: NamedNode) -> Quad:
    return Quad(_node(subj), _node(pred), _node(obj), graph_name)


def _node(term):
    from pyoxigraph import BlankNode, Literal

    if isinstance(term, rdflib.BNode):
        return BlankNode(str(term))
    if isinstance(term, rdflib.Literal):
        if term.datatype:
            return Literal(str(term), datatype=NamedNode(str(term.datatype)))
        if term.language:
            return Literal(str(term), language=str(term.language))
        return Literal(str(term))
    return NamedNode(str(term))


def _rdflib(term):
    from pyoxigraph import BlankNode, Literal, NamedNode as OxNamed

    if isinstance(term, BlankNode):
        return rdflib.BNode(term.value)
    if isinstance(term, Literal):
        datatype = rdflib.URIRef(term.datatype.value) if term.datatype else None
        return rdflib.Literal(term.value, datatype=datatype, lang=term.language or None)
    if isinstance(term, OxNamed):
        return rdflib.URIRef(term.value)
    return rdflib.Literal(str(term))


__all__ = ["ContractStore", "GRAPH_FILES"]
