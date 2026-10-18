"""Turtle serializer: fact dicts -> three plain-Turtle files (PART1_PLAN Task 1.7).

Outputs (CONTRACT.md §6): ofbiz_structural.ttl, airflow.ttl, cicd.ttl.
Each file is a PLAIN Turtle dataset with NO GRAPH blocks (Parts 3/4 wrap
files into Named Graphs at load time).
"""

from __future__ import annotations

from pathlib import Path

from .triple_builder import build_graph, route_filename

OUTPUT_FILES = ("ofbiz_structural.ttl", "airflow.ttl", "cicd.ttl")


def serialize(facts: list, repo_root, out_dir, generated_at: str = "") -> dict:
    """Split facts per output file, build one Graph each, write Turtle."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    buckets: dict[str, list] = {name: [] for name in OUTPUT_FILES}
    for fact in facts:
        buckets[route_filename(fact)].append(fact)
    result = {}
    for name in OUTPUT_FILES:
        graph = build_graph(buckets[name], repo_root, generated_at)
        path = out_dir / name
        path.write_text(graph.serialize(format="turtle"), encoding="utf-8")
        result[name] = {"path": str(path), "facts": len(buckets[name]), "triples": len(graph)}
    return result
