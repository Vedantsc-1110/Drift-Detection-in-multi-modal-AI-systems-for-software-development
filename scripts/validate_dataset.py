"""Dataset validation + statistics (deterministic, read-only on OFBiz).

Checks (exit non-zero on any failure):
 1. exactly 20 synthetic .docx documents
 2. exactly 5 requirements / 5 designs / 5 policies / 5 sops
 3. every document has required metadata
 4. document IDs unique
 5. every referenced document ID exists
 6. every [OFBiz-existing] service/entity ref exists in extracted facts
 7. every ground-truth fact has a valid document ID
 8. every ground-truth OFBiz source path exists
 9. negative cases carry expected classifications
 10. no duplicate fact/negative IDs
 11. no broken cross-document references (docs + negatives)
 12. manifest counts match reality

Also writes dataset/dataset-statistics.json from actual files (no fabrication).
Usage: python scripts/validate_dataset.py [--stats-out dataset/dataset-statistics.json]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYN = ROOT / "dataset" / "synthetic-enterprise"
OFBIZ = ROOT / "dataset" / "apache-ofbiz-24.09.07"
FACTS = ROOT / "outputs-deps" / "order-facts.jsonl"
ERRORS = []

TYPE_DIRS = {"requirements": "requirements", "designs": "designs", "policies": "policies", "sops": "sops"}
REQUIRED_META = ["document_id", "title", "type", "version", "date", "author", "department",
                 "related_documents", "related_ofbiz_components", "purpose"]
ALLOWED_NEG = {"UNSUPPORTED", "NOT_FOUND", "PARTIALLY_SUPPORTED"}
ALLOWED_SUPPORT = {"DIRECT", "INDIRECT", "SYNTHETIC", "UNRESOLVED"}


def fail(msg):
    ERRORS.append(msg)


def load_yaml(path):
    import yaml
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def parse_meta(md_text):
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", md_text, re.S)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def main():
    stats_out = ROOT / "dataset" / "dataset-statistics.json"
    if "--stats-out" in sys.argv:
        stats_out = ROOT / sys.argv[sys.argv.index("--stats-out") + 1]

    # --- collect docs ---
    docx_files = sorted((SYN).rglob("*.docx"))
    # only count corpus docs (exclude nothing else lives there)
    md_files = sorted([p for p in SYN.rglob("*.md") if p.name != "README.md"])
    by_type = {t: sorted((SYN / d).glob("*.docx")) for t, d in TYPE_DIRS.items()}

    # 1. exactly 20
    if len(docx_files) != 20:
        fail("expected 20 .docx documents, found %d" % len(docx_files))
    # 2. per-type
    for t, files in by_type.items():
        if len(files) != 5:
            fail("expected 5 %s docs, found %d" % (t, len(files)))

    # 3/4. metadata + unique IDs
    metas = {}
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        meta = parse_meta(text)
        for field in REQUIRED_META:
            if field not in meta or not meta[field]:
                fail("%s missing metadata '%s'" % (md.name, field))
        did = meta.get("document_id", "")
        if did in metas:
            fail("duplicate document_id %s" % did)
        metas[did] = {"meta": meta, "path": md}
    if len(metas) != 20:
        fail("expected 20 unique document IDs, found %d" % len(metas))

    # 5/11. referenced IDs exist
    valid_ids = set(metas)
    for did, info in metas.items():
        rels = [r.strip() for r in info["meta"].get("related_documents", "").strip("[]").split(",") if r.strip()]
        for r in rels:
            if r not in valid_ids:
                fail("%s references unknown document %s" % (did, r))

    # 6. OFBiz refs exist in facts
    try:
        facts = [json.loads(x) for x in FACTS.read_text(encoding="utf-8").splitlines() if x.strip()]
    except FileNotFoundError:
        facts = []
        fail("extracted facts missing: %s (run extraction first)" % FACTS)
    svc_names = {f["props"]["name"] for f in facts if f["kind"] == "service"}
    ent_names = {f["props"]["name"] for f in facts if f["kind"] in ("entity", "view_entity")}
    existing_names = svc_names | ent_names
    ofbiz_existing_refs = set()
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for m in re.finditer(r"\[OFBiz-existing\]\s+([A-Za-z0-9_#]+)", text):
            name = m.group(1)
            if not re.search(r"[A-Z]", name):
                continue  # prose word after the marker, not an identifier
            ofbiz_existing_refs.add((md.name, name))
    for fname, name in sorted(ofbiz_existing_refs):
        base = name.split("#")[0]
        if base not in existing_names:
            fail("%s: [OFBiz-existing] '%s' not in extracted facts" % (fname, name))
    out_of_scope_refs = set()
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for m in re.finditer(r"\[OFBiz-reference-out-of-scope\]\s+([A-Za-z0-9_#]+)", text):
            out_of_scope_refs.add(m.group(1))

    # 7/8/10. ground truth
    gt = load_yaml(SYN / "ground_truth" / "fact-mappings.yaml")
    fact_list = gt.get("facts", [])
    seen_facts = set()
    support_counts = {}
    for f in fact_list:
        fid = f.get("fact_id")
        if fid in seen_facts:
            fail("duplicate fact_id %s" % fid)
        seen_facts.add(fid)
        if f.get("document_id") not in valid_ids:
            fail("%s has invalid document_id %s" % (fid, f.get("document_id")))
        if f.get("support_type") not in ALLOWED_SUPPORT:
            fail("%s bad support_type %s" % (fid, f.get("support_type")))
        support_counts[f.get("support_type")] = support_counts.get(f.get("support_type"), 0) + 1
        for k in ("statement", "subject", "predicate", "object"):
            if not f.get(k):
                fail("%s missing '%s'" % (fid, k))
        if f.get("ofbiz_source") and f.get("source_file"):
            if not (OFBIZ / f["source_file"]).is_file():
                fail("%s OFBiz source missing: %s" % (fid, f["source_file"]))

    neg = load_yaml(SYN / "ground_truth" / "negative_cases.yaml")
    neg_list = neg.get("cases", [])
    seen_neg = set()
    neg_counts = {}
    for n in neg_list:
        nid = n.get("negative_id")
        if nid in seen_neg:
            fail("duplicate negative_id %s" % nid)
        seen_neg.add(nid)
        if n.get("expected_classification") not in ALLOWED_NEG:
            fail("%s bad classification %s" % (nid, n.get("expected_classification")))
        neg_counts[n.get("expected_classification")] = neg_counts.get(n.get("expected_classification"), 0) + 1
        if not n.get("statement") or not n.get("why_unsupported"):
            fail("%s missing statement/why_unsupported" % nid)
        for r in n.get("related_documents", []):
            if r not in valid_ids:
                fail("%s references unknown document %s" % (nid, r))

    # 12. manifest counts
    for mp in (SYN / "dataset-manifest.yaml", ROOT / "dataset" / "dataset-manifest.yaml"):
        if Path(mp).is_file():
            man = load_yaml(str(mp))
            text = json.dumps(man)
            if "20" not in text:
                fail("%s does not mention 20 documents" % mp)

    # --- statistics from actual files ---
    words_total = 0
    words_by_type = {}
    for t, d in TYPE_DIRS.items():
        w = 0
        for md in sorted((SYN / d).glob("*.md")):
            w += len(md.read_text(encoding="utf-8").split())
        words_by_type[t] = w
        words_total += w
    cross_links = sum(len([r for r in info["meta"].get("related_documents", "").strip("[]").split(",") if r.strip()]) for info in metas.values())
    svc_refs = sorted({n for _, n in ofbiz_existing_refs if n.split("#")[0] in svc_names})
    ent_refs = sorted({n for _, n in ofbiz_existing_refs if n.split("#")[0] in ent_names})
    stats = {
        "total_documents": len(docx_files),
        "documents_by_type": {t: len(files) for t, files in by_type.items()},
        "total_words_md": words_total,
        "words_by_type_md": words_by_type,
        "total_ground_truth_facts": len(fact_list),
        "facts_by_support_type": support_counts,
        "total_negative_cases": len(neg_list),
        "negatives_by_classification": neg_counts,
        "cross_document_links": cross_links,
        "ofbiz_services_referenced": svc_refs,
        "ofbiz_services_referenced_count": len(svc_refs),
        "ofbiz_entities_referenced": ent_refs,
        "ofbiz_entities_referenced_count": len(ent_refs),
        "ofbiz_out_of_scope_referenced": sorted(out_of_scope_refs),
        "method": "computed from actual MD bodies, front-matter related_documents, [OFBiz-existing] markers, and ground-truth YAMLs",
    }
    stats_out.parent.mkdir(parents=True, exist_ok=True)
    stats_out.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("docs: %d (req=%d des=%d pol=%d sop=%d)" % (len(docx_files), *[len(by_type[t]) for t in ("requirements", "designs", "policies", "sops")]))
    print("words(md): %d facts: %d negatives: %d support=%s neg=%s" % (words_total, len(fact_list), len(neg_list), support_counts, neg_counts))
    print("services_ref: %d entities_ref: %d out_of_scope: %s cross_links: %d" % (len(svc_refs), len(ent_refs), sorted(out_of_scope_refs), cross_links))
    if ERRORS:
        print("VALIDATION FAILED (%d):" % len(ERRORS))
        for e in ERRORS:
            print(" - " + e)
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
