"""Typed impact traversal (§7.3 Step 5, PART4 Task 4.6).

BFS from changed symbols along EXACTLY the CONTRACT §7 path:
  Symbol --calls--> Symbol --implementedBy--> Service --constrainedBy--> Policy
  --mentionedIn--> Contract/Filing --dependsOn--> DAG Task --assignedTo--> Agent/System
with the declared inverses needed to walk it (implementedByOf, constrainedBy,
mentionedIn, invokedBy for Task→Service bridges, calledBy, dependencyOf).
Predicates outside the path are not followed (typed discipline). Literals
are never entities. Returns {entity: {distance, via}} with shortest paths.
"assignedTo" has no contract declaration; it is followed when present and
otherwise simply absent (documented gap — no agent individuals exist yet).
"""

from __future__ import annotations

from collections import deque

import rdflib

CTX = "http://context.example.org/"

# predicate local name -> (forward label, reverse label or None)
PATH_EDGES = {
    "calls": ("calls", "calledBy"),
    "implementedBy": ("implementedBy", "implementedByOf"),
    "constrains": ("constrains", "constrainedBy"),
    "mentionsEntity": ("mentionsEntity", "mentionedIn"),
    "mentionsProcess": ("mentionsProcess", "mentionedIn"),
    "dependsOn": ("dependsOn", "dependencyOf"),
    "invokesService": ("invokesService", "invokedBy"),
    "assignedTo": ("assignedTo", None),
}


def traverse(graph: rdflib.Graph, seeds: list, max_hops: int | None = None) -> dict:
    """BFS over the §7 path. seeds: URI strings. Returns {uri: {distance, via}}."""
    seeds = [str(s) for s in seeds]
    reached: dict[str, dict] = {seed: {"distance": 0, "via": []} for seed in seeds}
    queue: deque = deque(seeds)
    while queue:
        current = queue.popleft()
        if max_hops is not None and reached[current]["distance"] >= max_hops:
            continue
        for neighbor, label in _moves(graph, current):
            key = str(neighbor)
            if key not in reached:
                reached[key] = {"distance": reached[current]["distance"] + 1,
                                "via": reached[current]["via"] + [label]}
                queue.append(key)
    return reached


def _moves(graph: rdflib.Graph, current: str):
    """Yield (neighbor, step label) hops along the §7 path."""
    subject = rdflib.URIRef(current)
    for _, pred, obj in graph.triples((subject, None, None)):
        name = str(pred).rsplit("/", 1)[-1]
        if name in PATH_EDGES and isinstance(obj, rdflib.URIRef):
            yield obj, PATH_EDGES[name][0]
    for subj, pred, _ in graph.triples((None, None, subject)):
        name = str(pred).rsplit("/", 1)[-1]
        if name in PATH_EDGES and PATH_EDGES[name][1] is not None and isinstance(subj, rdflib.URIRef):
            yield subj, PATH_EDGES[name][1]
