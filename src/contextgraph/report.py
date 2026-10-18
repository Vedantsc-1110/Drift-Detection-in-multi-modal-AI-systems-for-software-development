"""Context Identification Report: Context Graph -> human-readable JSON + Markdown.

Every claim cites graph evidence (counts, names, files). Nothing is asserted
beyond what the triples + facts support. DIRECTLY EXTRACTED and INFERRED are
always separated; out-of-scope references are reported as unresolved, never
presented as discoveries.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from . import queries as Q
from .store import ContextStore

P = "PREFIX ofbiz: <http://example.org/ofbiz/0.1/>\n"


def _one(store, sparql):
    rows = store.sparql(sparql)
    return rows[0] if rows else {}


def build_report(store, manifest, facts, unresolved):
    """Assemble the report dict. store: ContextStore; rest: loaded JSON."""
    r = {}
    r["repository"] = manifest.get("repository", "unknown")
    r["component"] = manifest.get("component", "unknown")
    r["extractor"] = "%s %s" % (manifest.get("extractor"), manifest.get("extractor_version"))
    r["extracted_at"] = manifest.get("extracted_at", "")

    files = manifest.get("files", [])
    r["source_files_analyzed"] = len(files)
    r["source_files"] = sorted(
        [{"file": f["relpath"], "type": f.get("artifact_type", ""), "sha256": f.get("sha256", "")} for f in files],
        key=lambda x: x["file"],
    )

    kinds = Counter(f["kind"] for f in facts)
    etypes = Counter(f["prov"].get("extraction_type", "?") for f in facts)
    r["facts_extracted"] = len(facts)
    r["direct_facts"] = etypes.get("direct", 0)
    r["inferred_facts"] = etypes.get("inferred", 0)
    r["facts_by_kind"] = dict(sorted(kinds.items()))
    r["graph_triples"] = store.count()

    # --- components / services / entities ---
    services = store.sparql(Q.q_services())
    r["services_discovered"] = len(services)
    r["service_names"] = sorted(row["name"] for row in services)
    engines = Counter()
    for row in store.sparql(
        P + "SELECT ?engine WHERE { ?s a ofbiz:Service . OPTIONAL { ?s ofbiz:engine ?engine } }"
    ):
        engines[row.get("engine") or "(absent)"] += 1
    r["services_by_engine"] = dict(sorted(engines.items()))

    entities = store.sparql(
        P + "SELECT ?e ?name WHERE { ?e a ofbiz:ViewEntity ; ofbiz:name ?name } ORDER BY ?name"
    )
    r["entities_discovered"] = len(entities)
    r["entity_names"] = sorted(row["name"] for row in entities)
    base = store.sparql(
        P + "SELECT ?e ?name WHERE { ?e a ofbiz:Entity ; ofbiz:name ?name } ORDER BY ?name"
    )
    r["base_entities_discovered"] = len(base)
    r["base_entity_names"] = sorted(row["name"] for row in base)
    r["entity_note"] = (
        "%d base entities and %d view-entities are represented from this run's source files. "
        "%d entity references remain unresolved; these references are not additional discovered entities."
        % (len(base), len(entities), sum(1 for u in unresolved if u.get("to_kind") == "entity"))
    )

    # --- implementations ---
    impls = store.sparql(Q.q_implementations())
    with_impl = [x for x in impls if x.get("method")]
    r["services_with_implementation"] = len(with_impl)
    r["services_without_implementation"] = len(impls) - len(with_impl)
    r["implementations_sample"] = [
        {"service": x["service"].rsplit("/", 1)[-1], "class": x.get("class"), "method": x.get("invoke")}
        for x in sorted(impls, key=lambda x: x["service"])[:15]
        if x.get("method")
    ]

    # --- inputs / outputs ---
    n_in = _one(store, P + "SELECT (COUNT(*) AS ?n) WHERE { ?s ofbiz:hasInput ?p }").get("n", 0)
    n_out = _one(store, P + "SELECT (COUNT(*) AS ?n) WHERE { ?s ofbiz:hasOutput ?p }").get("n", 0)
    r["input_links"] = int(n_in)
    r["output_links"] = int(n_out)
    r["services_ranked_by_inputs"] = [
        {"service": x["service"], "inputs": int(x["n"])}
        for x in store.sparql(
            P + "SELECT ?service (COUNT(?p) AS ?n) WHERE {"
            " ?s ofbiz:name ?service ; ofbiz:hasInput ?p } GROUP BY ?service ORDER BY DESC(?n) ?service LIMIT 10"
        )
    ]

    # --- entity relationships (in-scope: view composition) ---
    r["view_links"] = kinds.get("view_link", 0)
    r["view_members"] = kinds.get("view_member", 0)
    r["view_aliases"] = kinds.get("view_alias", 0)
    r["relations_extracted"] = kinds.get("relation", 0)
    r["relations_resolved"] = int(_one(store, P + "SELECT (COUNT(*) AS ?n) WHERE { ?r ofbiz:relationTo ?target }").get("n", 0))

    # --- ECAs ---
    ecas = store.sparql(Q.q_eca_rules())
    r["eca_rules_discovered"] = len(ecas)
    r["eca_by_class"] = dict(sorted(Counter(x.get("class", "").rsplit("/", 1)[-1] for x in ecas).items()))
    trig = store.sparql(Q.q_eca_triggered_services())
    r["eca_triggered_services"] = sorted({x["service"] for x in trig})
    r["conditions"] = kinds.get("condition", 0)

    # --- service-to-entity ---
    ent_refs = store.sparql(Q.q_entities_referenced())
    r["service_to_entity_statements"] = len(ent_refs)
    by_entity = Counter(x["entity"] if "://" not in str(x["entity"]) else x["entity"].rsplit("/", 1)[-1] for x in ent_refs)
    r["top_referenced_entities"] = [{"entity": e, "statements": n} for e, n in by_entity.most_common(10)]

    # --- dependencies (fan-in over stated referencesService) ---
    r["top_referenced_services"] = [
        {"service": x["service"], "referenced_by": int(x["fanin"])}
        for x in store.sparql(
            P + "SELECT ?service (COUNT(DISTINCT ?from) AS ?fanin) WHERE {"
            " ?from ofbiz:referencesService ?to . ?to ofbiz:name ?service }"
            " GROUP BY ?service ORDER BY DESC(?fanin) ?service LIMIT 10"
        )
    ]
    r["references_links_total"] = int(
        _one(store, P + "SELECT (COUNT(*) AS ?n) WHERE { ?s ofbiz:referencesService ?o }").get("n", 0)
    )

    # --- provenance / unresolved ---
    r["extraction_methods"] = dict(sorted(Counter(f["prov"].get("method", "?") for f in facts).items()))
    by_ukind = Counter(u["kind"] for u in unresolved)
    r["unresolved_total"] = len(unresolved)
    r["unresolved_by_kind"] = dict(sorted(by_ukind.items()))
    dangling = [u for u in unresolved if u["kind"] == "dangling_reference"]
    top_targets = Counter(u.get("to_name", "?") for u in dangling)
    r["cross_component_dependencies"] = [
        {"target": t, "references": n,
         "via": sorted({u.get("edge", u.get("via", "?")) for u in dangling if u.get("to_name") == t})}
        for t, n in top_targets.most_common(15)
    ]

    return r


SECTION_ORDER = [
    "repository_overview",
    "components",
    "entities",
    "services",
    "implementations",
    "inputs_outputs",
    "entity_relationships",
    "eca_rules",
    "service_to_entity",
    "dependencies",
    "provenance",
    "statistics",
]


def to_markdown(r) -> str:
    L = []
    A = L.append
    A("# Context Identification Report: `%s` / `%s`" % (r["repository"], r["component"]))
    A("")
    A("_Generated %s by %s. Every statement below cites graph evidence; " % (r["extracted_at"], r["extractor"]))
    A("out-of-scope references are listed as unresolved, never presented as discoveries._")
    A("")
    A("## 1. Repository overview")
    A("- Repository: %s; component: `%s`" % (r["repository"], r["component"]))
    A("- Source files analyzed: %d; facts extracted: %d; graph triples: %d" % (r["source_files_analyzed"], r["facts_extracted"], r["graph_triples"]))
    A("- Services: %d; base entities: %d; view-entities: %d; ECA rules: %d" % (r["services_discovered"], r["base_entities_discovered"], r["entities_discovered"], r["eca_rules_discovered"]))
    A("")
    A("## 2. Components discovered")
    A("- Requested component: `%s`. Totals cover every source file listed below, including explicit dependencies." % r["component"])
    A("")
    A("## 3. Entities discovered")
    A("- Base entities (defined in entity models): %d (e.g. %s)" % (r["base_entities_discovered"], ", ".join(r["base_entity_names"][:8]) or "none in scope"))
    A("- View-entities (joins over base entities): %d (e.g. %s)" % (r["entities_discovered"], ", ".join(r["entity_names"][:8])))
    A("- Note: %s" % r["entity_note"])
    A("")
    A("## 4. Services discovered")
    A("- Total: %d" % r["services_discovered"])
    A("- By engine: %s" % ", ".join("%s=%d" % kv for kv in sorted(r["services_by_engine"].items())))
    A("")
    A("## 5. Service implementations")
    A("- DIRECTLY EXTRACTED bindings (stated location+invoke): %d services" % r["services_with_implementation"])
    A("- Services with no code entry point in source (entity-auto/group/interface): %d" % r["services_without_implementation"])
    A("- Sample: %s" % "; ".join("%s -> %s#%s" % (x["service"], x["class"], x["method"]) for x in r["implementations_sample"][:8]))
    A("")
    A("## 6. Service inputs/outputs")
    A("- Parameter links (direct + inferred): %d inputs, %d outputs" % (r["input_links"], r["output_links"]))
    A("- INFERRED parameter links (implements-chain inheritance, evidenced): included in totals above; "
      "see facts with extractionType=inferred")
    A("- Most inputs: %s" % "; ".join("%s (%s)" % (x["service"], x["inputs"]) for x in r["services_ranked_by_inputs"][:5]))
    A("")
    A("## 7. Entity relationships")
    A("- DIRECTLY EXTRACTED view composition: %d view-links, %d member references, %d aliases" % (r["view_links"], r["view_members"], r["view_aliases"]))
    A("- Relation facts extracted: %d; resolved relationTo links: %d. Definitions and targets are limited to the source files in this run." % (r.get("relations_extracted", 0), r.get("relations_resolved", 0)))
    A("")
    A("## 8. ECA rules")
    A("- Rules: %d (%s)" % (r["eca_rules_discovered"], ", ".join("%s=%d" % kv for kv in sorted(r["eca_by_class"].items()))))
    A("- Conditions: %d; services triggered (in scope): %d" % (r["conditions"], len(r["eca_triggered_services"])))
    A("")
    A("## 9. Service-to-entity relationships")
    A("- Statements: %d (stated `default-entity-name` literals + resolved `operatesOn` links)" % r["service_to_entity_statements"])
    A("- Most referenced: %s" % "; ".join("%s (%s)" % (x["entity"], x["statements"]) for x in r["top_referenced_entities"][:8]))
    A("- No exclusivity or CRUD intent is claimed beyond the stated attribute (see ontology).")
    A("")
    A("## 10. Important dependencies")
    A("- Highest fan-in (stated referencesService): %s" % "; ".join("%s (%s)" % (x["service"], x["referenced_by"]) for x in r["top_referenced_services"][:8]))
    A("- referencesService links total: %s" % r["references_links_total"])
    A("- Cross-component dependencies (top dangling targets, reported with evidence, never minted): %s" % "; ".join("%s (%s via %s)" % (x["target"], x["references"], ",".join(x["via"])) for x in r["cross_component_dependencies"][:10]) or "none")
    A("")
    A("## 11. Provenance")
    A("- Every fact carries repository, file, line/XPath, extractor name/version, method, and direct/inferred classification.")
    A("- Extraction methods: %s" % ", ".join("%s=%d" % kv for kv in sorted(r["extraction_methods"].items())))
    A("- Unresolved references (reported, never minted): %d (%s)" % (r["unresolved_total"], ", ".join("%s=%d" % kv for kv in sorted(r["unresolved_by_kind"].items()))))
    A("- Source files: %s" % ", ".join(f["file"] for f in r["source_files"]))
    A("")
    A("## 12. Extraction statistics")
    A("- Facts extracted: %d" % r["facts_extracted"])
    A("- DIRECTLY EXTRACTED: %d" % r["direct_facts"])
    A("- INFERRED (deterministic joins, all evidence cited): %d" % r["inferred_facts"])
    A("- Graph triples: %d" % r["graph_triples"])
    A("- Facts by kind: %s" % ", ".join("%s=%d" % kv for kv in sorted(r["facts_by_kind"].items())))
    A("")
    return "\n".join(L)


def write_reports(report, json_path, md_path):
    Path(json_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(md_path).write_text(to_markdown(report), encoding="utf-8")
