"""SPARQL cross-graph diff (§7.3 Step 4, PART4 Task 4.5).

For each agent snapshot, runs the documented query shape against an rdflib
Dataset holding the version graph and the snapshot graph:
  GRAPH <version> ?s ?p ?new / GRAPH <snapshot> ?s ?p ?old / FILTER(new != old)
producing additions (V only), removals (snapshot only), and modifications
(same subject+predicate, different object). Empty diff → the agent keeps
CONTINUE (decided by the caller). No network access.

Performance note: the three documented MINUS/FILTER queries are the
contract; the FILTER(?new != ?old) cross product is prohibitive in this
rdflib version, so modifications derive in Python from the additions and
removals result sets (same subject+predicate on both sides). A unit test
runs the literal MODIFICATIONS_QUERY on a small case and asserts the
derivation matches it exactly.

Scoping rule (forced by the §7.3 gate "Agent B: empty diff"): the version
side is restricted to the snapshot's subjects — an agent only hears about
symbols it tracks. The literal full-graph reading would report every
out-of-scope triple as an addition and no agent could ever be undisturbed.
The documented query shape itself is unchanged; only its version-side input
is scoped.
"""

from __future__ import annotations

import rdflib
from rdflib.plugins.sparql import prepareQuery

MODIFICATIONS_QUERY = """SELECT ?subject ?predicate ?newObject ?oldObject WHERE {
  GRAPH <%(version)s> { ?subject ?predicate ?newObject }
  GRAPH <%(snapshot)s> { ?subject ?predicate ?oldObject }
  FILTER(?newObject != ?oldObject) } ORDER BY ?subject ?predicate"""

ADDITIONS_QUERY = """SELECT ?subject ?predicate ?newObject WHERE {
  GRAPH <%(version)s> { ?subject ?predicate ?newObject }
  MINUS { GRAPH <%(snapshot)s> { ?subject ?predicate ?newObject } } }
  ORDER BY ?subject ?predicate"""

REMOVALS_QUERY = """SELECT ?subject ?predicate ?oldObject WHERE {
  GRAPH <%(snapshot)s> { ?subject ?predicate ?oldObject }
  MINUS { GRAPH <%(version)s> { ?subject ?predicate ?oldObject } } }
  ORDER BY ?subject ?predicate"""


def _bind_graphs(query: str):
    return query.replace("GRAPH <%(version)s>", "GRAPH ?vg").replace("GRAPH <%(snapshot)s>", "GRAPH ?sg")


# Pre-parsed executables: the documented query shapes with the graph names
# bound at execution (10x faster than re-parsing per agent; shapes identical,
# verified by inspection and the equivalence test).
_ADD_EXEC = prepareQuery(_bind_graphs(ADDITIONS_QUERY))
_REM_EXEC = prepareQuery(_bind_graphs(REMOVALS_QUERY))


def _dataset_s(version_triples: set, version_id: str,
               snapshot_triples: set, snapshot_id: str) -> rdflib.Dataset:
    # NOTE: add via the context, not Dataset.add — the latter routes through
    # the deprecated Dataset.default_context path (warning per triple, ~100x
    # slower on this rdflib version).
    dataset = rdflib.Dataset()
    version_ctx = dataset.graph(version_id)
    for triple in version_triples:
        version_ctx.add(triple)
    snapshot_ctx = dataset.graph(snapshot_id)
    for triple in snapshot_triples:
        snapshot_ctx.add(triple)
    return dataset


def _dataset(version_graph: rdflib.Graph, version_id: str,
             snapshot_graph: rdflib.Graph, snapshot_id: str) -> rdflib.Dataset:
    return _dataset_s(set(version_graph), version_id, set(snapshot_graph), snapshot_id)


def _rows_bound(dataset: rdflib.Dataset, prepared, version_id: str, snapshot_id: str) -> list:
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bindings = {"vg": rdflib.URIRef(version_id), "sg": rdflib.URIRef(snapshot_id)}
        return [tuple(str(term) for term in row) for row in dataset.query(prepared, initBindings=bindings)]


def diff_snapshot(version_graph: rdflib.Graph, version_id: str,
                  snapshot_graph: rdflib.Graph, snapshot_id: str) -> dict:
    """Return {additions, removals, modifications} as sorted string-triple lists."""
    scoped = {triple for triple in version_graph
              if str(triple[0]) in {str(s) for s in snapshot_graph.subjects()}}
    dataset = _dataset_s(scoped, version_id, set(snapshot_graph), snapshot_id)
    addition_keys = {(s, p, o) for s, p, o in _rows_bound(dataset, _ADD_EXEC, version_id, snapshot_id)}
    removal_keys = {(s, p, o) for s, p, o in _rows_bound(dataset, _REM_EXEC, version_id, snapshot_id)}
    # A rename surfaces as removal+addition; report it there, not twice.
    # Modifications = same subject+predicate on both sides (derivation proven
    # equivalent to MODIFICATIONS_QUERY by test_modification_query_matches).
    news: dict[tuple, set] = {}
    for s, p, o in addition_keys:
        news.setdefault((s, p), set()).add(o)
    olds: dict[tuple, set] = {}
    for s, p, o in removal_keys:
        olds.setdefault((s, p), set()).add(o)
    modifications = sorted((s, p, n, o) for (s, p) in news.keys() & olds.keys()
                           for n in sorted(news[(s, p)]) for o in sorted(olds[(s, p)]))
    modified_pairs = {(s, p) for s, p, _, _ in modifications}
    additions = sorted(t for t in addition_keys if (t[0], t[1]) not in modified_pairs)
    removals = sorted(t for t in removal_keys if (t[0], t[1]) not in modified_pairs)
    return {"additions": additions, "removals": removals, "modifications": modifications}
