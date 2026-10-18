"""Canonical drift pipeline (§7.3 Steps 4–9, PART4 Task 4.9).

Wires diff → impact → severity → remediation → patches over fixture (or
real) version graphs and agent snapshots. Severity inputs split visibly:
DERIVED from the change (breakage shape, directness rule, assumption flag)
plus fixture-DECLARED labels (criticality per OPEN Q2, constraint,
conflicting) passed in as `labels`. The report records both per agent.
"""

from __future__ import annotations

import rdflib
from rdflib.namespace import RDF

from .patch import build_patch
from .remediation import remediate
from .severity import verdict
from .sparql_diff import diff_snapshot
from .traversal import traverse

CTX = "http://context.example.org/"
TYPE = str(RDF.type)


def _subjects(triples):
    return {t[0] for t in triples}


def derive_inputs(agent: str, snapshot: rdflib.Graph, version: rdflib.Graph, diff: dict) -> dict:
    """Derive breakage / directness / assumption from the change shape.

    - breakage "signature": a type triple was removed (subject deleted) or a
      removed edge now dangles (its object is gone from the version).
    - directness: 1-hop when a tracked subject vanished entirely; 2-hop when
      a tracked subject persists with changed own triples (modifications,
      additions, or removals whose object still exists); 3+ when the agent's
      own triples are intact but a referenced symbol vanished.
    - assumption invalidated: any removal or modification present.
    """
    removals = diff.get("removals", [])
    modifications = diff.get("modifications", [])
    additions = diff.get("additions", [])
    tracked = {str(s) for s in snapshot.subjects()}
    version_subjects = {str(s) for s in version.subjects()}
    version_triples = set(version)

    signature = any(p == TYPE for _, p, _ in removals)
    if not signature:
        mentioned = {str(t[0]) for t in version_triples} | {str(t[2]) for t in version_triples}
        for _, _, o in removals:
            if o not in mentioned:
                signature = True
                break
    if signature:
        breakage = "signature"
    elif additions and not removals and not modifications:
        breakage = "additive"
    else:
        breakage = "cosmetic"

    vanished_tracked = [s for s in _subjects(removals) | {m[0] for m in modifications}
                        if s in tracked and s not in version_subjects]
    if vanished_tracked:
        hops = 1
    else:
        mentioned = {str(t[0]) for t in version_triples} | {str(t[2]) for t in version_triples}
        own_change = (
            any(m[0] in tracked for m in modifications)
            or any(a[0] in tracked for a in additions)
            or any(s in tracked and o in mentioned for s, _, o in removals))
        hops = 2 if own_change else 3
    return {"breakage": breakage, "directness": hops,
            "assumption": bool(removals or modifications)}


def run(version: rdflib.Graph, version_id: str, snapshots: dict,
        labels: dict | None = None, snapshot_id_prefix: str = "urn:agent_snapshot") -> dict:
    """Run the canonical scenario. snapshots: {agent: Graph}. labels:
    {agent: {criticality, constraint, conflicting}}. Returns per-agent
    results plus the report sentence."""
    labels = labels or {}
    agents = {}
    for agent in sorted(snapshots):
        snapshot = snapshots[agent]
        diff = diff_snapshot(version, version_id, snapshot, "%s_%s" % (snapshot_id_prefix, agent))
        has_diff = any(diff.values())
        if not has_diff:
            agents[agent] = {"diff": diff, "impact": {}, "severity": verdict(False),
                             "remediation": remediate(0.0), "patch": None}
            continue
        derived = derive_inputs(agent, snapshot, version, diff)
        declared = labels.get(agent, {})
        scored = verdict(True,
                         criticality=declared.get("criticality", "normal"),
                         breakage=derived["breakage"],
                         directness=derived["directness"],
                         assumption=derived["assumption"],
                         constraint=declared.get("constraint", False),
                         conflicting=declared.get("conflicting", False))
        changed = _subjects(diff["removals"]) | {m[0] for m in diff["modifications"]}
        impact = traverse(version, sorted(changed))
        snapshot_now = sorted({(str(s), str(p), str(o)) for s in snapshot.subjects()
                               for p, o in version.predicate_objects(rdflib.URIRef(s))})
        agents[agent] = {
            "diff": diff, "impact": impact, "severity": scored,
            "severity_inputs": {"derived": derived, "declared": {
                "criticality": declared.get("criticality", "normal"),
                "constraint": declared.get("constraint", False),
                "conflicting": declared.get("conflicting", False)}},
            "remediation": remediate(scored["score"]),
            "patch": build_patch(agent, diff, scored, remediate(scored["score"]), snapshot_now),
        }
    undisturbed = sorted(a for a, r in agents.items() if r["remediation"] == "CONTINUE")
    patched = sorted(a for a, r in agents.items() if r["patch"] is not None)
    sentence = "Agent %s continues undisturbed; %s receive context patches." % (
        " and ".join(undisturbed) if undisturbed else "none",
        " and ".join(patched) if patched else "none")
    return {"agents": agents, "report": sentence}
