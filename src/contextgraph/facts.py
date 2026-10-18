"""Fact model: plain dicts with fixed schema, JSON-serializable, deterministically ordered."""
from __future__ import annotations

from . import EXTRACTOR_NAME, EXTRACTOR_VERSION, NAMESPACE


def uri(*parts: str) -> str:
    return NAMESPACE + "/".join(parts)


def make_fact(kind, fid, props=None, prov=None):
    """Create a fact dict. prov keys: repository, file, line, xpath, method,
    extraction_type, evidence (list of {file, line, xpath, snippet})."""
    return {
        "id": fid,
        "kind": kind,
        "props": props or {},
        "prov": prov or {},
    }


def base_prov(ctx, element=None, method="", extraction_type="direct"):
    """Provenance envelope for a fact stated by one XML element."""
    prov = {
        "repository": ctx.repo_id,
        "file": ctx.artifact.relpath,
        "line": None,
        "xpath": None,
        "extractor": EXTRACTOR_NAME,
        "extractor_version": EXTRACTOR_VERSION,
        "method": method,
        "extraction_type": extraction_type,
        "evidence": [],
    }
    if element is not None:
        prov["line"] = element.sourceline
        try:
            prov["xpath"] = ctx.tree.getpath(element)
        except Exception:
            prov["xpath"] = None
    return prov


def add_evidence(prov, ctx, element, snippet=""):
    prov["evidence"].append(
        {
            "file": ctx.artifact.relpath,
            "line": element.sourceline,
            "xpath": ctx.tree.getpath(element),
            "snippet": snippet,
        }
    )
    return prov


def snippet_of(element, limit=300):
    """Short verbatim rendering of an element for evidence (start tag only)."""
    from lxml import etree

    text = etree.tostring(element, encoding="unicode", with_tail=False)
    # Keep only the start tag for bounded, stable evidence.
    head = text.split(">", 1)[0] + ">"
    return head[:limit]
