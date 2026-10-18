"""Canned SPARQL for enterprise-context questions. All deterministic (ORDER BY)."""
from __future__ import annotations

PREFIX = "PREFIX ofbiz: <http://example.org/ofbiz/0.1/>\n"


def q_services():
    return PREFIX + """SELECT ?service ?name WHERE {
  ?service a ofbiz:Service ; ofbiz:name ?name .
} ORDER BY ?name"""


def q_implementations():
    return PREFIX + """SELECT ?service ?method ?class ?invoke WHERE {
  ?service a ofbiz:Service ; ofbiz:name ?serviceName .
  OPTIONAL {
    ?service ofbiz:implementedBy ?method .
    ?method ofbiz:name ?invoke .
    BIND(STRBEFORE(STRAFTER(STR(?method), "method/"), "#") AS ?class)
  }
} ORDER BY ?service"""


def q_inputs(service_name: str):
    return PREFIX + """SELECT ?param ?type ?mode ?optional WHERE {
  ?service a ofbiz:Service ; ofbiz:name "%s" ; ofbiz:hasInput ?p .
  ?p ofbiz:name ?param .
  OPTIONAL { ?p ofbiz:attrType ?type }
  OPTIONAL { ?p ofbiz:paramMode ?mode }
  OPTIONAL { ?p ofbiz:optional ?optional }
} ORDER BY ?param""" % service_name


def q_outputs(service_name: str):
    return PREFIX + """SELECT ?param ?type ?mode ?optional WHERE {
  ?service a ofbiz:Service ; ofbiz:name "%s" ; ofbiz:hasOutput ?p .
  ?p ofbiz:name ?param .
  OPTIONAL { ?p ofbiz:attrType ?type }
  OPTIONAL { ?p ofbiz:paramMode ?mode }
  OPTIONAL { ?p ofbiz:optional ?optional }
} ORDER BY ?param""" % service_name


def q_entities_referenced():
    return PREFIX + """SELECT DISTINCT ?entity ?via WHERE {
  { ?service ofbiz:operatesOn ?e . BIND(STR(?e) AS ?entity) BIND("operatesOn" AS ?via) }
  UNION
  { ?service ofbiz:defaultEntityName ?entity . BIND("defaultEntityName" AS ?via) }
} ORDER BY ?entity"""


def q_eca_rules():
    return PREFIX + """SELECT ?eca ?class ?event ?operation ?trigger WHERE {
  ?eca a ?class .
  FILTER(?class IN (ofbiz:EntityECA, ofbiz:ServiceECA))
  OPTIONAL { ?eca ofbiz:ecaEvent ?event }
  OPTIONAL { ?eca ofbiz:ecaOperation ?operation }
  OPTIONAL { ?eca ofbiz:triggerEntityName ?trigger }
  OPTIONAL { ?eca ofbiz:triggerServiceName ?trigger }
} ORDER BY ?eca"""


def q_eca_triggered_services():
    return PREFIX + """SELECT DISTINCT ?service ?eca WHERE {
  ?e ofbiz:triggersService ?s .
  ?s ofbiz:name ?service .
  ?e ofbiz:definedIn ?f .
  BIND(STRAFTER(STR(?e), "/eca/") AS ?eca)
} ORDER BY ?service"""


def q_fact_provenance(fact_uri: str):
    return PREFIX + """SELECT ?file ?sha ?artifactType ?extractionType ?line WHERE {
  <%s> ofbiz:definedIn ?a ; ofbiz:extractionType ?extractionType .
  ?a ofbiz:filePath ?file .
  OPTIONAL { ?a ofbiz:sha256 ?sha }
  OPTIONAL { ?a ofbiz:artifactType ?artifactType }
  OPTIONAL { <%s> ofbiz:evidenceLine ?line }
}""" % (fact_uri, fact_uri)


def q_service_files(service_name: str):
    return PREFIX + """SELECT DISTINCT ?file WHERE {
  { ?service a ofbiz:Service ; ofbiz:name "%s" ; ofbiz:definedIn ?a . }
  UNION
  { ?service a ofbiz:Service ; ofbiz:name "%s" ;
      (ofbiz:hasInput|ofbiz:hasOutput) ?p . ?p ofbiz:definedIn ?a . }
  ?a ofbiz:filePath ?file .
} ORDER BY ?file""" % (service_name, service_name)


def q_component_services(component_name: str):
    return PREFIX + """SELECT ?service WHERE {
  ?c a ofbiz:Component ; ofbiz:name "%s" ; ofbiz:containsService ?s .
  ?s ofbiz:name ?service .
} ORDER BY ?service""" % component_name


QUERIES = {
    "services": q_services,
    "implementations": q_implementations,
    "inputs": q_inputs,
    "outputs": q_outputs,
    "entities-referenced": q_entities_referenced,
    "eca-rules": q_eca_rules,
    "eca-triggered-services": q_eca_triggered_services,
    "fact-provenance": q_fact_provenance,
    "service-files": q_service_files,
    "component-services": q_component_services,
}
