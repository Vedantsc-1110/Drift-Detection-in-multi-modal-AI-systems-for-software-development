"""Opt-in browser regressions: RUN_BROWSER_TESTS=1 python -m pytest this_file.

Requires Playwright and Edge (PLAYWRIGHT_CHANNEL can select another browser).
All page requests are served by the actual FastAPI TestClient, without a port,
remote server, or network connection. Screenshots go to .tools/ui/.
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / ".tools/browser"))
pytestmark = pytest.mark.skipif(os.environ.get("RUN_BROWSER_TESTS") != "1", reason="Opt in with RUN_BROWSER_TESTS=1; requires Playwright and a browser")


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        instance = playwright.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL", "msedge"), headless=True)
        yield instance
        instance.close()


@pytest.fixture
def page(browser, tmp_path):
    from fastapi.testclient import TestClient
    from contextgraph.contract_api import create_app
    from contextgraph.contract_store import ContractStore

    store = ContractStore(tmp_path / "store")
    directory = PROJECT / "tests/fixtures/contract/api"
    for filename, graph in (("structural.ttl", "urn:ofbiz_structural"), ("airflow.ttl", "urn:airflow"), ("semantic.ttl", "urn:ofbiz_semantic"), ("cuad.ttl", "urn:cuad"), ("bridges.ttl", "urn:bridges")):
        store.load_file(directory / filename, graph)
    with TestClient(create_app(store, data_info={"mode": "demo", "source": "API fixtures"})) as client:
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        tab = context.new_page()

        def serve(route):
            uri = urlsplit(route.request.url)
            response = client.get(uri.path + ("?" + uri.query if uri.query else ""))
            route.fulfill(status=response.status_code, content_type=response.headers.get("content-type", "text/plain"), body=response.content)

        context.route("http://context.test/**", serve)
        yield tab
        context.close()
    store.close()


def ready(page, query=""):
    page.goto("http://context.test/dashboard" + query)
    page.wait_for_function("document.querySelector('#graph').getAttribute('aria-busy') === 'false'")


def wait_loaded(page):
    page.wait_for_function("document.querySelector('#graph').getAttribute('aria-busy') === 'false'")


def test_canvas_node_click_zoom_drag_and_evidence(page):
    ready(page)
    canvas = page.locator("#graph canvas")
    canvas.scroll_into_view_if_needed()
    assert canvas.is_visible()
    assert canvas.bounding_box()["width"] > 500
    assert page.locator("#connection").inner_text() == "Demo fixtures · Local store"
    uri = "http://context.example.org/findOrders"
    point = page.evaluate("uri => network.canvasToDOM(network.getPositions([uri])[uri])", uri)
    bounds = canvas.bounding_box()
    page.mouse.click(bounds["x"] + point["x"], bounds["y"] + point["y"])
    page.wait_for_function("document.querySelector('#provenance').textContent.includes('Line 142')")
    assert "services.xml" in page.locator("#provenance").inner_text()
    scale = page.evaluate("network.getScale()")
    page.locator("#zoomIn").click()
    assert page.evaluate("network.getScale()") > scale
    page.locator("#fit").click()
    before = page.evaluate("uri => network.getPositions([uri])[uri]", uri)
    point = page.evaluate("uri => network.canvasToDOM(network.getPositions([uri])[uri])", uri)
    bounds = canvas.bounding_box()
    page.mouse.move(bounds["x"] + point["x"], bounds["y"] + point["y"])
    page.mouse.down()
    page.mouse.move(bounds["x"] + point["x"] + 45, bounds["y"] + point["y"] + 30, steps=8)
    page.mouse.up()
    assert page.evaluate("uri => network.getPositions([uri])[uri]", uri) != before
    page.locator("#physics").click()
    assert page.locator("#physics").get_attribute("aria-pressed") == "true"
    page.locator("#physics").click()
    assert page.locator("#physics").get_attribute("aria-pressed") == "false"


def test_filter_empty_reset_history_and_repeated_reload(page):
    ready(page)
    initial = page.locator("#nodeCount").inner_text()
    page.locator("#search").fill("no-such-service-xyz")
    page.locator("#reload").click()
    wait_loaded(page)
    assert page.locator("#nodeCount").inner_text() == "0"
    assert page.locator("#messageTitle").inner_text() == "No nodes match these filters."
    assert "search=no-such-service-xyz" in page.url
    page.locator("#reset").click()
    wait_loaded(page)
    assert page.locator("#nodeCount").inner_text() == initial
    page.go_back()
    wait_loaded(page)
    assert page.locator("#nodeCount").inner_text() == "0"
    page.locator("#reset").click()
    wait_loaded(page)
    for _ in range(3):
        page.locator("#reload").click()
        wait_loaded(page)
        assert page.locator("#graph canvas").count() == 1
    page.select_option("#factType", "probabilistic")
    wait_loaded(page)
    assert page.locator("#nodeCount").inner_text() == page.locator("#inferredCount").inner_text()


def test_node_directory_and_relationship_inspection(page):
    ready(page)
    page.locator("#directorySummary").click()
    entry = page.locator("#nodelist button").filter(has_text="findOrders").first
    entry.focus()
    page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('#provenance').textContent.includes('Visible connections')")
    page.locator("#provenance .node-link").first.click()
    assert page.locator("#provenance h3").inner_text() == "Relationship"
    assert "per-arrow" in page.locator("#provenance").inner_text()


def test_renderer_unavailable_retains_accessible_directory(page):
    page.route("**/vendor/vis-network.min.js", lambda route: route.abort())
    ready(page)
    assert "renderer" in page.locator("#messageTitle").inner_text()
    assert page.locator("#fallback").get_attribute("open") is not None
    assert page.locator("#nodelist button").count() > 5
    page.locator("#nodelist button").first.click()
    page.wait_for_function("document.querySelector('#provenance').textContent.toLowerCase().includes('confidence')")


def test_api_error_retry_and_refresh_retains_previous_data(page):
    page.route("**/graph/nodes?*", lambda route: route.fulfill(status=503, body="Unavailable"))
    ready(page)
    assert page.locator("#retry").is_visible()
    assert "Could not load" in page.locator("#status").inner_text()
    page.unroute("**/graph/nodes?*")
    page.locator("#retry").click()
    wait_loaded(page)
    initial = page.locator("#nodeCount").inner_text()
    page.route("**/graph/nodes?*", lambda route: route.fulfill(status=503, body="Unavailable"))
    page.locator("#reload").click()
    wait_loaded(page)
    assert page.locator("#nodeCount").inner_text() == initial
    assert page.locator("#graph canvas").is_visible()
    assert "previous graph" in page.locator("#status").inner_text()
    assert page.locator("#reload").is_enabled()


def test_desktop_and_mobile_layout_and_screenshots(page):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    ready(page)
    directory = PROJECT / ".tools/ui"
    directory.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(directory / "desktop.png"), full_page=True)
    page.locator("#explorer").screenshot(path=str(directory / "graph.png"))
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(250)  # Allow the debounced graph resize to finish.
    page.screenshot(path=str(directory / "mobile.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.locator("#graph canvas").bounding_box()["width"] > 300
    assert not errors


def test_graph_is_a_useful_work_surface_without_scrolling(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    ready(page)

    bounds = page.locator("#graph canvas").bounding_box()
    assert bounds is not None
    assert bounds["width"] > 500
    assert bounds["height"] >= 300
    assert 0 <= bounds["y"] < 350, "The explorer must be visible on arrival"
    assert bounds["y"] + bounds["height"] <= 900, "The graph should fit the desktop viewport"
    assert page.locator("#viewGraph").is_visible()
    assert page.locator("#viewList").is_visible()
    effective_font = page.evaluate("""() => {
      const node = network.body.nodes['http://context.example.org/findOrders'];
      return node.options.font.size * network.getScale();
    }""")
    assert effective_font >= 10, "The initial graph must show readable labels, not tiny unlabeled dots"


@pytest.mark.parametrize("width,height", [(1440, 900), (1024, 768), (390, 844)])
def test_workspace_fits_supported_viewports_without_horizontal_page_scroll(page, width, height):
    page.set_viewport_size({"width": width, "height": height})
    ready(page)

    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.locator("#graph canvas").bounding_box()["width"] > 300
    for control in ("#search", "#viewGraph", "#viewList", "#exportGraph"):
        assert page.locator(control).is_visible(), f"{control} must remain reachable at {width}px"


def test_node_view_and_keyboard_selection_keep_evidence_available(page):
    ready(page)
    count = int(page.locator("#nodeCount").inner_text())

    page.locator("#viewList").click()
    assert page.locator("#workspace").get_attribute("data-view") == "list"
    assert page.locator("#nodelist button").count() == count
    entry = page.locator("#nodelist button").filter(has_text="findOrders").first
    assert entry.is_visible()
    entry.focus()
    page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('#provenance').textContent.includes('Line 142')")
    assert page.locator("#selectionBadge").inner_text() != "No selection"
    assert "findOrders" in page.locator("#provenance h3").inner_text()

    page.locator("#viewGraph").click()
    assert page.locator("#workspace").get_attribute("data-view") == "graph"
    assert page.locator("#graph canvas").is_visible()
    assert "findOrders" in page.locator("#provenance").inner_text()


def test_search_shortcut_focuses_search_without_stealing_typing(page):
    ready(page)
    page.locator("#viewGraph").focus()
    page.keyboard.press("/")
    assert page.locator("#search").evaluate("input => document.activeElement === input")
    page.locator("#search").fill("find")
    page.keyboard.press("/")
    assert page.locator("#search").input_value() == "find/"


def test_visible_interactive_controls_have_accessible_names(page):
    ready(page)
    missing = page.evaluate("""() => {
      const visible = item => item.getClientRects().length && getComputedStyle(item).visibility !== 'hidden';
      const labelled = item => {
        const references = (item.getAttribute('aria-labelledby') || '').split(/\\s+/).filter(Boolean);
        return references.some(id => document.getElementById(id)?.textContent.trim())
          || (item.getAttribute('aria-label') || '').trim()
          || (item.getAttribute('title') || '').trim()
          || [...(item.labels || [])].some(label => label.textContent.trim())
          || (item.matches('button, a') && item.textContent.trim());
      };
      return [...document.querySelectorAll('button, a[href], input:not([type="hidden"]), select')]
        .filter(item => visible(item) && !labelled(item))
        .map(item => item.id || item.outerHTML.slice(0, 120));
    }""")
    assert not missing, f"Controls without an accessible name: {missing}"


def test_source_navigator_counts_triples_and_filters_the_actual_graph(page):
    with page.expect_response(lambda response: urlsplit(response.url).path == "/graph/summary") as metadata:
        ready(page)
    graphs = metadata.value.json()["graphs"]
    assert int(page.locator("#sourceCount").inner_text()) == len(graphs)
    assert page.locator("#sourceList button").count() == len(graphs) + 1
    for graph in graphs:
        source = page.locator(f"#sourceList button[data-graph-id='{graph['id']}']")
        assert int(source.locator(".source-total").inner_text().replace(",", "")) == graph["triples"]
        assert f"{graph['triples']} stored triples" in source.get_attribute("aria-label")

    initial = int(page.locator("#nodeCount").inner_text())
    with page.expect_response(lambda response: urlsplit(response.url).path == "/graph/nodes") as filtered:
        page.locator("#sourceList button[data-graph-id='urn:airflow']").click()
    wait_loaded(page)
    payload = filtered.value.json()
    assert page.locator("#graphFilter").input_value() == "urn:airflow"
    assert page.locator("#sourceList button[data-graph-id='urn:airflow']").get_attribute("aria-pressed") == "true"
    assert int(page.locator("#nodeCount").inner_text()) == len(payload["nodes"])
    assert 0 < len(payload["nodes"]) < initial
    assert page.evaluate("network.body.data.nodes.getIds().sort()") == sorted(node["id"] for node in payload["nodes"])
    assert all(edge["graph"] == "urn:airflow" for edge in payload["edges"])

    page.locator("#sourceList button[data-graph-id='']").click()
    wait_loaded(page)
    assert int(page.locator("#nodeCount").inner_text()) == initial
    assert page.locator("#graphFilter").input_value() == ""


def test_export_contains_visible_data_and_applied_filters_after_failed_refresh(page, tmp_path):
    ready(page)
    with page.expect_response(lambda response: urlsplit(response.url).path == "/graph/nodes") as filtered:
        page.select_option("#graphFilter", "urn:airflow")
    wait_loaded(page)
    payload = filtered.value.json()

    # An unapplied edit must not be presented as the filter behind exported data.
    page.route("**/graph/nodes?*", lambda route: route.fulfill(status=503, body="Unavailable"))
    page.locator("#search").fill("an edit that could not load")
    page.locator("#reload").click()
    wait_loaded(page)
    with page.expect_download() as download:
        page.locator("#exportGraph").click()
    target = tmp_path / "visible-graph.json"
    download.value.save_as(target)
    output = json.loads(target.read_text(encoding="utf-8"))

    assert download.value.suggested_filename.endswith(".json")
    assert output["nodes"] == payload["nodes"]
    assert output["edges"] == payload["edges"]
    assert output["filters"] == {"confidence": "all", "factType": "both", "graph": "urn:airflow", "search": ""}
    assert output["exportedAt"]
    assert "Exported" in page.locator("#status").inner_text()


def test_focus_and_clear_selection_recover_the_graph_and_inspector(page):
    ready(page)
    page.wait_for_function("document.querySelector('#provenance').textContent.includes('Line 142')")
    page.locator("#viewList").click()
    page.locator("#nodelist button[data-node-id='http://context.example.org/findOrders']").click()
    assert page.locator("#focusSelection").is_enabled()
    page.evaluate("network.moveTo({position: {x: 5000, y: 5000}, animation: false})")
    page.locator("#focusSelection").click()
    page.wait_for_function("""() => {
      if (document.querySelector('#workspace').dataset.view !== 'graph') return false;
      const uri = 'http://context.example.org/findOrders';
      const point = network.canvasToDOM(network.getPositions([uri])[uri]);
      const bounds = document.querySelector('#graph canvas').getBoundingClientRect();
      return point.x >= 0 && point.x <= bounds.width && point.y >= 0 && point.y <= bounds.height;
    }""")
    assert page.evaluate("network.getSelectedNodes()") == ["http://context.example.org/findOrders"]

    page.locator("#clearSelection").click()
    assert page.evaluate("network.getSelectedNodes()") == []
    assert page.locator("#selectionBadge").inner_text() == "No selection"
    assert page.locator("#focusSelection").is_disabled()
    assert page.locator("#clearSelection").is_disabled()
    assert page.locator("#provenance .inspector-empty").is_visible()


def test_mobile_refinement_keeps_source_filtering_reachable(page):
    page.set_viewport_size({"width": 390, "height": 844})
    ready(page)
    initial = int(page.locator("#nodeCount").inner_text())
    refinement = page.locator("#advancedFilters > summary")
    assert refinement.is_visible()
    assert refinement.bounding_box()["height"] >= 44
    refinement.click()
    assert page.locator("#graphFilter").is_visible()

    page.select_option("#graphFilter", "urn:airflow")
    wait_loaded(page)
    assert 0 < int(page.locator("#nodeCount").inner_text()) < initial
    page.locator("#reset").click()
    wait_loaded(page)
    assert int(page.locator("#nodeCount").inner_text()) == initial
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_mobile_selection_reveals_evidence_and_focus_returns_to_graph(page):
    page.set_viewport_size({"width": 390, "height": 844})
    ready(page)
    page.wait_for_function("document.querySelector('#provenance').textContent.includes('Line 142')")
    page.locator("#graph canvas").scroll_into_view_if_needed()
    uri = "http://context.example.org/findOrders"
    point = page.evaluate("uri => network.canvasToDOM(network.getPositions([uri])[uri])", uri)
    bounds = page.locator("#graph canvas").bounding_box()
    page.mouse.click(bounds["x"] + point["x"], bounds["y"] + point["y"])
    page.wait_for_function("document.querySelector('.inspector').getBoundingClientRect().top < 120")
    assert "findOrders" in page.locator("#provenance").inner_text()

    page.locator("#focusSelection").click()
    page.wait_for_function("document.querySelector('#graph').getBoundingClientRect().top >= 0 && document.querySelector('#graph').getBoundingClientRect().top < 120")
    assert page.locator("#graph canvas").is_visible()
