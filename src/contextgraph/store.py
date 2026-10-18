"""Local Oxigraph store: load Turtle, SPARQL, export, clear/rebuild."""
from __future__ import annotations

from pathlib import Path

from pyoxigraph import DefaultGraph, RdfFormat, Store


class ContextStore:
    """Persistent local Oxigraph database for one Context Graph version."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._store = Store(str(self.path))

    def load_turtle(self, ttl_path):
        """Bulk-load a Turtle graph (default graph)."""
        self._store.bulk_load(path=str(ttl_path), format=RdfFormat.TURTLE)
        self._store.flush()

    def count(self) -> int:
        return len(self._store)

    def sparql(self, query: str):
        """Run SPARQL, return rows as [{var: python value}] in query order."""
        result = self._store.query(query)
        var_names = [v.value for v in result.variables]
        out = []
        for solution in result:
            terms = list(solution)
            out.append({name: _term_value(terms[i]) for i, name in enumerate(var_names)})
        return out

    def export_turtle(self, out_path):
        """Dump the default graph back to Turtle."""
        self._store.dump(str(out_path), RdfFormat.TURTLE, from_graph=DefaultGraph())

    def clear(self):
        """Remove all triples (rebuild = clear + load)."""
        self._store.clear()
        self._store.flush()

    def close(self):
        self._store.flush()


def _term_value(term):
    if term is None:
        return None
    value = getattr(term, "value", None)  # Literal -> python value; NamedNode -> bare IRI
    return value if value is not None else str(term)
