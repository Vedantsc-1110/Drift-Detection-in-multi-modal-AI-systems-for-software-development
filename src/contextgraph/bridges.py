"""Bridge edge creation across artifact graphs (PART3 Task 3.4, §7.2 3.4).

The §3.4 table, implemented as deterministic label-matching rules over the
union of contract graphs (matching is case-insensitive substring on
rdfs:label, minimum length guards against noise):
  Task --invokesService--> Service (task label names the service)
  Policy --constrains--> Service (policy label names the service)
  Contract --mentionsEntity--> Entity (contract/clause labels name it)
  Filing --referencesModule--> Module (filing literals name the module)
  Document --relatedTo--> Document (shared word, length >= 6)

Vocabulary note: ctx:relatedTo appears in the §3.4 table but NOT in the §3
property list — implemented as specified, flagged for contract review.
Each bridge carries a provenance record (prov:Entity) in the bridges graph:
deterministic derivation (confidence 1.0) by ctx:BridgesExtractor.
"""

from __future__ import annotations

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS

CTX = Namespace("http://context.example.org/")
BRIDGES_GRAPH = "urn:bridges"
EXTRACTOR = CTX.BridgesExtractor

MIN_NAME_LEN = 4
MIN_WORD_LEN = 6
STOPWORDS = {"and", "the", "for", "with", "from", "that", "this"}

BRIDGE_PREDICATES = {
    "invokesService": CTX.invokesService,
    "constrains": CTX.constrains,
    "mentionsEntity": CTX.mentionsEntity,
    "referencesModule": CTX.referencesModule,
    "relatedTo": CTX.relatedTo,  # §3.4 table only; absent from §3 list
}


def _labels(graph: Graph, rdf_class: URIRef) -> dict:
    """Subject -> label for individuals of a class (sorted, deterministic)."""
    out = {}
    for subj in sorted(graph.subjects(RDF.type, rdf_class), key=str):
        label = next(graph.objects(subj, RDFS.label), None)
        if label:
            out[subj] = str(label)
    return out


def discover_bridges(graph: Graph) -> list:
    """Return bridge specs [{s, p, o, via}] in deterministic order."""
    services = _labels(graph, CTX.Service)
    tasks = _labels(graph, CTX.Task)
    policies = _labels(graph, CTX.Policy)
    entities = _labels(graph, CTX.Entity)
    contracts = _labels(graph, CTX.Contract)
    clauses = _labels(graph, CTX.Clause)
    filings = _labels(graph, CTX.Filing)
    modules = _labels(graph, CTX.Module)
    documents = _labels(graph, CTX.Document)
    bridges = []

    for task, task_label in tasks.items():
        lowered = task_label.lower()
        for service, service_label in services.items():
            if len(service_label) >= MIN_NAME_LEN and service_label.lower() in lowered:
                bridges.append({"s": task, "p": "invokesService", "o": service,
                                "via": "task-label-names-service"})
    for policy, policy_label in policies.items():
        lowered = policy_label.lower()
        for service, service_label in services.items():
            if len(service_label) >= MIN_NAME_LEN and service_label.lower() in lowered:
                bridges.append({"s": policy, "p": "constrains", "o": service,
                                "via": "policy-label-names-service"})
    for contract, contract_label in contracts.items():
        haystack = contract_label + " " + " ".join(
            label for subj, label in clauses.items()
            if (contract, CTX.hasClause, subj) in graph)
        lowered = haystack.lower()
        for entity, entity_label in entities.items():
            if len(entity_label) >= MIN_NAME_LEN and entity_label.lower() in lowered:
                bridges.append({"s": contract, "p": "mentionsEntity", "o": entity,
                                "via": "contract-text-names-entity"})
    filing_text_by_filing: dict = {}
    sections_by_filing: dict = {}
    unclaimed_sections = []
    for section, heading in _labels(graph, CTX.Section).items():
        claimed = None
        for filing in filings:
            tag = str(filing).rsplit("/", 1)[-1]
            if str(section).startswith("http://context.example.org/Section/" + tag + "/"):
                claimed = filing
                break
        if claimed is None:
            unclaimed_sections.append(heading)
        else:
            sections_by_filing.setdefault(claimed, []).append(heading)
    for filing, filing_label in filings.items():
        own = [filing_label] + sections_by_filing.get(filing, []) + unclaimed_sections
        filing_text_by_filing[filing] = " ".join(own).lower()
    for filing in sorted(filings, key=str):
        filing_text = filing_text_by_filing[filing]
        for module, module_label in modules.items():
            if len(module_label) >= MIN_NAME_LEN and module_label.lower() in filing_text:
                bridges.append({"s": filing, "p": "referencesModule", "o": module,
                                "via": "filing-text-names-module"})
    docs = sorted(documents.items(), key=lambda kv: str(kv[0]))
    for i, (doc_a, label_a) in enumerate(docs):
        words_a = {w.strip(".,;:!?()\"'").lower() for w in label_a.split()}
        for doc_b, label_b in docs[i + 1:]:
            words_b = {w.strip(".,;:!?()\"'").lower() for w in label_b.split()}
            shared = sorted((words_a & words_b) - STOPWORDS)
            if any(len(w) >= MIN_WORD_LEN for w in shared):
                bridges.append({"s": doc_a, "p": "relatedTo", "o": doc_b,
                                "via": "shared-label-word:%s" % shared[0]})
    bridges.sort(key=lambda b: (b["p"], str(b["s"]), str(b["o"])))
    return bridges


def bridges_graph(bridges: list, source_graph: str = "urn:union") -> Graph:
    """Bridge edges + one provenance record per bridge (prov:Entity)."""
    graph = Graph()
    graph.bind("ctx", CTX)
    for i, bridge in enumerate(bridges):
        subj, pred, obj = bridge["s"], BRIDGE_PREDICATES[bridge["p"]], bridge["o"]
        graph.add((subj, pred, obj))
        record = URIRef(str(CTX) + "Bridge/%d" % i)
        graph.add((record, RDF.type, PROV.Entity))
        graph.add((record, RDFS.label, Literal("%s %s %s (%s)" % (subj, pred, obj, bridge["via"]))))
        graph.add((record, PROV.wasGeneratedBy, EXTRACTOR))
        graph.add((record, PROV.hadPrimarySource, URIRef(source_graph)))
        graph.add((record, CTX.confidence, Literal(1.0)))
        graph.add((record, CTX.factType, Literal("deterministic")))
    return graph


def insert_bridges(store, bridges: list, source_graph: str = "urn:union") -> int:
    """Load bridge edges + records into the store's urn:bridges graph."""
    from pyoxigraph import NamedNode, Quad

    from .contract_store import _node

    target = NamedNode(BRIDGES_GRAPH)
    count = 0
    for subj, pred, obj in bridges_graph(bridges, source_graph):
        store._store.add(Quad(_node(subj), _node(pred), _node(obj), target))
        count += 1
    store._store.flush()
    return count
