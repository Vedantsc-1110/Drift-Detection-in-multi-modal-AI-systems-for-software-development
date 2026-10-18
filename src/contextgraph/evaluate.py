"""Part 1 deterministic evaluation harness (no LLM, no network).

Compares SOURCE/GOLD (evaluation/questions.yaml) against CONTEXT GRAPH answers
(Oxigraph store + facts + manifest + unresolved) with structured comparison.

Statuses: CORRECT | PARTIAL | INCORRECT | UNRESOLVED
Fact types: DIRECT | INFERRED | UNRESOLVED
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

NB = "http://example.org/ofbiz/0.1/"
P = "PREFIX ofbiz: <http://example.org/ofbiz/0.1/>\n"


def _norm_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _norm_set(values) -> list:
    return sorted({_norm_text(v) for v in values if _norm_text(v)})


def _load_yaml(path):
    import yaml

    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Evaluator:
    """Holds graph + pipeline outputs for deterministic question checks."""

    def __init__(self, store, facts, manifest, unresolved):
        self.store = store
        self.facts = facts
        self.manifest = manifest
        self.unresolved = unresolved
        self.facts_by_id = {f["id"]: f for f in facts}

    # -- helpers ---------------------------------------------------------
    def _sparql(self, q):
        return self.store.sparql(q)

    def _fact(self, fid):
        return self.facts_by_id.get(fid)

    def _facts_for_service(self, name):
        return [f for f in self.facts if f["kind"] == "service" and f["props"].get("name") == name]

    def _evidence_from_fact(self, fact):
        if not fact:
            return {}
        prov = fact.get("prov", {})
        return {
            "file": prov.get("file"),
            "line": prov.get("line"),
            "xpath": prov.get("xpath"),
            "extractor": prov.get("extractor"),
            "extractor_version": prov.get("extractor_version"),
            "method": prov.get("method"),
            "extraction_type": prov.get("extraction_type"),
        }

    def _has_node(self, uri, rdf_class):
        rows = self._sparql(
            P + "ASK { <%s> a ofbiz:%s }" % (uri, rdf_class)
        )
        # ContextStore.sparql returns rows for SELECT; for ASK pyoxigraph
        # returns a single solution with empty binding — handle robustly.
        # Fall back to SELECT check.
        try:
            rows2 = self._sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % uri)
            classes = [r.get("c", "") for r in rows2]
            return any(c.endswith("/" + rdf_class) or c == rdf_class for c in classes)
        except Exception:
            return False

    def _node_classes(self, uri):
        rows = self._sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % uri)
        return sorted(r.get("c", "") for r in rows)

    def _unresolved_for(self, to_name):
        return [u for u in self.unresolved if u.get("to_name") == to_name]

    # -- checks ----------------------------------------------------------
    def check_component_name(self, q):
        expected = q["expected_answer"]["component"]
        rows = self._sparql(P + 'SELECT ?name WHERE { ?c a ofbiz:Component ; ofbiz:name ?name } ORDER BY ?name')
        names = sorted(r["name"] for r in rows)
        graph_answer = {"components": names}
        facts = [f for f in self.facts if f["kind"] == "component" and f["props"].get("name") == expected]
        ev = self._evidence_from_fact(facts[0] if facts else None)
        if expected in names:
            return graph_answer, "CORRECT", "DIRECT", ev, "Component node present."
        # unresolved fallback: component referenced but missing?
        return graph_answer, "INCORRECT", "DIRECT", ev, "Expected component '%s' not in %s." % (expected, names)

    def check_scope_components(self, q):
        exp = q["expected_answer"]
        rows = self._sparql(P + 'SELECT ?name WHERE { ?c a ofbiz:Component ; ofbiz:name ?name } ORDER BY ?name')
        names = sorted(r["name"] for r in rows)
        scope = self.manifest.get("scope", {})
        graph_answer = {
            "components": names,
            "dependency_files": sorted(scope.get("dependency_files", [])),
            "include_dependencies": scope.get("include_dependencies", False),
        }
        ev = {"file": "manifest:scope", "line": None, "xpath": None,
              "extractor": self.manifest.get("extractor"), "extractor_version": self.manifest.get("extractor_version"),
              "method": "scope", "extraction_type": "direct"}
        if set(exp["components"]) == set(names) and set(exp["dependency_files"]) == set(graph_answer["dependency_files"]) and exp["include_dependencies"] == graph_answer["include_dependencies"]:
            return graph_answer, "CORRECT", "DIRECT", ev, "Scope matches manifest + graph."
        if set(exp["components"]).issubset(set(names)):
            return graph_answer, "PARTIAL", "DIRECT", ev, "Subset of expected components present."
        return graph_answer, "INCORRECT", "DIRECT", ev, "Scope mismatch."

    def check_service_description(self, q):
        exp = q["expected_answer"]
        svc = exp["service"]
        uri = NB + "service/" + svc
        rows = self._sparql(P + 'SELECT ?desc WHERE { <%s> ofbiz:description ?desc }' % uri)
        desc = rows[0]["desc"] if rows else None
        graph_answer = {"service": svc, "description": desc}
        facts = self._facts_for_service(svc)
        ev = self._evidence_from_fact(facts[0] if facts else None)
        if desc is None:
            if self._unresolved_for(svc):
                return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "Service missing; reference reported as unresolved."
            return graph_answer, "INCORRECT", "DIRECT", ev, "No description triple."
        if _norm_text(desc) == _norm_text(exp["description"]):
            return graph_answer, "CORRECT", "DIRECT", ev, "Verbatim description matches."
        return graph_answer, "INCORRECT", "DIRECT", ev, "Description mismatch."

    def check_service_implementation(self, q):
        exp = q["expected_answer"]
        svc = exp["service"]
        uri = NB + "service/" + svc
        rows = self._sparql(
            P + 'SELECT ?engine ?loc ?inv WHERE { <%s> a ofbiz:Service . OPTIONAL { <%s> ofbiz:engine ?engine } OPTIONAL { <%s> ofbiz:implLocation ?loc } OPTIONAL { <%s> ofbiz:implInvoke ?inv } }' % ((uri,) * 4)
        )
        d = rows[0] if rows else {}
        impl_rows = self._sparql(P + 'SELECT ?m WHERE { <%s> ofbiz:implementedBy ?m }' % uri)
        method_uri = impl_rows[0]["m"] if impl_rows else None
        graph_answer = {"service": svc, "engine": d.get("engine"), "implementation_class": d.get("loc"), "method": d.get("inv"), "method_uri": method_uri}
        facts = self._facts_for_service(svc)
        ev = self._evidence_from_fact(facts[0] if facts else None)
        if not rows or not d.get("loc"):
            if self._unresolved_for(svc):
                return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "Implementation target outside scope."
            return graph_answer, "INCORRECT", "DIRECT", ev, "No implementation binding."
        ok_engine = _norm_text(d.get("engine")) == _norm_text(exp["engine"])
        ok_class = _norm_text(d.get("loc")) == _norm_text(exp["implementation_class"])
        ok_method = _norm_text(d.get("inv")) == _norm_text(exp["method"])
        if ok_engine and ok_class and ok_method:
            return graph_answer, "CORRECT", "DIRECT", ev, "Source-stated binding matches (not code-verified)."
        if ok_class and ok_method:
            return graph_answer, "PARTIAL", "DIRECT", ev, "Class+method match, engine differs."
        return graph_answer, "INCORRECT", "DIRECT", ev, "Binding mismatch."

    def _param_names(self, svc, predicate):
        if predicate == "inputs":
            q = P + 'SELECT ?param WHERE { <%s> ofbiz:hasInput ?p . ?p ofbiz:name ?param } ORDER BY ?param' % (NB + "service/" + svc)
        else:
            q = P + 'SELECT ?param WHERE { <%s> ofbiz:hasOutput ?p . ?p ofbiz:name ?param } ORDER BY ?param' % (NB + "service/" + svc)
        return sorted(r["param"] for r in self._sparql(q))

    def check_service_inputs(self, q):
        exp = q["expected_answer"]
        svc = exp["service"]
        expected = _norm_set(exp["inputs"])
        graph = _norm_set(self._param_names(svc, "inputs"))
        graph_answer = {"service": svc, "inputs": graph, "count": len(graph)}
        facts = self._facts_for_service(svc)
        ev = self._evidence_from_fact(facts[0] if facts else None)
        if not graph and not expected:
            return graph_answer, "CORRECT", "DIRECT", ev, "Both empty."
        if not graph:
            if self._unresolved_for(svc):
                return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "Service outside scope."
            return graph_answer, "INCORRECT", "DIRECT", ev, "No inputs in graph."
        missing = sorted(set(expected) - set(graph))
        extra = sorted(set(graph) - set(expected))
        if not missing and not extra:
            return graph_answer, "CORRECT", "DIRECT", ev, "Input sets identical (%d)." % len(graph)
        overlap = len(set(expected) & set(graph))
        cov = overlap / max(len(expected), 1)
        if overlap and cov >= 0.5:
            return graph_answer, "PARTIAL", "DIRECT", ev, "Overlap %.2f; missing=%s extra=%s." % (cov, missing[:10], extra[:10])
        return graph_answer, "INCORRECT", "DIRECT", ev, "Missing=%s extra=%s." % (missing[:10], extra[:10])

    def check_service_outputs(self, q):
        exp = q["expected_answer"]
        svc = exp["service"]
        expected = _norm_set(exp["outputs"])
        graph = _norm_set(self._param_names(svc, "outputs"))
        graph_answer = {"service": svc, "outputs": graph, "count": len(graph)}
        facts = self._facts_for_service(svc)
        ev = self._evidence_from_fact(facts[0] if facts else None)
        if not graph:
            if self._unresolved_for(svc):
                return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "Service outside scope."
            return graph_answer, "INCORRECT", "DIRECT", ev, "No outputs in graph."
        missing = sorted(set(expected) - set(graph))
        extra = sorted(set(graph) - set(expected))
        if not missing and not extra:
            return graph_answer, "CORRECT", "DIRECT", ev, "Output sets identical."
        overlap = len(set(expected) & set(graph))
        if overlap:
            return graph_answer, "PARTIAL", "DIRECT", ev, "Partial overlap; missing=%s extra=%s." % (missing, extra)
        return graph_answer, "INCORRECT", "DIRECT", ev, "Mismatch."

    def check_entity_exists(self, q):
        exp = q["expected_answer"]
        name = exp["entity"]
        uri = NB + "entity/" + name
        classes = self._node_classes(uri)
        short = sorted(c.rsplit("/", 1)[-1] for c in classes)
        graph_answer = {"entity": name, "classes": short, "exists": bool(classes)}
        facts = [f for f in self.facts if f["kind"] in ("entity", "view_entity") and f["props"].get("name") == name]
        ev = self._evidence_from_fact(facts[0] if facts else None)
        want_base = exp.get("is_base", True)
        if not classes:
            if self._unresolved_for(name):
                return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "No node; reference reported as unresolved."
            return graph_answer, "INCORRECT", "DIRECT", ev, "Entity node missing and not reported."
        is_entity = "Entity" in short
        is_view = "ViewEntity" in short
        if want_base and is_entity and not is_view:
            return graph_answer, "CORRECT", "DIRECT", ev, "Base Entity node present (not a view)."
        if want_base and is_view:
            return graph_answer, "INCORRECT", "DIRECT", ev, "View confused for base (has ViewEntity type)."
        if not want_base and is_view:
            return graph_answer, "CORRECT", "DIRECT", ev, "ViewEntity node present."
        return graph_answer, "PARTIAL", "DIRECT", ev, "Node present with classes %s." % short

    def check_entity_pk(self, q):
        exp = q["expected_answer"]
        name = exp["entity"]
        uri = NB + "entity/" + name
        rows = self._sparql(
            P + 'SELECT ?name WHERE { <%s> ofbiz:hasAttribute ?a . ?a ofbiz:name ?name ; ofbiz:isPrimaryKey \"true\"^^<http://www.w3.org/2001/XMLSchema#boolean> } ORDER BY ?name' % uri
        )
        graph = _norm_set(r["name"] for r in rows)
        expected = _norm_set(exp["primary_keys"])
        graph_answer = {"entity": name, "primary_keys": graph}
        flds = [f for f in self.facts if f["kind"] == "entity_field" and f["props"].get("entity") == name and f["props"].get("is_primary_key")]
        ev = self._evidence_from_fact(flds[0] if flds else (self._fact(NB + "entity/" + name)))
        if not graph:
            if not self._node_classes(uri):
                if self._unresolved_for(name):
                    return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "Entity outside scope."
                return graph_answer, "INCORRECT", "DIRECT", ev, "No PK triples."
            return graph_answer, "INCORRECT", "DIRECT", ev, "No PKs in graph."
        if graph == expected:
            return graph_answer, "CORRECT", "DIRECT", ev, "PK sets identical."
        if set(expected).issubset(set(graph)) or set(graph).issubset(set(expected)):
            return graph_answer, "PARTIAL", "DIRECT", ev, "PK subset overlap."
        return graph_answer, "INCORRECT", "DIRECT", ev, "PK mismatch."

    def check_entity_relations(self, q):
        exp = q["expected_answer"]
        subject = exp["subject"]
        subj_uri = NB + "entity/" + subject
        # resolved relationTo targets for this subject
        rows = self._sparql(
            P + 'SELECT ?target WHERE { ?r ofbiz:relationFrom <%s> . ?r ofbiz:relationTo ?t . ?t ofbiz:name ?target } ORDER BY ?target' % subj_uri
        )
        graph_resolved = _norm_set(r["target"] for r in rows)
        # all relation nodes for subject (to count)
        rows2 = self._sparql(P + 'SELECT ?r WHERE { ?r ofbiz:relationFrom <%s> }' % subj_uri)
        n_rel_nodes = len(rows2)
        un_for_subject = [u for u in self.unresolved if u.get("edge") == "relationTo" and subject in u.get("from", "")]
        un_targets = _norm_set(u.get("to_name", "") for u in un_for_subject)
        graph_answer = {"subject": subject, "resolved_targets": graph_resolved,
                        "relation_nodes": n_rel_nodes, "unresolved_targets": un_targets}
        exp_resolved = _norm_set(r["target"] for r in exp.get("resolved_relations", []))
        exp_un = _norm_set(exp.get("unresolved_targets", []))
        rel_facts = [f for f in self.facts if f["kind"] == "relation" and f["props"].get("subject") == subject]
        ev = self._evidence_from_fact(rel_facts[0] if rel_facts else None)
        missing_res = sorted(set(exp_resolved) - set(graph_resolved))
        missing_un = sorted(set(exp_un) - set(un_targets))
        if not missing_res and not missing_un:
            return graph_answer, "CORRECT", "DIRECT", ev, "Resolved + unresolved subsets verified."
        if not missing_res and missing_un:
            return graph_answer, "PARTIAL", "DIRECT", ev, "Resolved ok; unresolved missing %s." % missing_un
        if missing_res and len(missing_res) < len(exp_resolved):
            return graph_answer, "PARTIAL", "DIRECT", ev, "Partial resolved; missing %s." % missing_res
        return graph_answer, "INCORRECT", "DIRECT", ev, "Missing resolved %s." % missing_res

    def check_eca_behavior(self, q):
        exp = q["expected_answer"]
        trig = exp["trigger_entity"]
        rows = self._sparql(
            P + 'SELECT ?eca ?op ?ev WHERE { ?eca a ofbiz:EntityECA ; ofbiz:triggerEntityName \"%s\" ; ofbiz:ecaOperation ?op ; ofbiz:ecaEvent ?ev } ORDER BY ?eca' % trig
        )
        if not rows:
            return {"trigger_entity": trig}, "INCORRECT", "DIRECT", {}, "No EntityECA for trigger."
        eca_uri = rows[0]["eca"]
        conds = self._sparql(P + 'SELECT ?f ?o ?v WHERE { <%s> ofbiz:hasCondition ?c . ?c ofbiz:condField ?f ; ofbiz:condOperator ?o ; ofbiz:condValue ?v } ORDER BY ?f' % eca_uri)
        # normalize to list of dicts (sorted by field for determinism)
        graph_conds = sorted(({"field": r["f"], "operator": r["o"], "value": r["v"]} for r in conds), key=lambda d: (d["field"], d["operator"], d["value"]))
        exp_conds = exp["conditions"]
        cond_ok = all(any(_norm_text(g["field"]) == _norm_text(e["field"]) and _norm_text(g["operator"]) == _norm_text(e["operator"]) and _norm_text(g["value"]) == _norm_text(e["value"]) for g in graph_conds) for e in exp_conds)
        action = exp["action_service"]
        # triggersService edge?
        trig_rows = self._sparql(P + 'SELECT ?s WHERE { <%s> ofbiz:triggersService ?x . ?x ofbiz:name ?s }' % eca_uri)
        trig_services = [r["s"] for r in trig_rows]
        un = self._unresolved_for(action)
        eca_fact = self._fact(eca_uri)
        ev = self._evidence_from_fact(eca_fact)
        graph_answer = {"eca": eca_uri.rsplit("/", 1)[-1], "eca_uri": eca_uri,
                        "operation": rows[0].get("op"), "event": rows[0].get("ev"),
                        "conditions": graph_conds, "action_service": action,
                        "triggers_edge_present": action in trig_services,
                        "unresolved_reported": bool(un)}
        if cond_ok and action in trig_services:
            return graph_answer, "CORRECT", "DIRECT", ev, "Full behavior resolved in graph."
        if cond_ok and un and action not in trig_services:
            # Honest unresolved: ECA+conditions known, target outside scope.
            return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "ECA+conditions resolved; action '%s' outside scope (reported, not minted)." % action
        if cond_ok:
            return graph_answer, "PARTIAL", "DIRECT", ev, "Conditions ok; action edge missing."
        return graph_answer, "INCORRECT", "DIRECT", ev, "Conditions mismatch."

    def check_eca_identify(self, q):
        exp = q["expected_answer"]
        trig = exp["trigger_entity"]
        rows = self._sparql(
            P + 'SELECT ?eca ?op ?ev ?cls WHERE { ?eca a ?cls . FILTER(?cls IN (ofbiz:EntityECA, ofbiz:ServiceECA)) . ?eca ofbiz:triggerEntityName \"%s\" . OPTIONAL { ?eca ofbiz:ecaOperation ?op } OPTIONAL { ?eca ofbiz:ecaEvent ?ev } } ORDER BY ?eca' % trig
        )
        eca_fact = None
        ev = {}
        if rows:
            eca_fact = self._fact(rows[0]["eca"])
            ev = self._evidence_from_fact(eca_fact)
        graph_answer = {"matches": [{"eca": r["eca"].rsplit("/", 1)[-1], "operation": r.get("op"), "event": r.get("ev"), "class": r.get("cls", "").rsplit("/", 1)[-1]} for r in rows]}
        for r in rows:
            cls = r.get("cls", "").rsplit("/", 1)[-1]
            if cls == exp["eca_class"] and _norm_text(r.get("op")) == _norm_text(exp["operation"]) and _norm_text(r.get("ev")) == _norm_text(exp["event"]):
                return graph_answer, "CORRECT", "DIRECT", ev, "ECA rule identified."
        if rows:
            return graph_answer, "PARTIAL", "DIRECT", ev, "Trigger matches but class/op/event differ."
        return graph_answer, "INCORRECT", "DIRECT", ev, "No ECA for trigger."

    def check_eca_action(self, q):
        exp = q["expected_answer"]
        action = exp["action_service"]
        svc_uri = NB + "service/" + action
        classes = self._node_classes(svc_uri)
        un = [u for u in self.unresolved if u.get("to_name") == action and u.get("edge") == "triggersService"]
        graph_answer = {"action_service": action, "node_classes": sorted(c.rsplit("/", 1)[-1] for c in classes),
                        "node_exists": bool(classes), "unresolved_reported": bool(un),
                        "unresolved_via": sorted({u.get("via", "") for u in un})}
        ev = {"file": un[0]["source"]["file"] if un else None, "line": un[0]["source"]["line"] if un else None,
              "xpath": un[0]["source"].get("xpath") if un else None, "extraction_type": "unresolved"}
        if not classes and un:
            return graph_answer, "UNRESOLVED", "UNRESOLVED", ev, "Reference stated in eecas.xml; target outside scope (correctly not minted)."
        if classes:
            return graph_answer, "INCORRECT", "DIRECT", ev, "External service was minted (hallucinated)."
        return graph_answer, "INCORRECT", "DIRECT", ev, "Action reference missing entirely."

    def check_provenance(self, q):
        exp = q["expected_answer"]
        svc = exp["service"]
        uri = NB + "service/" + svc
        rows = self._sparql(
            P + 'SELECT ?file ?sha ?atype ?etype ?line WHERE { <%s> ofbiz:definedIn ?a ; ofbiz:extractionType ?etype . ?a ofbiz:filePath ?file . OPTIONAL { ?a ofbiz:sha256 ?sha } OPTIONAL { ?a ofbiz:artifactType ?atype } OPTIONAL { <%s> ofbiz:evidenceLine ?line } }' % (uri, uri)
        )
        d = rows[0] if rows else {}
        xpath_rows = self._sparql(P + 'SELECT ?xp WHERE { <%s> ofbiz:sourceXPath ?xp }' % uri)
        xp = xpath_rows[0]["xp"] if xpath_rows else None
        graph_answer = {"service": svc, "file": d.get("file"), "line": d.get("line"),
                        "xpath": xp, "extraction_type": d.get("etype"),
                        "sha256_present": bool(d.get("sha")), "artifact_type": d.get("atype")}
        facts = self._facts_for_service(svc)
        ev = self._evidence_from_fact(facts[0] if facts else None)
        ok = (d.get("file") == exp["file"] and str(d.get("line")) == str(exp["line"])
              and xp == exp["xpath"] and d.get("etype") == exp["extraction_type"] and bool(d.get("sha")))
        if ok:
            return graph_answer, "CORRECT", "DIRECT", ev, "Full source evidence present."
        partial = (d.get("file") == exp["file"] and d.get("etype") == exp["extraction_type"])
        if partial:
            return graph_answer, "PARTIAL", "DIRECT", ev, "File+type ok; line/xpath/sha differ."
        if not rows:
            return graph_answer, "INCORRECT", "DIRECT", ev, "No provenance triples."
        return graph_answer, "INCORRECT", "DIRECT", ev, "Provenance mismatch."

    def check_unresolved(self, q):
        exp_targets = q["expected_answer"]["unresolved_targets"]
        items = []
        all_ok = True
        for t in exp_targets:
            name = t["name"]
            kind = t.get("kind", "")
            un = self._unresolved_for(name)
            # node must NOT exist
            node_uris = [NB + "service/" + name, NB + "entity/" + name]
            minted = any(self._node_classes(u) for u in node_uris)
            ok = bool(un) and not minted
            if kind == "service":
                ok = ok and any(u.get("to_kind") == "service" for u in un)
            elif kind == "entity":
                ok = ok and any(u.get("to_kind") == "entity" for u in un)
            items.append({"name": name, "kind": kind, "unresolved_reported": bool(un),
                          "references": len(un), "minted": minted, "ok": ok})
            if not ok:
                all_ok = False
        graph_answer = {"targets": items, "unresolved_total": len(self.unresolved)}
        ev = {"file": "unresolved-report", "line": None, "xpath": None, "extraction_type": "unresolved"}
        if all_ok:
            return graph_answer, "CORRECT", "UNRESOLVED", ev, "All expected out-of-scope refs reported, none minted."
        some = sum(1 for i in items if i["ok"])
        if some:
            return graph_answer, "PARTIAL", "UNRESOLVED", ev, "%d/%d unresolved correctly handled." % (some, len(items))
        return graph_answer, "INCORRECT", "UNRESOLVED", ev, "Unresolved handling broken."

    def run_question(self, q):
        check = q.get("check", "")
        fn = getattr(self, "check_" + check, None)
        if fn is None:
            return {"id": q.get("id"), "category": q.get("category"), "question": q.get("question"),
                    "expected": q.get("expected_answer"), "graph_answer": None, "status": "INCORRECT",
                    "fact_type": "DIRECT", "evidence": {}, "note": "Unknown check '%s'." % check}
        try:
            graph_answer, status, fact_type, evidence, note = fn(q)
        except Exception as exc:  # never crash the harness; record as incorrect
            graph_answer, status, fact_type, evidence, note = None, "INCORRECT", "DIRECT", {}, "Evaluator error: %s" % exc
        return {"id": q.get("id"), "category": q.get("category"), "question": q.get("question"),
                "expected": q.get("expected_answer"), "graph_answer": graph_answer, "status": status,
                "fact_type": fact_type, "evidence": evidence, "note": note,
                "source_files": q.get("source_files", []), "source_locations": q.get("source_locations", []),
                "expected_fact_type": q.get("expected_fact_type", "")}


def evaluate_questions(store, facts, manifest, unresolved, questions):
    ev = Evaluator(store, facts, manifest, unresolved)
    results = [ev.run_question(q) for q in questions]
    return results, ev


def compute_metrics(results):
    total = len(results)
    correct = sum(1 for r in results if r["status"] == "CORRECT")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    incorrect = sum(1 for r in results if r["status"] == "INCORRECT")
    unresolved = sum(1 for r in results if r["status"] == "UNRESOLVED")
    answer_coverage = round((correct + partial) / total, 4) if total else None
    denom = correct + partial + incorrect
    correctness = round(correct / denom, 4) if denom else None
    prov_ok = sum(1 for r in results if (r.get("evidence") or {}).get("file"))
    provenance_coverage = round(prov_ok / total, 4) if total else None
    direct = sum(1 for r in results if r.get("fact_type") == "DIRECT")
    inferred = sum(1 for r in results if r.get("fact_type") == "INFERRED")
    unres = sum(1 for r in results if r.get("fact_type") == "UNRESOLVED")
    return {
        "total": total, "correct": correct, "partial": partial,
        "incorrect": incorrect, "unresolved": unresolved,
        "answer_coverage": answer_coverage,
        "resolved_correctness": correctness,
        "provenance_coverage": provenance_coverage,
        "provenance_covered": prov_ok,
        "direct_count": direct, "inferred_count": inferred, "unresolved_count": unres,
        "direct_coverage": round(direct / total, 4) if total else None,
        "inferred_coverage": round(inferred / total, 4) if total else None,
        "unresolved_fact_coverage": round(unres / total, 4) if total else None,
    }


def evaluate_structural(store, facts, unresolved, gold):
    """Sampled existence checks. Returns per-item results + precision/recall."""
    details = []
    # services
    for s in gold.get("services", []):
        uri = NB + "service/" + s["name"]
        rows = store.sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % uri)
        found = any("Service" in (r.get("c", "") or "") for r in rows)
        details.append({"kind": "service", "name": s["name"], "found": found, "expected_file": s.get("file")})
    for e in gold.get("base_entities", []):
        uri = NB + "entity/" + e["name"]
        rows = store.sparql(P + "SELECT ?c WHERE { <%s> a ?c } " % uri)
        classes = [r.get("c", "") for r in rows]
        found = any(c.endswith("/Entity") for c in classes) and not any(c.endswith("/ViewEntity") for c in classes)
        # ViewEntity subclass note: exact triple check — ViewEntity nodes have ViewEntity type.
        details.append({"kind": "base_entity", "name": e["name"], "found": found, "expected_file": e.get("file")})
    for r in gold.get("relations", []):
        subj, tgt = r["subject"], r["target"]
        # relation node: any Relation with relationFrom subject and rel_entity_name target in facts
        rel_facts = [f for f in facts if f["kind"] == "relation" and f["props"].get("subject") == subj and f["props"].get("rel_entity_name") == tgt]
        node_ok = bool(rel_facts)
        if r.get("in_scope"):
            # relationTo edge must exist
            edge_ok = bool(store.sparql(
                P + 'SELECT ?x WHERE { ?rel ofbiz:relationFrom <%s> . ?rel ofbiz:relationTo <%s> }' % (NB + "entity/" + subj, NB + "entity/" + tgt)))
            found = node_ok and edge_ok
        else:
            un = [u for u in unresolved if u.get("edge") == "relationTo" and u.get("to_name") == tgt and subj in u.get("from", "")]
            edge_absent = not store.sparql(
                P + 'SELECT ?x WHERE { ?rel ofbiz:relationFrom <%s> . ?rel ofbiz:relationTo <%s> }' % (NB + "entity/" + subj, NB + "entity/" + tgt))
            found = node_ok and bool(un) and edge_absent
        details.append({"kind": "relation", "name": "%s->%s" % (subj, tgt), "found": found,
                        "node_ok": node_ok, "expected_file": r.get("file")})
    for e in gold.get("ecas", []):
        if e.get("trigger_entity"):
            rows = store.sparql(
                P + 'SELECT ?eca WHERE { ?eca a ofbiz:EntityECA ; ofbiz:triggerEntityName \"%s\" ; ofbiz:ecaEvent \"%s\" }' % (e["trigger_entity"], e["event"]))
            found = bool(rows)
            details.append({"kind": "eca", "name": "ECA:%s:%s" % (e["trigger_entity"], e["event"]), "found": found, "expected_file": e.get("file")})
        else:
            rows = store.sparql(
                P + 'SELECT ?eca WHERE { ?eca a ofbiz:ServiceECA ; ofbiz:triggerServiceName \"%s\" ; ofbiz:ecaEvent \"%s\" }' % (e["trigger_service"], e["event"]))
            found = bool(rows)
            details.append({"kind": "eca", "name": "ECA:%s:%s" % (e["trigger_service"], e["event"]), "found": found, "expected_file": e.get("file")})
    total = len(details)
    tp = sum(1 for d in details if d["found"])
    precision = round(tp / total, 4) if total else None
    recall = round(tp / total, 4) if total else None
    by_kind = {}
    for kind in ("service", "base_entity", "relation", "eca"):
        items = [d for d in details if d["kind"] == kind]
        f = sum(1 for d in items if d["found"])
        by_kind[kind] = {"total": len(items), "found": f,
                         "precision": round(f / len(items), 4) if items else None,
                         "recall": round(f / len(items), 4) if items else None}
    return {"label": "sampled structural gold-set evaluation", "total": total, "found": tp,
            "missing": total - tp, "precision": precision, "recall": recall,
            "by_kind": by_kind, "details": sorted(details, key=lambda d: (d["kind"], d["name"]))}


def normalized_hash(obj) -> str:
    text = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
