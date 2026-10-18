"""Report statements must follow the run's data rather than a fixed scope."""

from contextgraph.report import build_report, to_markdown
from contextgraph.store import ContextStore


def test_dependency_scope_report_does_not_claim_discovered_entities_are_absent(tmp_path):
    ttl = tmp_path / "source.ttl"
    ttl.write_text(
        '@prefix ofbiz: <http://example.org/ofbiz/0.1/> .\n'
        'ofbiz:OrderHeader a ofbiz:Entity ; ofbiz:name "OrderHeader" .\n',
        encoding="utf-8",
    )
    store = ContextStore(tmp_path / "store")
    store.load_turtle(ttl)
    report = build_report(store, {"component": "order"}, [], [])
    assert report["base_entities_discovered"] == 1
    assert "outside this run's scope" not in report["entity_note"]
    markdown = to_markdown(report)
    assert "foreign keys) live outside this run's scope" not in markdown
    assert "1 base entities" in report["entity_note"]
